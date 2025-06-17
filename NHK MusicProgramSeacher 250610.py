# 📅 NHK音楽番組取得 Colabノートブック
# - APIキーはデフォルトで埋め込み済み
# - ユーザーは開始日だけ入力すればOK

import requests
import datetime
import pandas as pd
from IPython.display import display
import time
import os # 追加
import json # 追加
import tempfile
import webbrowser
import re

# ✅ APIキー（デフォルト）
API_KEY = "Bou4nmnOLBjpnAgHKCwA7rGRhYWAZHab"
AREA = "130"  # 東京
SERVICES = [("テレビ", "tv"), ("ラジオ", "radio")] # API呼び出しを効率化するため、包括的なサービスIDを使用
GENRE = "0409"  # 音楽・キッズ

# キャッシュディレクトリの定義と作成
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# 音楽番組を判断するヘルパー関数
def is_music_program(prog):
    # 音楽関連キーワード
    music_keywords = [
        "音楽", "歌", "ライブ", "コンサート", "メロディ", "ソング", "ミュージック",
        "バンド", "アーティスト", "アイドル", "ポップス", "ロック", "ジャズ",
        "クラシック", "演歌", "ヒップホップ", "R&B", "DJ", "FES", "フェス",
        "サウンド", "カバーズ", "SONGS", "J-MELO", "MUSIC SPECIAL", "ミュージックライン",
        "シンフォニー", "オペラ", "オーケストラ", "ピアノ", "ギター", "ドラム", "バイオリン",
        "楽器", "演奏", "合唱", "楽曲", "名曲", "カラオケ", "ベストソング", "リサイタル", "ジャム",
        "ポップ", "K-POP", "J-POP", "演歌", "歌謡", "歌劇", "合唱", "演奏会", "ミュージカル",
        "紅白歌合戦", "うたコン", "ザ少年倶楽部", "プレミアム", "うたの", "SOUND TRIPPER",
        "セッション", "ハーモニー", "吹奏楽", "雅楽", "ピアノ", "ギター", "ドラム", "バイオリン",
        "チェロ", "管弦楽", "指揮", "名演奏", "クラシックTV",
        "サウンドイマジン", "古家正亨のPOP★A", "音楽遊覧飛行", "弾き語りフォーユー",
        "歌謡スクランブル", "世界の快適音楽セレクション", "ベストオブクラシック", "ジャズ・ヴォヤージュ",
        "リサイタル・パッシオ", "古楽の楽しみ", "現代の音楽", "邦楽のひととき", "ミュージックサイレン"
    ]
    # 強力な除外キーワード（キッズ関連、その他一般的な非音楽番組タイトル）
    strong_exclude_keywords = [
        "Eテレ", "おかあさんといっしょ", "みいつけた！", "いないいないばあっ！",
        "ワンワン", "うたのお兄さん", "うたのお姉さん", "パッコロリン", "コレナンデ商会",
        "天才てれびくん", "シャキーン！", "ピタゴラスイッチ", "にほんごであそぼ", "えいごであそぼ",
        "みんなのうた", # ユーザーの要望により明示的に除外
        "名曲アルバム", # ユーザーの要望により明示的に除外
        "街角ピアノ", # ユーザーの要望により明示的に除外
        "ラジオ深夜便", # ユーザーの要望により明示的に除外
        "名曲の小箱", # 追加除外
        "クラシック倶楽部", # 追加除外
        "古楽の楽しみ", # 追加除外
        "邦楽百番", # 追加除外
        "ジャズ・トゥナイト", # 追加除外
        "名曲スケッチ", # 追加除外
        "音楽遊覧飛行", # 追加除外
        "弾き語りフォーユー", # 追加除外
        "FM能楽堂", # 追加除外
        "芸能きわみ堂", # 追加除外
        "おとうさんといっしょ", "あおきいろ", "ひるのいこい", "ラジオ文芸館",
        "深夜便アーカイブス", "日本列島くらしのたより", "明日へのことば", "リワインドタイム",
        "連続テレビ小説", "大河ドラマ", "ドラマ", "時代劇", "シネマ", "ニュース", "報道",
        "天気", "スポーツ", "旅", "ドキュメンタリー", "バラエティ", "情報", "教養", "福祉",
        "語学", "趣味", "実用", "生活", "歴史", "自然百景", "国宝", "コズミックフロント",
        "謎解き", "顔に魅せられた男", "やまとの季節", "大岡越前", "べらぼう", "国宝へようこそ",
        "さわやか自然百景", "美の壺",
        # ユーザー追加分
        "プレミアムシアター", "Ｎ響演奏会", "駅ピアノ", "ジャズＳＰアワー", "ザ・ミュージック・ブック",
        "歌謡スクランブル", "オペラ・ファンタスティカ", "小原孝のやすらぎクラシック", "ベストオブクラシック",
        "マイ・フェイバリット・アルバム", "のど自慢", "民謡魂", "全国学校音楽コンクール", "音楽の泉",
        "現代の音楽", "ウィークエンドサンシャイン", "世界の快適音楽セレクション", "ラジオマンジャック",
        "ザ・ソウルミュージック", "クラシックの迷宮", "クラシック音楽館", "映像詩", "リサイタル・パッシオ",
        "ビバ！合唱", "名演奏ライブラリー", "×（かける）クラシック", "吹奏楽のひびき", "ジャズ・ヴォヤージュ",
        "古家正亨のＰＯＰ★Ａ", "眠れない貴女（あなた）へ", "おんがくブラボー", "邦楽のひととき",
        "びじゅチューン！",
        # ユーザー追加分（2024-07-01）
        "クラシックの庭", "空港ピアノ", "ＦＭ能楽堂", "ライブジャポニズム！"
    ]

    title = prog.get("title", "")
    subtitle = prog.get("subtitle", "")
    if not subtitle:
        subtitle = prog.get("content", "") # subtitleが空の場合、contentから取得
    act = prog.get("act", "")
    genres = prog.get("genres", []) # ジャンル情報も活用

    text_to_check = f"{title} {subtitle} {act}".lower()

    # --- ラジオ放送でクラシック音楽・民謡・邦楽ジャンルを除外 ---
    service_name = prog.get("service", {}).get("name", "")
    # NHK APIのラジオサービス名は「ラジオ第1」「ラジオ第2」「NHK-FM」など
    is_radio = "ラジオ" in service_name or "FM" in service_name.upper()
    exclude_genre_codes_radio = ["0407", "0411", "0412"]  # クラシック音楽, 邦楽, 民謡
    if is_radio:
        for genre_code in genres:
            if genre_code in exclude_genre_codes_radio:
                return False

    # 強力な除外キーワードが含まれているかチェック
    for sek in strong_exclude_keywords:
        if sek.lower() in text_to_check:
            return False

    # ジャンルコードから判断する
    is_genre_music = False
    is_genre_non_music_major = False # 音楽ではない主要ジャンル
    
    for genre_code in genres:
        if genre_code.startswith('04'): # 音楽の大分類
            is_genre_music = True
        # 音楽ではない主要ジャンルコード
        # 00:ニュース/報道, 01:スポーツ, 02:情報/ワイドショー, 03:ドラマ, 05:映画,
        # 06:劇場/エンタメ(音楽以外), 07:教育/福祉, 08:ドキュメンタリー/教養,
        # 09:自然/科学, 10:アニメ/特撮, 11:生活/実用, 12:文字/その他
        if genre_code.startswith(('00', '01', '02', '03', '05', '06', '07', '08', '09', '10', '11', '12')):
            if not genre_code.startswith('04'): # 音楽ジャンルでなければ非音楽主要ジャンルと判断
                is_genre_non_music_major = True

    # 音楽ジャンルが含まれていれば音楽番組と判断
    if is_genre_music:
        return True
    
    # 音楽ではない主要ジャンルが含まれていて、かつ音楽ジャンルが含まれていなければ非音楽番組と判断
    if is_genre_non_music_major and not is_genre_music:
        return False

    # キーワードが含まれているかチェック (ジャンルコードで判断できなかった場合、または補助的に)
    # ここは、ジャンルコードだけでは判断しきれない音楽番組を拾うために残す
    for mk in music_keywords:
        if mk.lower() in text_to_check:
            return True

    return False

