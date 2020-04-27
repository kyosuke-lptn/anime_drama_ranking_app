from ranking.models import *
content_getter = ScrapingContent()
url = content_getter.create_url('/program', anime_default=True)
response = content_getter.get_html_from(url)
contents_data = content_getter.extra_data_from(response)


# 取得できなかったもの
"""
おりがみにんじゃ コーヤン＠きんてれ　share
カードファイト!! ヴァンガード外伝 イフ-if-
困ったじいさん
デュエル・マスターズキング
トミカ絆合体 アースグランナー
文豪とアルケミスト　〜審判ノ歯車〜
みっちりわんこ！あにめーしょん
遊☆戯☆王SEVENS
爆丸アーマードアライアンス
ベイブレードバースト スパーキング
魔神英雄伝ワタル 七魂の龍神丸
"""



