import random

from .base import create_scenario


VISITOR_CONTEXTS={

    "approved":[

        "Visitor entered using a valid approved pass.",

        "Guest authenticated successfully.",

        "Resident approved visitor before arrival."

    ],

    "delivery":[

        "Food delivery entered after OTP verification.",

        "Courier entered using approved delivery access.",

        "Maintenance worker entered during scheduled hours."

    ],

    "overstay":[

        "Visitor remained inside the community beyond the expected checkout time.",

        "Visitor did not complete checkout after leaving.",

        "Guest exceeded approved visit duration."

    ],

    "restricted":[

        "Visitor entered a restricted residential block.",

        "Delivery partner attempted to access residential floors.",

        "Visitor entered the wrong tower."

    ],

    "critical":[

        "Visitor attempted entry using another visitor's QR.",

        "Fake visitor credentials were detected.",

        "Visitor entered after midnight without authorization.",

        "Visitor attempted re-entry using an invalid pass."

    ]

}


def _select(signal,resident):

    meta=signal.get("metadata",{})

    if meta.get("approved"):
        return "approved"

    if meta.get("delivery"):
        return "delivery"

    if meta.get("overstay"):
        return "overstay"

    if meta.get("restricted"):
        return "restricted"

    return "critical"


def get_context(signal,resident):

    category=_select(signal,resident)

    return create_scenario(

        scenario="Visitor",

        event_type="VISITOR_MANAGEMENT",

        context=random.choice(

            VISITOR_CONTEXTS[category]

        ),

        metadata={

            "category":category

        }

    )