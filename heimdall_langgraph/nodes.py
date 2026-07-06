"""
nodes.py — LangGraph investigation + dispatch nodes.

The simulator is now a background thread (simulator.py).
These nodes only handle: investigate anomaly → dispatch alert.

Node flow inside the graph:
  investigate → dispatch → [loop back to investigate if queue non-empty]
"""

import json
import os
from typing import List, Literal

from services.alert_service import route_alert

from context_generator import enrich_context
from pattern_cache import (
    get_cached_result,
    store_result
)

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

import database
from state import SecurityState

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not _api_key:
    raise EnvironmentError(
        "❌ GEMINI_API_KEY not found. Put it in your .env at the project root."
    )

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,
    api_key=_api_key,
)


# ── structured output ─────────────────────────────────────────────────────────
class SecurityAlert(BaseModel):
    severity: Literal["No Alert", "Low", "Medium", "High"] = Field(
        description="Threat classification based on context and history."
    )
    summary: str = Field(
        description=(
            "3-5 sentence narrative: what happened, correlated history found, "
            "why this severity was chosen, and any pattern recognised from memory."
        )
    )
    target_interface: List[Literal["resident", "security", "admin"]] = Field(
        description=(
            "Who must be notified, derived strictly from severity — do not improvise other combinations:\n"
            "No Alert → [] (empty list, nobody is notified)\n"
            "Low      → [\"resident\"]\n"
            "Medium   → [\"resident\", \"security\"]\n"
            "High     → [\"security\", \"resident\", \"admin\"]"
        )
    )
    recommended_action: str = Field(
        description="One concrete instruction for the receiving party."
    )
    trust_score_action: str = Field(
        description=(
            "Brief justification for the trust score penalty being applied "
            "to the responsible resident (if any). E.g. 'First offence, minor deduction.' "
            "If severity is 'No Alert', state plainly that no penalty applies."
        )
    )


_structured_llm = _llm.with_structured_output(SecurityAlert)

_SYSTEM_PROMPT = """You are Heimdall AI — a Tier-2 Physical Security Investigator.

Analyse the incoming anomaly context packet and produce a structured alert.

Every incident carries a free-text "context" field describing the situation observed around the anomaly (e.g. who accompanied the resident, timing relative to other events, whether a maintenance window was in effect). Treat this context as the primary source of truth.

Your objective is to minimize false alarms while ensuring genuine threats are escalated appropriately.

════════════════════
INVESTIGATION PRINCIPLE
════════════════════

Do NOT assume malicious intent simply because an anomaly occurred.

Most security anomalies are caused by ordinary human behaviour, authorized personnel, environmental conditions, or minor procedural mistakes.

Escalate severity only when objective evidence supports it.

If there is insufficient evidence to conclude malicious intent, prefer Medium over High.

If there is clear benign evidence, prefer Low.

════════════════════
SEVERITY RULES
════════════════════

── No Alert ──

Choose No Alert ONLY if there is explicit evidence that:

• A scheduled maintenance window was active.
OR
• The anomaly was caused by a confirmed sensor malfunction or self-correcting hardware glitch.

These are the ONLY No Alert cases.

────────────────────

── High ──

Choose High ONLY when there is strong evidence of an actual security threat.

Examples include:

• Forced door entry with no legitimate explanation.
• Multiple coordinated anomalies strongly indicating an attack.
• Trust score below 0.50 combined with suspicious behaviour.
• Multiple repeat incidents occurring in the investigation window.
• Clear malicious intent.
• Active intrusion or attempted unauthorized access.

Do NOT choose High simply because information is missing.

High should be uncommon and reserved for incidents requiring immediate escalation.

────────────────────

── Medium (Default Investigation Tier) ──

Choose Medium whenever an incident requires human verification.

This includes:

• Unknown intent.
• Ambiguous context.
• Tailgating where legitimacy cannot be confirmed.
• Unknown visitor.
• Door forced open after successful authentication.
• One repeat incident.
• One correlated anomaly.
• Incomplete evidence.
• Suspicious behaviour that is not clearly malicious.

Whenever a guard needs to verify the situation before deciding whether it is dangerous, choose Medium.

Medium is the preferred classification for uncertain incidents.

────────────────────

── Low ──

Choose Low whenever the anomaly appears benign and there is no meaningful evidence of malicious behaviour.

Examples include:

• Known resident with no history.
• Clearly identified family member.
• Child.
• Spouse.
• Roommate.
• Known delivery personnel.
• Authorized maintenance worker.
• Resident voluntarily allowing another known person through.
• First-time procedural mistake.
• Accidental tailgating.
• Minor policy violation without evidence of malicious intent.

Minor mistakes by trusted residents should normally be classified as Low.

════════════════════
ESCALATION RULES
════════════════════

Do NOT escalate based solely on uncertainty.

Escalate only when additional evidence exists, such as:

• repeat behaviour
• multiple correlated incidents
• degraded trust score
• malicious context
• attempted forced entry

Missing information alone is NOT sufficient reason to assign High.

════════════════════
DECISION PRIORITY
════════════════════

When multiple severities appear possible:

1. If explicit benign evidence exists → choose Low.
2. If the incident requires human verification → choose Medium.
3. Only choose High when there is strong evidence of malicious behaviour.

Prefer:

Low → Medium → High

rather than automatically escalating.

════════════════════
TARGET INTERFACE
════════════════════

No Alert → []

Low → ["resident"]

Medium → ["resident", "security"]

High → ["security", "resident", "admin"]

If there is no responsible resident, remove "resident" from the notification list while keeping the remaining recipients.

════════════════════
TRUST SCORE
════════════════════

Do NOT calculate trust score.

Only explain whether a trust score penalty is justified.

No Alert always means no penalty.

════════════════════
EPISODIC MEMORY
════════════════════

Use previous alerts to identify genuine repeat behaviour.

Do not escalate merely because an older incident exists.

Escalate only if the previous incidents demonstrate a meaningful pattern of repeated suspicious behaviour."""