# 🖊 ユーザー入力：開始日（例：YYYY-MM-DD）
today = datetime.date.today()
max_api_date = today + datetime.timedelta(days=6) # APIがサポートする最大日付（今日から7日後）

while True:
    start_input = input("開始日を入力してください（例: YYYY-MM-DD）：")
    try:
        requested_start_date = datetime.datetime.strptime(start_input.strip(), "%Y-%m-%d").date()
        if requested_start_date < today:
            print("⛔ 過去の日付は入力できません。本日以降の日付を入力してください。")
        else:
            break # 有効な日付が入力された
    except ValueError:
        print("⛔ 正しい日付形式で入力してください（例：YYYY-MM-DD）")

# 📆 検索対象とする日付リストを生成（APIの制約に合わせて調整）
date_list = []
current_date = requested_start_date

# 検索開始日がAPIの範囲外の場合、今日から7日間の範囲に調整する
if requested_start_date > max_api_date:
    print(f"⚠️ 入力された開始日 ({requested_start_date.strftime('%Y-%m-%d')}) は、APIがサポートする検索期間（本日({today.strftime('%Y-%m-%d')})から7日後({max_api_date.strftime('%Y-%m-%d')})まで）の範囲外です。本日からの番組を検索します。")
    current_date = today # 今日から検索を開始

