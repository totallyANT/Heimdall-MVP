import random

from .base import create_scenario

QR_CONTEXTS = {

    "network":[

        "Resident rescanned the QR because the scanner response was delayed.",

        "Duplicate authentication occurred due to network latency.",

        "Security requested another QR scan after timeout.",

        "Authentication server retried the same QR validation."

    ],

    "duplicate":[

        "Resident scanned the same QR twice within a few seconds.",

        "QR authentication was repeated because the gate failed to respond.",

        "Resident refreshed and rescanned the QR."

    ],

    "shared":[

        "Resident shared a QR screenshot with another individual.",

        "QR code was detected from another mobile device.",

        "The same QR was presented by another person."

    ],

    "expired":[

        "Visitor attempted to use an expired QR pass.",

        "Resident used a revoked authentication QR.",

        "Authentication attempted with an inactive QR."

    ],

    "critical":[

        "Same QR was used simultaneously at North Gate and South Gate.",

        "QR belonging to another resident was successfully authenticated.",

        "Resident reported phone stolen but QR was later used.",

        "QR authenticated six entries within two minutes."

    ]

}


def _select(signal,resident):

    meta=signal.get("metadata",{})

    if meta.get("network_issue"):
        return "network"

    if meta.get("duplicate_scan"):
        return "duplicate"

    if meta.get("shared_qr"):
        return "shared"

    if meta.get("expired"):
        return "expired"

    return "critical"


def get_context(signal,resident):

    category=_select(signal,resident)

    return create_scenario(

        scenario="Cloned QR",

        event_type="AUTHENTICATION",

        context=random.choice(QR_CONTEXTS[category]),

        metadata={

            "category":category

        }

    )