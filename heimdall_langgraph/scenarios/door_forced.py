import random

from .base import create_scenario


DOOR_CONTEXTS = {

    "maintenance": [

        "Maintenance personnel temporarily kept the entrance open while replacing access control equipment.",

        "Construction workers were transporting heavy materials through the entrance.",

        "Scheduled maintenance required the service entrance to remain open.",

        "Furniture movers temporarily blocked the automatic closing mechanism."

    ],

    "environment": [

        "Strong winds repeatedly forced the entrance door open.",

        "Emergency evacuation drill required all access doors to remain unlocked.",

        "Fire alarm triggered automatic unlocking of emergency exits."

    ],

    "minor": [

        "Resident accidentally held the entrance open while carrying luggage.",

        "Door closer failed to latch completely after a valid authentication.",

        "Security guard manually kept the entrance open for deliveries."

    ],

    "forced": [

        "Door sensor detected physical force being applied to the entrance.",

        "Unknown individual forced open the entrance without authentication.",

        "Repeated force attempts were detected before the door opened."

    ],

    "critical": [

        "Server room entrance was forced open after business hours.",

        "Forced entry followed multiple failed authentication attempts.",

        "Multiple forced entry attempts occurred at the same entrance within one hour."

    ]

}


def _select_category(signal, resident):

    hour = signal.get("hour", 12)

    metadata = signal.get("metadata", {})

    if metadata.get("maintenance"):

        return "maintenance"

    if metadata.get("weather") == "Windy":

        return "environment"

    if metadata.get("fire_alarm"):

        return "environment"

    if metadata.get("delivery"):

        return "minor"

    if hour >= 22:

        return "critical"

    return "forced"


def get_context(signal, resident):

    category = _select_category(signal, resident)

    return create_scenario(

        scenario="Door Forced Open",

        event_type="ACCESS_CONTROL",

        context=random.choice(

            DOOR_CONTEXTS[category]

        ),

        metadata={

            "category": category

        }

    )