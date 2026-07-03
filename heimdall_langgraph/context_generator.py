import random
from datetime import datetime

import database

from scenarios import (
    tailgating,
    door_forced,
    cloned_qr,
    visitor
)

# ------------------------------------------------------------------
# Environment Simulation
# ------------------------------------------------------------------

WEATHER = [
    "Sunny",
    "Cloudy",
    "Rainy",
    "Foggy",
    "Windy"
]


def get_weather():

    return random.choice(WEATHER)


def get_environment():

    return {

        "maintenance": random.random() < 0.08,

        "community_event": random.random() < 0.05,

        "delivery": random.random() < 0.12,

        "network_issue": random.random() < 0.03,

        "duplicate_scan": random.random() < 0.03,

        "shared_qr": random.random() < 0.02,

        "expired": random.random() < 0.02,

        "approved": random.random() < 0.80,

        "restricted": random.random() < 0.02,

        "overstay": random.random() < 0.03,

        "fire_alarm": False,

        "weather": get_weather()

    }


# ------------------------------------------------------------------
# Resident Loader
# ------------------------------------------------------------------

def load_resident(user_id):

    if user_id is None:

        return {

            "resident_id": None,

            "trust_score": 1.0,

            "family_members": 0

        }

    try:

        resident = database.get_resident_full_profile(user_id)

        if resident:

            return resident

    except Exception:

        pass

    return {

        "resident_id": user_id,

        "trust_score": 1.0,

        "family_members": 0

    }


# ------------------------------------------------------------------
# Scenario Selection
# ------------------------------------------------------------------

def choose_context(signal, resident):

    signal_type = signal["signal_type"]

    if signal_type == "TAILGATING":

        return tailgating.get_context(signal, resident)

    elif signal_type == "DOOR_ALARM":

        return door_forced.get_context(signal, resident)

    elif signal_type == "CLONED_QR":

        return cloned_qr.get_context(signal, resident)

    elif signal_type == "VISITOR":

        return visitor.get_context(signal, resident)

    return None


# ------------------------------------------------------------------
# Main Function
# ------------------------------------------------------------------

def enrich_context(signal):

    resident = load_resident(

        signal.get("responsible_user_id")

    )

    environment = get_environment()

    signal["metadata"] = environment

    signal["hour"] = datetime.now().hour

    scenario = choose_context(

        signal,

        resident

    )

    if scenario is None:

        return signal

    enriched = {

        **signal,

        "resident": resident,

        "weather": environment["weather"],

        "scenario": scenario["scenario"],

        "context": scenario["context"],

        "scenario_metadata": scenario["metadata"],

        "generated_at": datetime.now().isoformat()

    }

    return enriched