import calendar
import itertools
import re
from datetime import date

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


def get_prod_calendar_dict():
    """This function gets production calendar from HeadHunter (07.04.2023)"""

    def get_raw_calendar_dict(year):
        raw_data = calendar.Calendar().yeardayscalendar(year)
        raw_data = list(itertools.chain(*raw_data))

        months = [
            list(filter(lambda num: num != 0, itertools.chain(*month)))
            for month in raw_data
        ]
        result = dict()
        for index, month in enumerate(months, 1):
            for day in month:
                result.update(
                    {date(year=year, month=index, day=day).isoformat(): "Рабочий день"}
                )
        return result

    # Get raw html
    url = "https://hh.ru/calendar"
    headers = {"User-Agent": UserAgent().chrome}
    html_doc = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(html_doc.text, features="html.parser")

    # Get production calendar year
    calendar_data = soup.find(class_="calendar")
    calendar_title = calendar_data.find("h1").text
    year = int(re.search(r"202\d", calendar_title)[0])

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

    # Leave only shortened days and days-off
    months = [
        month.find_all(
            class_=[
                "calendar-list__numbers__item_day-off",
                "calendar-list__numbers__item_shortened",
            ]
        )
        for month in months
    ]

    # Get raw calendar dictionary
    result = get_raw_calendar_dict(year=year)

    # Filling raw calendar dictionary with days-off and shortened days
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
    return result
