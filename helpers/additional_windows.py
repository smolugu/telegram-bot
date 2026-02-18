ADDITIONAL_WINDOWS = [

    # London / Early NY manipulation window
    {
        "name": "london_reversal",
        "start": {"hour": 3, "minute": 0},
        "end": {"hour": 5, "minute": 0}
    },

    # NY Lunch reversal window
    {
        "name": "ny_lunch",
        "start": {"hour": 12, "minute": 0},
        "end": {"hour": 13, "minute": 30}
    }

]

SPECIFIC_WINDOWS = {
    "current_wick": [],
    "ny_lunch": ("12:00", "13:30"),
    "london_reversal": ("03:00", "05:00"),
}