# ═══════════════════════════════════════════════════════════════════════════════
# NODE: INVESTIGATE
# ═══════════════════════════════════════════════════════════════════════════════
def investigate_node(state: SecurityState) -> dict:
    """
    Pull the oldest anomaly from anomaly_queue (passed in via state),
    gather full context from DB, call Gemini, return updated state.
    """
    queue: list[dict] = list(state.get("anomaly_queue", []))
    if not queue:
        return {}

    incident    = queue.pop(0)
    # ----------------------------------------------------
# Enrich Tier-1 signal with simulated environment
# ----------------------------------------------------

    incident = enrich_context(incident)
    signal_type = incident["signal_type"]
    gate_id     = incident["gate_id"]
    user_id     = incident.get("responsible_user_id")
    ts          = incident.get("timestamp", "")

    print(f"\n{'═'*70}")
    print(f"🔍 [INVESTIGATE] {signal_type} @ {gate_id}  |  user: {user_id or 'UNKNOWN'}")
    print(f"   Scenario : {incident.get('scenario')}")

    print(f"   Context  : {incident.get('context')}")

    print(f"   Weather  : {incident.get('weather')}")

    print(f"   Metadata : {incident.get('metadata')}")
    print(f"   Remaining in queue after this: {len(queue)}")

    # ── context aggregation ────────────────────────────────────────────────
    history     = database.get_recent_anomalies(gate_id, user_id, seconds_back=1)
    correlation = database.get_cross_incident_correlation(ts, window_seconds=1)
    profile     = database.get_resident_full_profile(user_id) if user_id else None

    # derive quick stats for the prompt
    prior_tailgating_by_user = len(history.get("tailgating_by_user", []))
    prior_forced_at_gate     = len(history.get("forced_open_at_gate", []))
    correlated_other         = (
        len(correlation.get("correlated_tailgating", []))
        + len(correlation.get("correlated_forced_open", []))
    )
    trust_score = profile.get("trust_score", 1.0) if profile else None

    print(f"   📊 Prior tailgating (user, 1sec): {prior_tailgating_by_user}")
    print(f"   📊 Prior forced-open (gate, 1sec): {prior_forced_at_gate}")
    print(f"   📊 Correlated anomalies (±1sec): {correlated_other}")
    print(f"   📊 Current trust score: {trust_score if trust_score is not None else 'N/A (no user)'}")

    context_packet = {

        "incident": incident,

        "scenario": incident.get("scenario"),

        "scenario_context": incident.get("context"),

        "environment":{

            "weather":incident.get("weather"),

            "time_of_day":incident.get("hour"),

            "metadata":incident.get("metadata",{})

        },

        "resident":profile,

        "responsible_party":profile or "Unknown",

        "db_history_last_1sec":history,

        "cross_incident_1sec":correlation

    }

    # ----------------------------------------------------
