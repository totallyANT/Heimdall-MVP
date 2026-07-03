from context_generator import enrich_context

signal = {

    "signal_type":"TAILGATING",

    "gate_id":"north_gate",

    "responsible_user_id":"RES001"

}

print(

    enrich_context(signal)

)