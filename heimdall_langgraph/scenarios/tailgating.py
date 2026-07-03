import random

from .base import create_scenario


TAILGATING_CONTEXTS = {

    "family": [

        "Resident briefly held the gate open for their spouse carrying groceries.",

        "Resident allowed elderly parents to enter together after authenticating.",

        "Resident entered together with children returning from school.",

        "Resident held the gate open for another registered family member."

    ],

    "maintenance": [

        "Construction workers were unloading heavy materials while the gate remained open.",

        "Maintenance staff entered with the resident during scheduled work.",

        "Furniture delivery required the entrance to remain open temporarily."

    ],

    "community": [

        "Heavy rainfall caused multiple residents to enter together through the same gate.",

        "Residents entered together because of a society festival.",

        "Morning rush caused several authenticated residents to walk together."

    ],

    "unknown": [

        "Unknown individual closely followed an authenticated resident without presenting credentials.",

        "Person loitered near the entrance before following another resident inside.",

        "Unidentified individual avoided the authentication terminal before entering."

    ],

    "high_risk": [

        "Known blacklisted individual entered behind an authenticated resident.",

        "Tailgating occurred near midnight and the unknown individual proceeded toward a restricted area.",

        "Resident has been associated with repeated tailgating incidents within the last 24 hours."

    ]

}


def _select_category(signal, resident):

    hour = signal.get("hour", 12)

    metadata = signal.get("metadata", {})

    trust = resident.get("trust_score", 1.0)


    if metadata.get("maintenance"):

        return "maintenance"


    if metadata.get("community_event"):

        return "community"


    if resident.get("family_members", 0) > 0 and trust > 0.9:

        return "family"


    if trust < 0.5:

        return "high_risk"


    if hour >= 22 or hour <= 5:

        return "high_risk"


    return "unknown"



def get_context(signal, resident):

    category = _select_category(signal, resident)

    context = random.choice(

        TAILGATING_CONTEXTS[category]

    )

    return create_scenario(

        scenario="Tailgating",

        event_type="ACCESS_CONTROL",

        context=context,

        metadata={

            "category": category

        }

    )