## 調査
週間天気予報を確認する場合に通常アクセスするURL\
https://www.jma.go.jp/bosai/forecast/#area_type=offices&area_code=250000

読み込まれるJSON\
https://www.jma.go.jp/bosai/forecast/data/forecast/250000.json?__time__=202103021201

URLにアクセス日時`time`がない場合でも取得可能。キャッシュなどの問題を考えてtimeは付けた方が良いと思う。\
https://www.jma.go.jp/bosai/forecast/data/forecast/250000.json


エリアには5種類の詳細度がある。　http://www.jma.go.jp/bosai/common/const/area.json
- centers　気象台
- offices　都道府県レベル
- class10s　県北部南部等（週間天気予報が発表される範囲）
- class15s
- class20s　市区町村

officesにはclass10sのchildrensが一つ以上存在する。滋賀なら、南部を表す250010と北部を表す250020だ。

週間天気予報の最高・最低気温の取得には、class10sと対応するアメダスの番号が必要。以下で取得可能。\
https://www.jma.go.jp/bosai/forecast/const/week_area.json

weatherCodesと天気の対応関係はjsonではなく、HTML本体に`Const.TELOPS`として記述されている。

## 取得の流れ
週間天気予報の取得方法
事前準備
1. 都道府県レベル`offices`+県北部南部等レベル`class10s`のエリアを決定 e.g. 250000, 250010 http://www.jma.go.jp/bosai/common/const/area.json
2. class10sに対応するamedasの番号を取得 e.g. 60216 https://www.jma.go.jp/bosai/forecast/const/week_area.json
3. TELOPSの保存
毎回
1. JSONの取得 https://www.jma.go.jp/bosai/forecast/data/forecast/250000.json
2. 最初の配列は週間天気予報がある len(timeSeries>timeDefines) == 7 の方を選択。len == 3 は明後日までの予報
3. 日付列を取得
4. timeSeriesの要素の中で、areasの要素の中で、2重列挙を行い、area>codeがclass10sに当てはまれば天気、amedasに当てはまれば最高・最低気温を取得
5. 天気をtelopsを用いて文字列に変換、時刻を日付に変換
6. 3.4.で取得した日付、天気、最高・最低をzipしてical化

この方法だと明日の気温もわからない問題がある。実際には明後日までの天気も読み取ることが必要。

## 日付変換
``` python
import dateutil.parser
dateutil.parser.parse("2021-03-03T00:00:00+09:00").date()
# 返り値は現在使用しているdate型。
```
