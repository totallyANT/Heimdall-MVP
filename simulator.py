import os
import csv
import json
import time
import uuid
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    from pymongo import MongoClient
except ImportError as e:
    raise SystemExit(
        "pymongo is not installed. Run:\n"
        "    pip install pymongo --break-system-packages\n"
        "then re-run this script."
    ) from e

# Load environment variable mappings securely
load_dotenv()

GATES = ["lobby_entrance", "north_gate", "server_room_door"]
AUTH_TYPES = ["badge_swipe", "camera_scan"]

# =====================================================================
# 0. LOAD VALID RESIDENTS FROM ACTUAL ROSTER CSV
# =====================================================================
def load_resident_ids():
    return ["RES-101", "RES-112"]


# =====================================================================
# 1. GENERATORS (Now strictly driven by your actual resident IDs)
# =====================================================================
def generate_normal_entry(base_time, resident_ids):
    gate = random.choice(GATES)
    user_id = random.choice(resident_ids)
    auth_event = random.choice(AUTH_TYPES)
    
    payload = {"status": "success", "user_id": user_id}
    if auth_event == "badge_swipe":
        payload["credential_id"] = "rfid_ok"
    else:
        payload["confidence_score"] = f"{random.uniform(0.95, 0.99):.2f}"

    return [
        {"event_id": str(uuid.uuid4()), "timestamp": base_time.isoformat(), "gate_id": gate, "event_type": auth_event, "payload": payload},
        {"event_id": str(uuid.uuid4()), "timestamp": (base_time + timedelta(seconds=1)).isoformat(), "gate_id": gate, "event_type": "door_state_change", "payload": {"state": "open"}},
        {"event_id": str(uuid.uuid4()), "timestamp": (base_time + timedelta(seconds=2)).isoformat(), "gate_id": gate, "event_type": "person_counter_update", "payload": {"count": 1}}
    ]

def generate_tailgating_incident(base_time, resident_ids):
    gate = random.choice(GATES)
    user_id = random.choice(resident_ids)
    auth_event = random.choice(AUTH_TYPES)
    
    payload = {"status": "success", "user_id": user_id}
    if auth_event == "badge_swipe":
        payload["credential_id"] = "rfid_ok"
    else:
        payload["confidence_score"] = f"{random.uniform(0.95, 0.99):.2f}"

    return [
        {"event_id": str(uuid.uuid4()), "timestamp": base_time.isoformat(), "gate_id": gate, "event_type": auth_event, "payload": payload},
        {"event_id": str(uuid.uuid4()), "timestamp": (base_time + timedelta(seconds=1)).isoformat(), "gate_id": gate, "event_type": "door_state_change", "payload": {"state": "open"}},
        {"event_id": str(uuid.uuid4()), "timestamp": (base_time + timedelta(seconds=6)).isoformat(), "gate_id": gate, "event_type": "person_counter_update", "payload": {"count": 2}}
    ]

def generate_door_forced_incident(base_time):
    gate = "server_room_door"
    return [
        {"event_id": str(uuid.uuid4()), "timestamp": base_time.isoformat(), "gate_id": gate, "event_type": "door_sensor", "payload": {"state": "FORCED_OPEN"}},
        {"event_id": str(uuid.uuid4()), "timestamp": (base_time + timedelta(seconds=1)).isoformat(), "gate_id": gate, "event_type": "person_counter_update", "payload": {"count": 1}}
    ]


# =====================================================================
# 2. TIER-1 FILTER DETECTOR ENGINE (Routes & Saves Anomalies)
# =====================================================================
gate_history = {}

