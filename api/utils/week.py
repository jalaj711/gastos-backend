from datetime import datetime
from math import ceil


def get_wom_from_date(date: datetime):
    """ Returns the week of the month for the specified date.
    """

    first_day = date.replace(day=1)
    adjusted_dom = date.day + first_day.weekday()

    return int(ceil(adjusted_dom/7.0))
