import streamlit as st
import requests
import datetime
import pandas as pd
import os
import json
import re

# ✅ APIキー（デフォルト）
API_KEY = "Bou4nmnOLBjpnAgHKCwA7rGRhYWAZHab"
AREA = "130"  # 東京
SERVICES = [("テレビ", "tv"), ("ラジオ", "radio")]
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# --- 音楽番組判定関数（元コードから流用） ---
def is_music_program(prog):
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
    strong_exclude_keywords = [
        "Eテレ", "おかあさんといっしょ", "みいつけた！", "いないいないばあっ！",
        "ワンワン", "うたのお兄さん", "うたのお姉さん", "パッコロリン", "コレナンデ商会",
        "天才てれびくん", "シャキーン！", "ピタゴラスイッチ", "にほんごであそぼ", "えいごであそぼ",
        "みんなのうた", "名曲アルバム", "街角ピアノ", "ラジオ深夜便", "名曲の小箱", "クラシック倶楽部",
        "古楽の楽しみ", "邦楽百番", "ジャズ・トゥナイト", "名曲スケッチ", "音楽遊覧飛行", "弾き語りフォーユー",
        "FM能楽堂", "芸能きわみ堂", "おとうさんといっしょ", "あおきいろ", "ひるのいこい", "ラジオ文芸館",
        "深夜便アーカイブス", "日本列島くらしのたより", "明日へのことば", "リワインドタイム",
        "連続テレビ小説", "大河ドラマ", "ドラマ", "時代劇", "シネマ", "ニュース", "報道",
        "天気", "スポーツ", "旅", "ドキュメンタリー", "バラエティ", "情報", "教養", "福祉",
        "語学", "趣味", "実用", "生活", "歴史", "自然百景", "国宝", "コズミックフロント",
        "謎解き", "顔に魅せられた男", "やまとの季節", "大岡越前", "べらぼう", "国宝へようこそ",
        "さわやか自然百景", "美の壺", "プレミアムシアター", "Ｎ響演奏会", "駅ピアノ", "ジャズＳＰアワー",
        "ザ・ミュージック・ブック", "歌謡スクランブル", "オペラ・ファンタスティカ", "小原孝のやすらぎクラシック",
        "ベストオブクラシック", "マイ・フェイバリット・アルバム", "のど自慢", "民謡魂", "全国学校音楽コンクール", "音楽の泉",
        "現代の音楽", "ウィークエンドサンシャイン", "世界の快適音楽セレクション", "ラジオマンジャック",
        "ザ・ソウルミュージック", "クラシックの迷宮", "クラシック音楽館", "映像詩", "リサイタル・パッシオ",
        "ビバ！合唱", "名演奏ライブラリー", "×（かける）クラシック", "吹奏楽のひびき", "ジャズ・ヴォヤージュ",
        "古家正亨のＰＯＰ★Ａ", "眠れない貴女（あなた）へ", "おんがくブラボー", "邦楽のひととき",
        "びじゅチューン！", "クラシックの庭", "空港ピアノ", "ＦＭ能楽堂", "ライブジャポニズム！"
    ]
    title = prog.get("title", "")
    subtitle = prog.get("subtitle", "")
    if not subtitle:
        subtitle = prog.get("content", "")
    act = prog.get("act", "")
    genres = prog.get("genres", [])
    text_to_check = f"{title} {subtitle} {act}".lower()
    service_name = prog.get("service", {}).get("name", "")
    is_radio = "ラジオ" in service_name or "FM" in service_name.upper()
    exclude_genre_codes_radio = ["0407", "0411", "0412"]
    if is_radio:
        for genre_code in genres:
            if genre_code in exclude_genre_codes_radio:
                return False
    for sek in strong_exclude_keywords:
        if sek.lower() in text_to_check:
            return False
    is_genre_music = False
    is_genre_non_music_major = False
    for genre_code in genres:
        if genre_code.startswith('04'):
            is_genre_music = True
        if genre_code.startswith(('00', '01', '02', '03', '05', '06', '07', '08', '09', '10', '11', '12')):
            if not genre_code.startswith('04'):
                is_genre_non_music_major = True
    if is_genre_music:
        return True
    if is_genre_non_music_major and not is_genre_music:
        return False
    for mk in music_keywords:
        if mk.lower() in text_to_check:
            return True
    return False