def process_event_locally(event, db_client):
    gate_id = event.get("gate_id")
    event_type = event.get("event_type")
    payload = event.get("payload", {})
    current_time = datetime.fromisoformat(event.get("timestamp"))

    if gate_id not in gate_history and gate_id is not None:
        gate_history[gate_id] = {
            "last_auth_time": None,
            "last_user_id": None
        }

    time_str = current_time.strftime("%H:%M:%S")
    payload_str = ", ".join([f"{k}: {v}" for k, v in payload.items()])
    print(f"⚙️  [LOG] [{time_str}] | Place: {gate_id:<18} | Event: {event_type:<22} | Details: {payload_str}")

    if event_type in AUTH_TYPES and payload.get("status") == "success":
        gate_history[gate_id]["last_auth_time"] = current_time
        gate_history[gate_id]["last_user_id"] = payload.get("user_id")

    elif event_type == "person_counter_update":
        count = payload.get("count", 0)
        if count > 1:
            last_auth = gate_history[gate_id]["last_auth_time"]
            responsible_user = gate_history[gate_id]["last_user_id"]
            
            if last_auth is None:
                trigger_candidate_signal(
                    "TAILGATING", gate_id, 
                    "Multiple people entered but no authentication records found.", 
                    event, db_client
                )
            else:
                time_diff = (current_time - last_auth).total_seconds()
                if time_diff > 5.0:
                    reason_msg = f"Tailgating breach. Entry detected {time_diff}s after authorization."
                    trigger_candidate_signal(
                        "TAILGATING", gate_id, reason_msg, event, db_client,
                        responsible_user_id=responsible_user
                    )

    elif event_type == "door_sensor":
        state = payload.get("state")
        if state == "FORCED_OPEN":
            trigger_candidate_signal(
                "DOOR_ALARM", gate_id, 
                "Hardware contact sensor registers physical forced break-in.", 
                event, db_client
            )

def trigger_candidate_signal(signal_type, gate_id, reason, trigger_event, db_client, responsible_user_id=None):
    # Assemble the formal candidate anomaly tracking payload
    signal = {
        "status": "CANDIDATE_SIGNAL",
        "incident_created": True,
        "signal_type": signal_type,
        "gate_id": gate_id,
        "timestamp": datetime.now().isoformat(),
        "reason": reason,
        "triggering_event": trigger_event
    }
    
    if responsible_user_id:
        signal["responsible_user_id"] = responsible_user_id
        
    print(f"\n🚨🚨🚨 [ALERT!!!] Tier-1 Detector Caught a {signal_type} Anomaly!")
    
    # --- ROUTING AND PUSHING TO CORRESPONDING MONGODB COLLECTIONS ---
    db = db_client["heimdall_security"]
    target_collection = ""
    
    if signal_type == "TAILGATING":
        target_collection = "Tailgating_incidents"
    elif signal_type == "DOOR_ALARM":
        target_collection = "Door_Forced_Open_Incidents"
        
    if target_collection:
        # Save to database
        db[target_collection].insert_one(signal)
        print(f"📥 [DATABASE SAVE SUCCESS] -> Written to cloud collection: '{target_collection}'")
        
        # Print exactly what was stored to the terminal
        print("💾 [RECORD DUMP]:")
        print(json.dumps(signal, indent=2, default=str))
        
        # --- PREPARATION LAYER FOR THE DYNAMIC LANGGRAPH AGENT INVOKER ---
        print("\n🤖 [LANGGRAPH TRIGGER POINT]: Preparing to pass context packet to downstream agent loop...")
        # Note: input_agent_invoke(signal) will be connected right here in the next step!
        
    print("=" * 80 + "\n", flush=True)


# =====================================================================
# 3. REALISTIC LIVE STREAM LOOP (Configured with 1-in-50 Anomaly Rate)
# =====================================================================
if __name__ == "__main__":
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        print("❌ Error: MONGO_URI missing from your '.env' cluster file configuration!")
        exit(1)
        
    print("Connecting to live MongoDB Atlas Cluster...")
    client = MongoClient(MONGO_URI)
    
    # Initialize valid active roster IDs
    try:
        resident_ids = load_resident_ids()
        print(f"Successfully loaded {len(resident_ids)} active resident targets for simulation tracking.")
    except Exception as e:
        print(e)
        exit(1)
        
    print("Heimdall Live Pipeline Engine Fully Functional. Streaming Sensor States...")
    print("-" * 80)
    
    simulated_clock = datetime.now()

    try:
        while True:
            simulated_clock += timedelta(seconds=random.randint(10, 45))
            
            # --- SCENARIO PROBABILITY SELECTION MATRIX ---
            # Adjusted to hit roughly a 2% (1-in-50) cumulative anomaly encounter trend line
            roll = random.random()
            
            if roll < 0.98:   # 49 out of 50 sequences on average will execute normal traffic
                sequence = generate_normal_entry(simulated_clock, resident_ids)
            elif roll < 0.99: # Tailgating split
                sequence = generate_tailgating_incident(simulated_clock, resident_ids)
            else:             # Forced door intrusion split
                sequence = generate_door_forced_incident(simulated_clock)

            for event in sequence:
                process_event_locally(event, client)
                
            print("-" * 40)
            time.sleep(1.5)  # Quick cycle pause for readable streaming visibility
            
    except KeyboardInterrupt:
        print("\nTelemetry acquisition terminated cleanly.")
        client.close()