# 実際に検索する日付を生成
while current_date <= max_api_date:
    date_list.append(current_date.strftime("%Y-%m-%d"))
    current_date += datetime.timedelta(days=1)

# 🔍 番組取得と整理
all_programs = []

for date in date_list:
    for service_name, service_code in SERVICES:
        cache_file_path = os.path.join(CACHE_DIR, f"nhk_programs_{date}_{service_code}.json")

        programs_from_cache = None
        if os.path.exists(cache_file_path):
            try:
                with open(cache_file_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    # キャッシュデータが辞書型であり、かつ 'list' キーが存在するかを確認
                    if isinstance(cached_data, dict) and "list" in cached_data:
                        programs_by_service = cached_data["list"]
                        if isinstance(programs_by_service, dict):
                            all_programs_for_date_service = []
                            for sub_service_code, progs_list in programs_by_service.items():
                                if isinstance(progs_list, list):
                                    all_programs_for_date_service.extend(progs_list)
                            if all_programs_for_date_service:
                                programs_from_cache = all_programs_for_date_service
                                print(f"✅ {date} {service_name} の番組情報をキャッシュから読み込みました。")
            except Exception as e:
                print(f"⚠️ キャッシュファイル {cache_file_path} の読み込み中にエラーが発生しました: {e}。APIから再取得します。")
                programs_from_cache = None

        if programs_from_cache:
            all_programs_for_date_service = programs_from_cache
        else:
            # url = f"https://api.nhk.or.jp/v2/pg/genre/{AREA}/{service_code}/{GENRE}/{date}.json?key={API_KEY}"
            url = f"https://api.nhk.or.jp/v2/pg/list/{AREA}/{service_code}/{date}.json?key={API_KEY}"
            
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    break # 成功した場合はループを抜ける
                except requests.exceptions.HTTPError as http_err:
                    if http_err.response.status_code == 429: # Rate Limit Exceeded
                        print(f"⚠️ {date} {service_name} の取得失敗: HTTPエラー 429 - レート制限に達しました。リトライします... (試行 {attempt + 1}/{max_retries})")
                        time.sleep(2 ** attempt) # 指数バックオフ
                        if attempt == max_retries - 1:
                            print(f"❌ {date} {service_name} の取得失敗: 最大リトライ回数に達しました。 (URL: {url})")
                            continue # 次のサービス/日付に進む
                    else:
                        print(f"⚠️ {date} {service_name} の取得失敗: HTTPエラー {http_err.response.status_code} - {http_err.response.text} (URL: {url})")
                        continue
                except Exception as e:
                    print(f"⚠️ {date} {service_name} の取得失敗: {type(e).__name__} - {e}")
                    continue
            else: # ループがbreakせずに完了した場合 (全ての試行が失敗した場合)
                continue # 次のサービス/日付に進む

            # ここからresponseが成功していると仮定
            json_data = response.json()
            programs_by_service = json_data.get("list") # This will be a dict like {"g1": [...], "e1": [...]}

            if not programs_by_service: # If "list" is empty or not present
                print(f"⚠️ {date} {service_name} の番組情報が見つかりませんでした。")
                continue

            # Collect all programs from different sub-services
            all_programs_for_date_service = []
            if isinstance(programs_by_service, dict):
                for sub_service_code, progs_list in programs_by_service.items():
                    if isinstance(progs_list, list):
                        all_programs_for_date_service.extend(progs_list)
                    else:
                        print(f"⚠️ {date} {service_name} のサブサービス {sub_service_code} の番組リストが期待される形式ではありません。")
            else:
                print(f"⚠️ {date} {service_name} のAPIレスポンスの 'list' が期待される辞書型ではありません。")
                continue

            if not all_programs_for_date_service:
                print(f"⚠️ {date} {service_name} の番組情報が見つかりませんでした。")
                continue
            
            # 成功した場合のみキャッシュに保存
            with open(cache_file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            print(f"📁 {date} {service_name} の番組情報をキャッシュに保存しました: {cache_file_path}")

        for prog in all_programs_for_date_service:
            if is_music_program(prog):
                title = prog.get("title", "未公開")
                start = prog.get("start_time", "")
                end = prog.get("end_time", "")
                content = prog.get("content", "未公開")
                act = prog.get("act", "未公開")

                start_dt = datetime.datetime.fromisoformat(start) if start else None
                end_dt = datetime.datetime.fromisoformat(end) if end else None
                duration = (end_dt - start_dt).seconds // 60 if start_dt and end_dt else "未公開"

                formatted = {
                    "日付": start_dt.strftime("%Y年%m月%d日（%a）") if start_dt else date,
                    "放送波": prog.get("service", {}).get("name", "未公開"),
                    "番組タイトル": title,
                    "放送日時": f"{start_dt.strftime('%Y年%m月%d日（%a）%H:%M')}〜{end_dt.strftime('%H:%M')}" if start_dt and end_dt else "未公開",
                    "放送時間": f"{duration}分" if isinstance(duration, int) else duration,
                    "出演者情報": act,
                    "番組内容詳細": content
                }
                all_programs.append(formatted)

# 📋 DataFrameで表示
if not all_programs:
    print("⚠️ 音楽番組が見つかりませんでした。")
    # 空のDataFrameでもHTML出力
    df = pd.DataFrame([{"メッセージ": "該当する音楽番組はありませんでした。"}])
else:
    df = pd.DataFrame(all_programs)
    # 放送日時順に並べ替え（放送日時カラムをdatetime型に変換してソート）
    if "放送日時" in df.columns:
        # 放送日時カラムから日付・時刻部分を抽出し、datetime型に変換
        def parse_datetime(s):
            if not isinstance(s, str):
                return None
            m = re.match(r"(\d{4})年(\d{2})月(\d{2})日.*?(\d{2}):(\d{2})", s)
            if m:
                return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
            return None
        df["_sort_dt"] = df["放送日時"].apply(parse_datetime)
        df = df.sort_values("_sort_dt").drop(columns=["_sort_dt"]).reset_index(drop=True)

# 長いテキストをトリミングして表示を見やすくする
def trim_text(text, length=100):
    if isinstance(text, str) and len(text) > length:
        return text[:length] + "..."
    return text

df["出演者情報"] = df["出演者情報"].apply(trim_text, length=50)
df["番組内容詳細"] = df["番組内容詳細"].apply(trim_text, length=100)

# print(df.to_string())

# 一時ファイルにHTMLを書き出し、ブラウザで開く
with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
    html_output = df.to_html(index=False)
    f.write(html_output)
    temp_html_path = f.name

webbrowser.open('file://' + os.path.abspath(temp_html_path))
print(f"ブラウザで番組表を表示しました: {temp_html_path}")

# 💾 CSV保存（オプション）
# df.to_csv("NHK_music_schedule.csv", index=False)
# print("\\n📁 NHK音楽番組一覧をCSVファイルとして保存しました。")
