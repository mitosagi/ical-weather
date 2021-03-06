# coding: utf-8
from icalendar import Calendar, Event
from datetime import datetime, date, timedelta

import requests
import dateutil.parser
from bs4 import BeautifulSoup
import json


def display(cal):
    return cal.to_ical().decode().replace('\r\n', '\n').strip()


def get_forecast(office, class10, amedas):
    # const
    telops = {}
    with open('telops.json') as json_file:
        telops = json.load(json_file)

    # urls
    cache_now = datetime.now().strftime('%Y%m%d%H%M')
    url_forecast = f'https://www.jma.go.jp/bosai/forecast/data/forecast/{office}.json?__time__={cache_now}'
    print(url_forecast)

    # main
    forecast = requests.get(url_forecast).json()
    forecast_week = {}
    forecast_3d = {}
    for forecast_3d_or_week in forecast:
        if "tempAverage" in forecast_3d_or_week:
            forecast_week = forecast_3d_or_week
        else:
            forecast_3d = forecast_3d_or_week

    forecast_areas = []
    for forecast_weather_or_temp in forecast_week["timeSeries"]:
        for forecast_area in forecast_weather_or_temp["areas"]:
            forecast_areas.append(forecast_area)

    timeDefines = [dateutil.parser.parse(
        d).date() for d in forecast_week["timeSeries"][0]["timeDefines"]]

    place = ""
    weathers = []
    tempsMin = []
    tempsMax = []
    for area in forecast_areas:
        if area["area"]["code"] == class10:
            weathers = [telops[w][3] for w in area["weatherCodes"]]
        if area["area"]["code"] == amedas:
            place = area["area"]["name"]
            tempsMin = area["tempsMin"]
            tempsMax = area["tempsMax"]

    return place, list(zip(timeDefines, weathers, tempsMax, tempsMin))


def write_ical():
    office = "250000"
    class10 = "250010"
    amedas = "60216"
    place, weatherlist = get_forecast(office, class10, amedas)

    # [iCalendar package — icalendar 4.0.5.dev0 documentation](https://icalendar.readthedocs.io/en/latest/usage.html)
    cal = Calendar()
    cal.add('version', '2.0')
    cal.add('prodid', '-//mitosagi//icalweather v1.0//EN')
    cal.add('X-WR-CALNAME', f'週間天気予報({place})')
    cal.add('X-WR-CALDESC', '気象庁の週間天気予報')
    cal.add('X-WR-TIMEZONE', 'Asia/Tokyo')
    for day, weather, max, min in weatherlist:
        event = Event()
        event.add('summary', f'{weather} {max}℃/{min}℃')
        event.add('dtstart', day)
        event.add('dtend', day + timedelta(days=1))
        event.add('DESCRIPTION',
                  f'詳細：https://www.jma.go.jp/bosai/forecast/#area_type=offices&area_code={office}')
        cal.add_component(event)

    with open('weather.ics', mode='w') as f:
        f.write(display(cal) + '\n')


if __name__ == '__main__':
    write_ical()
