from datetime import datetime


def get_current_contract(instrument, date_str=None):
    contract = ""
    if date_str is None:
        today = datetime.now().date()
    else:
        today = datetime.strptime(date_str, "%Y-%m-%d")
    print("month: ", today.month)
    print("day:", today.day)
    print("year:", f"{today.year % 100:02d}")
    year = f"{today.year % 100:02d}"
    
    # Very simple quarterly logic (adjust the exact switch day if your broker rolls on a different date)
    if today.month < 3: 
        return f"{instrument}H{year}.CME"
    elif today.month == 3 and today.day < 18:
        # return instrument + "H26.CME"
        return f"{instrument}H{year}.CME"
    elif today.month == 3 and today.day >= 18:
        # return instrument + "M26.CME"
        return f"{instrument}M{year}.CME"
    elif today.month < 6:
        # return instrument + "M26.CME"
        return f"{instrument}M{year}.CME"
    elif today.month == 6 and today.day < 15:
        # return instrument + "M26.CME"
        return f"{instrument}M{year}.CME"
    elif today.month == 6 and today.day >= 15:
        # return instrument + "U26.CME"
        return f"{instrument}U{year}.CME"
    elif today.month < 9:
        # return instrument + "U26.CME"
        return f"{instrument}U{year}.CME"
    elif today.month == 9 and today.day < 15:
        return f"{instrument}U{year}.CME"
    elif today.month == 9 and today.day >= 15:
        return f"{instrument}Z{year}.CME"
    else: 
        return f"{instrument}Z{year}.CME"