import calendar
import re
from datetime import datetime, date
from functools import lru_cache

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


@lru_cache
def get_default_calendar_dict(year):
    def _filter_date(date_obj):
        if date_obj.year == year:
            return True

    def _sublist_to_set(list_obj):
        for item in list_obj:
            if isinstance(item, list):
                _sublist_to_set(item)

            elif _filter_date(item):
                date_set.add(item)

    date_set = set()
    raw_data = calendar.Calendar().yeardatescalendar(year=year)
    _sublist_to_set(raw_data)

    calendar_dict = {}
    for date_obj in date_set:
        day_status = "Рабочий день"

        if date_obj.weekday() in [5, 6]:
            day_status = "Выходной"

        calendar_dict[date_obj.isoformat()] = day_status
    return calendar_dict


def get_prod_calendar_dict():
    """This function gets actual production calendar from HeadHunter"""

    # Get default calendar dictionary
    year = datetime.now().year
    default_calendar = get_default_calendar_dict(year=year)

    try:
        # Get raw html
        url = "https://hh.ru/calendar"
        headers = {"User-Agent": UserAgent().chrome}
        html_doc = requests.get(url=url, headers=headers)
        soup = BeautifulSoup(html_doc.text, features="html.parser")

        # Get calendar data
        calendar_data = soup.find(class_="calendar")

        # Get quarters data
        quarters = calendar_data.find_all(class_="calendar-list")

        # Get months data
        months = []
        for quarter in quarters:
            months.extend(quarter.find_all(class_="calendar-list__item"))

        # Clear data
        for month in months:
            for elem in month.find_all(class_=["calendar-hint"]):
                elem.decompose()

        # Leave shortened days and days-off only
        months = [
            month.find_all(
                class_=[
                    "calendar-list__numbers__item_day-off",
                    "calendar-list__numbers__item_shortened",
                ]
            )
            for month in months
        ]

        # Setup result dictionary
        result = default_calendar.copy()

        # Filling default calendar dictionary with days-off and shortened days
        for index, month in enumerate(months, start=1):
            for day in month:
                day = day.__str__()
                day_number = int(re.search(r"\d{1,2}", day)[0])
                if re.search("calendar-list__numbers__item_day-off", day) is not None:
                    result.update(
                        {
                            date(
                                year=year, month=index, day=day_number
                            ).isoformat(): "Выходной"
                        }
                    )
                    continue
                if re.search("calendar-list__numbers__item_shortened", day) is not None:
                    result.update(
                        {
                            date(
                                year=year, month=index, day=day_number
                            ).isoformat(): "Сокращённый день"
                        }
                    )
                    continue
    except:
        return default_calendar

    return result
