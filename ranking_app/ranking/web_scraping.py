from ranking.models import *
content_getter = ScrapingContent()
res = content_getter.get_html_with_chrome_from('https://hamehura-anime.com/')


url = content_getter.create_url('/program', anime_default=True)
response = content_getter.get_html_from(url)
contents_data = content_getter.extra_data_from(response)

from collections import Counter
import re


# for data in contents_data:
#     url = data['official_url']
#     response = contents_data.get_html(url)
#     soup = BeautifulSoup(response.data, 'html.parser')
#     a_tag_list = soup.find_all('a')
#     pattern = r'href="(https://twitter.com/\w+)"'
#     repatter = re.compile(pattern)
#     extract_a_tag_list = repatter.findall(str(a_tag_list))
#     twitter_url = Counter(extract_a_tag_list).most_common()[0][0]
#     screen_name_pattern = r'https://twitter.com/(\w+)'
#     screen_name_repatter = re.compile(screen_name_pattern)
#     screen_name = screen_name_repatter.match(twitter_url).groups()[0]
# screen_name = re.match(r'https://twitter.com/(\w+)', twitter_url).groups()[0]


# screen_nameの取得まで

# 除外する内容
'https://twitter.com/share'
'https://twitter.com/BS7ch_PR'
'https://twitter.com/TVTOKYO_PR'

# 取得できなかったもの
"""
乙女ゲームの破滅フラグしかない悪役令嬢に転生してしまった…
おりがみにんじゃ コーヤン＠きんてれ　share
俺の指で乱れろ。～閉店後二人きりのサロンで…～
カードファイト!! ヴァンガード外伝 イフ-if-
ガンダムビルドダイバーズ Re:RISE 2nd Season
グレイプニル
困ったじいさん
デュエル・マスターズキング
トミカ絆合体 アースグランナー
波よ聞いてくれ
のりものまん モービルランドのカークン
フルーツバスケット 2nd season
文豪とアルケミスト　〜審判ノ歯車〜
みっちりわんこ！あにめーしょん
遊☆戯☆王SEVENS
爆丸アーマードアライアンス
ベイブレードバースト スパーキング
魔神英雄伝ワタル 七魂の龍神丸
"""