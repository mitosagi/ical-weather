# coding: utf-8
from icalendar import Calendar, Event
from datetime import datetime, date, timedelta

import requests
from bs4 import BeautifulSoup


def main():
    # shiga otsu = 334, 0
    # shiga hikone = 334, 1
    pref_id = 334
    point = 0
    (pref, place, days, wt) = weather(pref_id, point)

    # [iCalendar package — icalendar 4.0.5.dev0 documentation](https://icalendar.readthedocs.io/en/latest/usage.html)
    cal = Calendar()
    cal.add('version', '2.0')
    cal.add('prodid', '-//mitosagi//icalweather v1.0//EN')
    cal.add('X-WR-CALNAME', f'週間天気予報({place})')
    cal.add('X-WR-CALDESC', '気象庁の週間天気予報')
    cal.add('X-WR-TIMEZONE', 'Asia/Tokyo')
    for day, w in zip(days, wt):
        event = Event()
        event.add('summary', w)
        event.add('dtstart', day)
        event.add('dtend', day + timedelta(days=1))
        event.add('DESCRIPTION',
                  f'詳細：https://www.jma.go.jp/jp/week/{pref_id}.html')
        cal.add_component(event)

    with open('weather.ics', mode='w') as f:
        f.write(display(cal) + '\n')


def display(cal):
    return cal.to_ical().decode().replace('\r\n', '\n').strip()


def weather(pref_id, point):
    load_url = f"https://www.jma.go.jp/jp/week/{pref_id}.html"
    html = requests.get(load_url)
    soup = BeautifulSoup(html.content, 'html5lib')
    data = soup.select_one('#infotablefont').select('tr')
    rows = data[1:][point*5:point*5 + 5]

    # get pref
    pref = soup.find('h1').text.split('：')[-1].strip()
    print(pref)

    # get place
    place = rows[3].find('th').text
    print(place)

    # get date
    first_day = int(data[0].select('th')[1].find(
        "br").previousSibling)  # e.g. 31

    if(not(1 <= first_day <= 31)):
        raise Exception

    full_date = date.today()
    attempt = 0
    max_attempt = 1

    while full_date.day != first_day:
        attempt += 1
        if attempt > max_attempt:
            raise Exception
        full_date += timedelta(days=1)

    days = [full_date + timedelta(days=i) for i in range(7)]
    print(days)

    # get weather
    weathers = [td.find("br").previousSibling for td in rows[0].select('td')]

    max_temp = [
        td.find("br").previousSibling if td.find("br") else '-' for td in rows[3].select('td')[1:]]
    min_temp = [
        td.find("br").previousSibling if td.find("br") else '-' for td in rows[4].select('td')[1:]]

    weather_temp = [f'{a} {b}℃/{c}℃'for a, b,
                    c in zip(weathers, max_temp, min_temp)]
    print(weather_temp)

    return (pref, place, days, weather_temp)


if __name__ == '__main__':
    main()