# Pattern Cache
# ----------------------------------------------------

    cached = get_cached_result(incident)

    if cached is not None:

        print("⚡ Pattern Cache Hit")

        result = SecurityAlert(

            **cached

        )

    else:

        print("🧠 Pattern Cache Miss")

    print("   🤖 Sending to Gemini 2.5 Flash...")


    if cached is None:

        result = _structured_llm.invoke(

            [

                SystemMessage(

                    content=_SYSTEM_PROMPT

                ),

                *state.get(

                    "messages",

                    []

                ),

                HumanMessage(

                    content=(

                        "Analyse this security incident.\n\n"

                        + json.dumps(

                            context_packet,

                            default=str,

                            indent=2

                        )

                    )

                )

            ]

        )

        store_result(

            incident,

            result.model_dump()

        )

    # ── terminal display ───────────────────────────────────────────────────
    emoji = {"No Alert": "⚪", "Low": "🟡", "Medium": "🟠", "High": "🔴"}.get(result.severity, "⚪")
    target_str = ", ".join(result.target_interface) if result.target_interface else "none"
    print(f"\n  {'▓'*66}")
    print(f"  {emoji}  HEIMDALL ALERT  ──  [{result.severity.upper()}]")
    print(f"  Type     : {signal_type}")
    print(f"  Gate     : {gate_id}")
    print(f"  User     : {user_id or 'UNKNOWN'}")
    print(f"  Target   : {target_str}")
    print(f"  Summary  : {result.summary}")
    print(f"  Action   : {result.recommended_action}")
    print(f"  Trust ⚖️  : {result.trust_score_action}")
    print(f"  {'▓'*66}\n")

    alert_dict = {
        "signal_type":        signal_type,
        "gate_id":            gate_id,
        "timestamp":          ts,
        "user_id":            user_id,
        "severity":           result.severity,
        "summary":            result.summary,
        "target_interface":   result.target_interface,
        "recommended_action": result.recommended_action,
        "trust_score_action": result.trust_score_action,
        "trust_score_before": trust_score,
    }

    existing = list(state.get("investigation_results", []))
    existing.append(alert_dict)

    # episodic memory — short entry for future cross-referencing
    memory_msg = HumanMessage(
        content=(
            f"[MEMORY] {result.severity} alert — {signal_type} at {gate_id} "
            f"by {user_id or 'Unknown'}. "
            f"Trust score was {trust_score}. {result.summary}"
        )
    )

    return {
        "anomaly_queue":         queue,
        "investigation_results": existing,
        "messages":              [memory_msg],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# NODE: DISPATCH
# ═══════════════════════════════════════════════════════════════════════════════
def dispatch_node(state: SecurityState) -> dict:
    """
    Pop the oldest alert, apply the trust score penalty, save the report,
    and print the final dispatch line.
    """
    results: list[dict] = list(state.get("investigation_results", []))
    if not results:
        return {}

    alert   = results.pop(0)
    user_id = alert.get("user_id")

    # ── trust score update ─────────────────────────────────────────────────
    # "No Alert" severity is a deliberate suppression (e.g. scheduled maintenance,
    # sensor self-correction) — no penalty is applied, even if a user is attached.
    if user_id and alert["severity"] != "No Alert":
        ts_update = database.update_trust_score(user_id, alert["severity"])
        alert["trust_score_after"] = ts_update.get("new")
        alert["trust_score_delta"] = ts_update.get("delta")
        penalty_str = (
            f"  Trust score: {ts_update['old']} → {ts_update['new']}  "
            f"(Δ {ts_update['delta']:+.2f}  penalty for {alert['severity']} alert)"
        )
    elif alert["severity"] == "No Alert":
        alert["trust_score_after"] = None
        alert["trust_score_delta"] = None
        penalty_str = "  Trust score: skipped (No Alert severity — no penalty applies)"
    else:
        alert["trust_score_after"] = None
        alert["trust_score_delta"] = None
        penalty_str = "  Trust score: N/A (no authenticated user)"

    # ── save to DB ─────────────────────────────────────────────────────────
    # Always saved, even for No Alert — it's recorded for audit purposes,
    # it's simply not surfaced to anyone (target_interface will be []).
    

    route_alert(alert)

    database.save_investigation_report(alert)

    # ── terminal dispatch block ────────────────────────────────────────────
    bar = {
        "No Alert": "·",
        "Low":      "▬▬▬▬▬",
        "Medium":   "▬▬▬▬▬▬▬▬▬",
        "High":     "▬▬▬▬▬▬▬▬▬▬▬▬▬",
    }.get(alert["severity"], "")
    target_ui = alert.get("target_interface") or []
    target_ui_str = ", ".join(target_ui) if target_ui else "none (suppressed)"
    print(f"\n📡 [DISPATCH] {'═'*54}")
    print(f"  SEVERITY   : {alert['severity']} {bar}")
    print(f"  TYPE       : {alert['signal_type']}")
    print(f"  GATE       : {alert['gate_id']}")
    print(f"  USER       : {user_id or 'UNKNOWN'}")
    print(f"  TIME       : {alert.get('timestamp','N/A')}")
    print(f"  TARGET UI  : {target_ui_str}")
    print(f"  SUMMARY    : {alert['summary']}")
    print(f"  ACTION     : {alert['recommended_action']}")
    print(penalty_str)
    print(f"  💾 Report saved to Investigation_Reports")
    print(f"  {'═'*56}\n")

    return {"investigation_results": results}