extended_closure_long = [{
    "applies": {
        "start": "2000-01-01T00:00:00-04:00",
        "end": "2024-02-01T23:59:00-05:00"
    }
}]

# Closed 01-06
extended_closure_short = [{
    "applies": {
        "start": "2000-01-05T18:00:00-04:00",
        "end": "2000-01-07T10:00:00-05:00"
    }
}]

extended_closure_overlapping = [
    {
        "applies": {
            "start": "2000-01-05T18:00:00-04:00",
            "end": "2024-01-07T10:00:00-05:00"
        }
    },
    {
        "applies": {
            "start": "2000-01-05T18:00:00-04:00",
            "end": "2000-01-06T13:00:00-05:00"
        }
    }
]

temp_closure_overlapping = [{
    "applies": {
        "start": "2000-01-05T10:00:00-04:00",
        "end": "2000-01-05T14:00:00-05:00"
    }
},
    {
    "applies": {
        "start": "2000-01-05T11:00:00-04:00",
        "end": "2000-01-05T12:00:00-05:00"
    }
}
]

extended_closure_into_late_opening = [{
    "applies": {
        "start": "2000-01-05T18:00:00-04:00",
        "end": "2024-01-07T12:00:00-05:00"
    }
}]

early_closure = [{
    "applies": {
        "start": "2000-01-06T14:00:00-04:00",
        "end": "2000-01-07T10:00:00-04:00"
    }
}]

delayed_opening = [{
    "applies": {
        "start": "2000-01-06T18:00:00-04:00",
        "end": "2000-01-07T12:00:00-04:00"
    }
}]