# --- 番組データ取得・整形 ---
@st.cache_data(show_spinner=True)
def get_music_programs(start_date):
    today = datetime.date.today()
    max_api_date = today + datetime.timedelta(days=6)
    if start_date < today:
        return pd.DataFrame([{"メッセージ": "過去の日付は選択できません。"}])
    if start_date > max_api_date:
        start_date = today
    date_list = []
    current_date = start_date
    while current_date <= max_api_date:
        date_list.append(current_date.strftime("%Y-%m-%d"))
        current_date += datetime.timedelta(days=1)
    all_programs = []
    for date in date_list:
        for service_name, service_code in SERVICES:
            cache_file_path = os.path.join(CACHE_DIR, f"nhk_programs_{date}_{service_code}.json")
            programs_from_cache = None
            if os.path.exists(cache_file_path):
                try:
                    with open(cache_file_path, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                        if isinstance(cached_data, dict) and "list" in cached_data:
                            programs_by_service = cached_data["list"]
                            if isinstance(programs_by_service, dict):
                                all_programs_for_date_service = []
                                for sub_service_code, progs_list in programs_by_service.items():
                                    if isinstance(progs_list, list):
                                        all_programs_for_date_service.extend(progs_list)
                                if all_programs_for_date_service:
                                    programs_from_cache = all_programs_for_date_service
                except Exception:
                    programs_from_cache = None
            if programs_from_cache:
                all_programs_for_date_service = programs_from_cache
            else:
                url = f"https://api.nhk.or.jp/v2/pg/list/{AREA}/{service_code}/{date}.json?key={API_KEY}"
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    json_data = response.json()
                except Exception:
                    continue
                programs_by_service = json_data.get("list")
                if not programs_by_service:
                    continue
                all_programs_for_date_service = []
                if isinstance(programs_by_service, dict):
                    for sub_service_code, progs_list in programs_by_service.items():
                        if isinstance(progs_list, list):
                            all_programs_for_date_service.extend(progs_list)
                if not all_programs_for_date_service:
                    continue
                with open(cache_file_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
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
    if not all_programs:
        return pd.DataFrame([{"メッセージ": "該当する音楽番組はありませんでした。"}])
    df = pd.DataFrame(all_programs)
    if "放送日時" in df.columns:
        def parse_datetime(s):
            if not isinstance(s, str):
                return None
            m = re.match(r"(\d{4})年(\d{2})月(\d{2})日.*?(\d{2}):(\d{2})", s)
            if m:
                return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
            return None
        df["_sort_dt"] = df["放送日時"].apply(parse_datetime)
        df = df.sort_values("_sort_dt").drop(columns=["_sort_dt"]).reset_index(drop=True)
    def trim_text(text, length=100):
        if isinstance(text, str) and len(text) > length:
            return text[:length] + "..."
        return text
    df["出演者情報"] = df["出演者情報"].apply(lambda x: trim_text(x, 50))
    df["番組内容詳細"] = df["番組内容詳細"].apply(lambda x: trim_text(x, 100))
    return df

# --- Streamlit UI ---
st.set_page_config(page_title="NHK音楽番組スケジューラー", layout="wide")
st.title("NHK音楽番組スケジューラー")
st.write("NHKの音楽番組スケジュールを自動取得・整理します。\n\n- 検索開始日を選択してください（本日から7日先まで）。\n- 番組表は音楽番組のみ抽出されます。\n- 検索結果はテーブルで表示されます。\n")

today = datetime.date.today()
start_date = st.date_input("検索開始日", value=today, min_value=today, max_value=today+datetime.timedelta(days=6), format="YYYY-MM-DD")

if st.button("番組表を取得"):
    with st.spinner("番組情報を取得中..."):
        df = get_music_programs(start_date)
    st.write("### 検索結果")
    st.dataframe(df, use_container_width=True)
    if "メッセージ" in df.columns:
        st.warning(df["メッセージ"].iloc[0])
else:
    st.info("検索開始日を選択し、\"番組表を取得\"ボタンを押してください。") 