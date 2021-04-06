# coding: utf-8
from icalendar import Calendar, Event
from datetime import datetime, date, timedelta

import requests
import dateutil.parser
from bs4 import BeautifulSoup
import json
import objectpath

def display(cal):
    return cal.to_ical().decode().replace('\r\n', '\n').strip()


def get_forecast(office):
    # const
    telops = {}
    with open('telops.json') as json_file:
        telops = json.load(json_file)

    # download
    cache_now = datetime.now().strftime('%Y%m%d%H%M')
    url_forecast = f'https://www.jma.go.jp/bosai/forecast/data/forecast/{office}.json?__time__={cache_now}'
    forecast = requests.get(url_forecast).json()

    # main
    def get_list(query):
        return list(objectpath.Tree(forecast).execute(query))

    # 一週間の最高最低気温
    # このコードはjson内の天気・気温等データの時刻に対する並び順が変わらないことを仮定しているため日付を取得してソートするなどの厳密な処理は行っていない
    # 週間天気のデータから県を代表するamedasのidを取得する
    amedas = get_list(f'$..*[timeDefines in @ and len(@..tempsMin) > 0]..code')[0]
    place = get_list(f'$..*[timeDefines in @ and len(@..tempsMin) > 0]..name')[0]

    date = [dateutil.parser.parse(d).date() for d in get_list(
        f'$..*[timeDefines in @ and len(@..tempsMin) > 0].timeDefines')[0]]

    maxt = get_list(f'$..*[timeDefines in @ and len(@..tempsMin) > 0]..tempsMax')
    mint = get_list(f'$..*[timeDefines in @ and len(@..tempsMin) > 0]..tempsMin')

    # 一週間の天気
    weathers = get_list(
        f'$..*[timeDefines in @ and "{office}" in @..code and len(@..weatherCodes) > 0]..*[@.area.code is "{office}"].weatherCodes')[0]

    # 今日明日の最高最低気温
    # 週間予報の配列を直接上書きする。今日明日の気温の配列は今日の分だけ最高気温が最低気温より前に格納されていることに注意

    ## 時間帯判定　5~11時なら週間天気予報と今日・明日の天気が、それ以外の時間は週間天気予報と明日の天気がオーバーラップしている
    ## これは週間天気予報が5時に発表されず、今日明日の天気に対して情報が古くなるために起こる
    day1 = get_list(f'$..*[timeDefines in @ and "{amedas}" in @..code and len(@..temps) > 0].timeDefines')[0][1]
    day2 = get_list(f'$..*[timeDefines in @ and len(@..tempsMin) > 0].timeDefines')[0][0]
    if day1 == day2: # データの古い5-11時
        maxt[1] = get_list(
            f'$..*[timeDefines in @ and "{amedas}" in @..code and len(@..temps) > 0]..*[@.area.code is "{amedas}"].temps')[0][3]
        mint[1] = get_list(
            f'$..*[timeDefines in @ and "{amedas}" in @..code and len(@..temps) > 0]..*[@.area.code is "{amedas}"].temps')[0][2]
        maxt[0] = get_list(
            f'$..*[timeDefines in @ and "{amedas}" in @..code and len(@..temps) > 0]..*[@.area.code is "{amedas}"].temps')[0][0]

    else:
        maxt[0] = get_list(
            f'$..*[timeDefines in @ and "{amedas}" in @..code and len(@..temps) > 0]..*[@.area.code is "{amedas}"].temps')[0][3]
        mint[0] = get_list(
            f'$..*[timeDefines in @ and "{amedas}" in @..code and len(@..temps) > 0]..*[@.area.code is "{amedas}"].temps')[0][2]
        # 配列を今日側に拡張
        date = [dateutil.parser.parse(day1).date()] + date
        weathers = [""] + weathers # 今日明日の天気の取得はamedasが存在するclass10を知っている必要があるので困難
        maxt = [get_list(
            f'$..*[timeDefines in @ and "{amedas}" in @..code and len(@..temps) > 0]..*[@.area.code is "{amedas}"].temps')[0][0]]\
            + maxt 
        mint = [""] + mint

    weathers = ["" if w == "" else telops[w][3] for w in weathers]

    return place, list(zip(date, weathers, maxt, mint))


def write_ical():
    office = "250000"
    # class10 = "250010"
    # amedas = "60216"
    place, weatherlist = get_forecast(office)

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
