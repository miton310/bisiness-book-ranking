#!/usr/bin/env python3
"""YouTube Data APIで全動画を取得し、書籍情報を抽出してJSONを生成するスクリプト"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

# Amazonリンクから書籍情報取得
from fetch_amazon_info import extract_books_from_amazon_links

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not YOUTUBE_API_KEY:
    # .envファイルから読み込み
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("YOUTUBE_API_KEY="):
                    YOUTUBE_API_KEY = line.strip().split("=", 1)[1]

AMAZON_ASSOCIATE_TAG = "miton31003"
AMAZON_TRACKING_ID = "business-book-ranking02-22"

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


# =============================================================================
# YouTube Data API
# =============================================================================

def api_get(endpoint, params):
    """YouTube Data API にGETリクエスト"""
    params["key"] = YOUTUBE_API_KEY
    url = f"{YOUTUBE_API_BASE}/{endpoint}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_uploads_playlist_id(channel_id):
    """チャンネルのアップロード再生リストIDを取得"""
    data = api_get("channels", {
        "part": "contentDetails",
        "id": channel_id,
    })
    items = data.get("items", [])
    if not items:
        return None
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_all_video_ids(playlist_id):
    """再生リストから全動画IDを取得（ページネーション対応）"""
    video_ids = []
    page_token = None
    while True:
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        data = api_get("playlistItems", params)
        for item in data.get("items", []):
            vid = item["snippet"]["resourceId"]["videoId"]
            video_ids.append(vid)
        page_token = data.get("nextPageToken")
        if not page_token:
            break
        time.sleep(0.1)
    return video_ids


def get_video_details(video_ids):
    """動画IDリストから詳細情報を取得（50件ずつバッチ処理）"""
    videos = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        data = api_get("videos", {
            "part": "snippet,statistics",
            "id": ",".join(batch),
        })
        for item in data.get("items", []):
            snippet = item["snippet"]
            stats = item.get("statistics", {})
            videos.append({
                "video_id": item["id"],
                "title": snippet["title"],
                "published": snippet["publishedAt"],
                "link": f"https://www.youtube.com/watch?v={item['id']}",
                "summary": snippet.get("description", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
            })
        time.sleep(0.1)
    return videos


def fetch_all_channel_videos(channel_id):
    """チャンネルの全動画を取得"""
    playlist_id = get_uploads_playlist_id(channel_id)
    if not playlist_id:
        print(f"  [ERROR] アップロード再生リストが見つかりません")
        return []
    video_ids = get_all_video_ids(playlist_id)
    print(f"  動画ID取得: {len(video_ids)}件")
    videos = get_video_details(video_ids)
    print(f"  動画詳細取得: {len(videos)}件")
    return videos


# =============================================================================
# 書籍抽出ロジック（チャンネル別パターン対応）
# =============================================================================

def extract_book_info_list(summary, video_title=None):
    """概要欄・動画タイトルから書籍情報を抽出"""
    results = []

    # パターン0: 動画タイトルから抽出「【要約】タイトル【著者】」（フェルミ漫画大学等）
    if video_title:
        m = re.match(r'【(?:要約|漫画)】(.+?)【(.+?)】', video_title)
        if m:
            book_title = m.group(1).strip()
            author = m.group(2).strip()
            results.append({
                "title": book_title,
                "author": author,
                "publisher": None,
            })
            return results

    # TODO: Amazonリンクから書籍情報を取得（時間がかかるため一時的に無効化）
    # amazon_urls = re.findall(r'https?://amzn\.to/[A-Za-z0-9]+', summary)
    # if amazon_urls:
    #     amazon_books = extract_books_from_amazon_links(amazon_urls, max_books=5, context=summary)
    #     for book in amazon_books:
    #         results.append({
    #             "title": book["title"],
    #             "author": None,
    #             "publisher": None,
    #             "amazon_url": book["amazon_url"],
    #         })
    #     if results:
    #         return results

    # パターン1: 本要約チャンネル / サラタメさん「タイトル：」「著者：」「出版社：」
    title_match = re.search(r'タイトル[：:](.+)', summary)
    if title_match:
        info = {
            "title": title_match.group(1).strip(),
            "author": None,
            "publisher": None,
        }
        author_match = re.search(r'著者[：:](.+)', summary)
        if author_match:
            info["author"] = author_match.group(1).strip()
        publisher_match = re.search(r'出版社[：:](.+)', summary)
        if publisher_match:
            info["publisher"] = publisher_match.group(1).strip()
        results.append(info)
        return results

    # パターン2: フェルミ漫画大学「参考：書名 著者名 さま」
    # 「参考文献：」も対応
    ref_match = re.search(r'参考(?:文献)?[：:](.+?)(?:\s+さま|\s*$)', summary, re.MULTILINE)
    if ref_match:
        title_text = ref_match.group(1).strip()
        # 著者名だけの行を除外（「さま」で終わる人名のみ、書籍タイトルなし）
        if not re.match(r'^[\w\s・　]+さま', title_text) and title_text:
            results.append({
                "title": title_text,
                "author": None,
                "publisher": None,
            })
            return results

    # パターン3: 学識サロン「【amazonリンク】\n『書名』著者 / 出版社」
    if "【amazonリンク】" in summary:
        gakushiki_match = re.search(r'『(.+?)』(.+?)(?:\s*/\s*(.+))?$', summary, re.MULTILINE)
        if gakushiki_match:
            info = {
                "title": gakushiki_match.group(1).strip(),
                "author": None,
                "publisher": None,
            }
            if gakushiki_match.group(2):
                info["author"] = gakushiki_match.group(2).strip()
            if gakushiki_match.group(3):
                info["publisher"] = gakushiki_match.group(3).strip()
            results.append(info)
            return results

    # パターン4: サムの本解説ch「【今回の参考書籍📚】」セクション
    sam_section = re.search(
        r'【今回の参考書籍.*?】\s*\n(.*?)(?=【|$)', summary, re.DOTALL
    )
    if sam_section:
        section_text = sam_section.group(1).strip()
        lines = section_text.split('\n')
        title_line = None
        author_line = None
        for line in lines:
            line = line.strip()
            if not line or line.startswith('http'):
                continue
            # 著者行を判定: 「〜(著)」「〜（著）」を含む行
            if re.search(r'[（(]著[）)]', line):
                author_line = line
            elif not title_line:
                # 最初の非著者行をタイトルとして取得
                title_line = re.sub(r'\s*(Kindle版|単行本|文庫|新書|ハードカバー)\s*$', '', line).strip()
                # 先頭の「・」を除去
                title_line = re.sub(r'^[・･]', '', title_line).strip()
        if title_line:
            info = {"title": title_line, "author": None, "publisher": None}
            if author_line:
                author_match = re.match(r'(.+?)\s*[（(]著[）)]', author_line)
                if author_match:
                    info["author"] = author_match.group(1).strip()
                pub_match = re.search(r'([^\s]+?)[（(]編集[）)]', author_line)
                if pub_match:
                    info["publisher"] = pub_match.group(1).strip()
            results.append(info)
            return results

    # パターン5: PIVOT系「＜参考書籍＞」「▼参考書籍」「▼関連書籍」「▼本映像で紹介した書籍」セクション
    pivot_section = re.search(
        r'(?:[＜<]参考書籍[＞>]|▼参考書籍|▼関連書籍|▼本映像で紹介した書籍)\s*\n(.*?)(?=\n[＜<]|\n▼[^参関本]|\n[■●]|\n※|\n\n\n|$)', summary, re.DOTALL
    )
    if pivot_section:
        section_text = pivot_section.group(1).strip()
        lines = section_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('http') or line.startswith('※'):
                continue

            title = None
            author = None

            # パターンA: 『タイトル』を優先（内部に「」が含まれてもOK）
            book_match = re.search(r'『(.+?)』', line)
            if book_match:
                title = book_match.group(1).strip()
                before = line[:book_match.start()].strip()
                if before:
                    author = before
                after = line[book_match.end():].strip()
                if not author and after:
                    a_match = re.match(r'(.+?)\s*[（(]著[）)]', after)
                    if a_match:
                        author = a_match.group(1).strip()

            # パターンB: 「タイトル」＋後続テキストも含める
            if not title:
                book_match = re.search(r'「(.+?)」(.+?)(?=[（(]|https?://|\s*$)', line)
                if book_match:
                    # 「タイトル」の後ろもタイトルの一部として結合
                    title = book_match.group(1).strip() + book_match.group(2).strip()
                    # 末尾の括弧内（出版社等）を除去
                    title = re.sub(r'[（(][^）)]+[）)]$', '', title).strip()

            if not title:
                continue

            results.append({
                "title": title,
                "author": author,
                "publisher": None,
            })
        # PIVOTの参考書籍セクションがある場合は結果に関わらずここで返す
        # （パターン6のamzn.to汎用抽出に落ちないようにする）
        return results

    # パターン6: 七瀬アリーサ — amzn.toリンクから書籍タイトルを抽出
    # 形式A: 「タイトル　https://amzn.to/xxx」(同一行)
    # 形式B: 「タイトル」+ 次行「https://amzn.to/xxx」(別行)
    amazon_lines = re.findall(r'https?://amzn\.to/[A-Za-z0-9]+', summary)
    if amazon_lines:
        lines = summary.split('\n')
        ng_words = ['Amazon', 'URL', 'リンク', '七瀬', '商品紹介', '特典',
                    'メッセージカード', 'Success Book', '動画', '概要欄',
                    'おすすめ順ではない', 'アソシエイト', '購入ページ',
                    '提供:', 'Mainichi Eikaiwa', '評判', 'おすすめ本', '出演本',
                    '参考本', 'お勧め本', 'TOEIC', '勉強本', 'オーディブル',
                    'Audible', 'Kindle', 'Udemy', '手帳', 'プランナー',
                    'オンライン英会話', 'AQUES', 'チャンネル登録', 'LOWYAの',
                    'Meta Quest', 'Kindle端末', '本棚デスク', 'はこちら',
                    'タイマー', 'トレーナー', 'ボードゲーム', 'かっさ',
                    'テラヘルツ', 'イヤホン', 'キーボード', 'マウス',
                    'ディスプレイ', 'モニター', 'チェア', 'ライト付き',
                    '金フレ', 'キクタン', 'でる1000問', '公式問題集',
                    '精選問題集', '精選模試']

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            amazon_match = re.search(r'https?://amzn\.to/[A-Za-z0-9]+', line_stripped)
            if not amazon_match:
                continue

            title_candidate = None
            amazon_url = amazon_match.group(0)

            # 形式A: amzn.toの前にテキストがある（同一行）
            before_url = line_stripped[:amazon_match.start()].strip()
            if before_url and not before_url.startswith('http'):
                title_candidate = before_url
            # 形式B: amzn.toだけの行 → 前の行がタイトル（著者・出版社行はスキップ）
            elif line_stripped == amazon_url and i > 0:
                for j in range(i-1, max(i-5, -1), -1):
                    prev_line = lines[j].strip()
                    if not prev_line or prev_line.startswith('http'):
                        break
                    # 著者・出版社などのメタデータ行はスキップ（空白入りも対応: 「著　者」「監　訳」）
                    if re.match(r'^(著[\s　]*者|監[\s　]*訳|出版社|出版|発行|発売日|価格|定価)[\s\u200f\u200e]*[：:.\s　]', prev_line):
                        continue
                    # 括弧だけの補足行はスキップ（例: 「(日本語版)」「（完全版）」）
                    if re.match(r'^[（(].+[）)]$', prev_line):
                        continue
                    # 著者行をスキップ（例: 「エミン・ユルマズ (著)」）
                    if re.search(r'[（(]著[）)]', prev_line) and '『' not in prev_line and '「' not in prev_line:
                        continue
                    title_candidate = prev_line
                    break

            if not title_candidate:
                continue

            # NGワードチェック
            if any(ng in title_candidate for ng in ng_words):
                continue

            # クリーンアップ
            cleaned = re.sub(r'^[*\s・※❤️📕📗📘📙🔽▽↓]+', '', title_candidate).strip()
            # 括弧付きの補足を除去: 「タイトル(Amazon)」→「タイトル」
            cleaned = re.sub(r'[（(](?:Amazon|Amazonリンク|アマゾン)[）)]$', '', cleaned).strip()
            # 『』「」で囲まれている場合は外す
            if cleaned.startswith('『') and cleaned.endswith('』'):
                cleaned = cleaned[1:-1]
            if cleaned.startswith('「') and cleaned.endswith('」'):
                cleaned = cleaned[1:-1]

            if cleaned and len(cleaned) > 2:
                results.append({
                    "title": cleaned,
                    "author": None,
                    "publisher": None,
                })

        if results:
            return results

    # パターン5: アバタロー「書籍の購入」セクション
    abataro_section = re.search(
        r'(?:【書籍の購入】|▼書籍の購入)\s*\n?(.*?)(?=\n▼|\n\n\n|\Z)', summary, re.DOTALL
    )
    if abataro_section:
        section_text = abataro_section.group(1)
        lines = section_text.strip().split('\n')
        seen_titles = set()
        is_first = True
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # 非書籍行をスキップ
            if not line or line.startswith('http') or 'エッセンシャル版' in line or '簡易版' in line:
                i += 1
                continue
            # セクションヘッダー・サービス宣伝・ハッシュタグ・絵文字付き動画タイトルをスキップ
            if (line.startswith('【') or line.startswith('#') or
                'Audible' in line or 'Kindle' in line or 'amzn.to' in line or
                line.startswith('📗') or line.startswith('📕') or
                '本を聴く' in line or '関連動画' in line or
                '分解説' in line or 'チャンネル登録' in line or
                'SNS' in line or 'Twitter' in line or 'Instagram' in line or
                'OUTPUT読書術' in line):
                i += 1
                continue
            line = re.sub(r'^・\s*', '', line)
            book_match = re.match(r'(.+?)(?:[｜|](.+?))?(?:[（(](.+?)[）)])?$', line)
            if book_match:
                title = book_match.group(1).strip()
                author = book_match.group(2).strip() if book_match.group(2) else None
                publisher = book_match.group(3).strip() if book_match.group(3) else None
                if title not in seen_titles:
                    seen_titles.add(title)
                    results.append({
                        "title": title,
                        "author": author,
                        "publisher": publisher,
                        "_is_first": is_first,
                    })
                is_first = False
            i += 1
        if results:
            return results

    return results


def clean_book_title(title):
    """タイトルから著者名・出版社などの付加情報を除去"""
    if not title:
        return title
    title = title.strip()

    # 先頭の絵文字・記号・丸数字を除去（📚📗▶︎◉①②等）
    # U+FE0E/U+FE0F (variation selector) も含めて除去
    title = re.sub(r'^[📚📗📕📘📙📖🔽▶▷◉◎○●■□▪▫★☆✅✓→►➤🔶🔷💡🎯📌①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳\ufe0e\ufe0f]+[\s　.）)、]*', '', title)

    # 「書籍：」「著書：」等のプレフィックスを除去
    title = re.sub(r'^(書籍|著書)[：:]\s*', '', title)

    # 『タイトル』＋後続テキスト → 『』内だけ抽出
    m = re.search(r'『(.+?)』', title)
    if m:
        inner = m.group(1).strip()
        before = title[:m.start()].strip()
        after = title[m.end():].strip()
        if before:
            return inner
        if after:
            return inner

    # 「タイトル」＋後続テキスト → 「」内だけ抽出
    m = re.search(r'「(.+?)」', title)
    if m:
        inner = m.group(1).strip()
        before = title[:m.start()].strip()
        after = title[m.end():].strip()
        # 前に「著書」「著者」等、後ろに▷や(著)等がある場合
        if re.match(r'^(著書|著者)', before) or (after and re.match(r'[▷▶→(（]', after)):
            return inner

    # 末尾の「（著者名著）」「(著者名著)」を除去
    title = re.sub(r'[（(].+?著[）)]\s*$', '', title).strip()

    # 末尾の「（出版社名）」と後続の著者名等を除去（文庫・新書・選書など）
    title = re.sub(r'[（(](幻冬舎文庫|新潮新書|講談社文庫|角川文庫|文春文庫|集英社文庫|PHP新書|中公新書|岩波新書|ちくま新書|光文社新書|朝日新書|SB新書|祥伝社新書|講談社現代新書|講談社\+α新書|ハヤカワ文庫|創元推理文庫|PHP文庫|だいわ文庫|知的生きかた文庫|三笠書房)[）)].*$', '', title).strip()

    # 「渡邉正裕 著『タイトル』」パターン
    m = re.match(r'.+?\s+著\s*『(.+?)』', title)
    if m:
        return m.group(1).strip()

    return title


def is_valid_book_title(title):
    """書籍タイトルとして有効かどうかを判定"""
    if not title or not isinstance(title, str):
        return False

    title = title.strip()

    # 短すぎるタイトルを除外（3文字以下）
    if len(title) <= 3:
        return False

    # 絵文字で始まるものを除外
    emoji_starts = ['📚', '📗', '📕', '📘', '📙', '▼', '【', '■', '●', '◉', '◎', '○', '・', '※']
    if any(title.startswith(emoji) for emoji in emoji_starts):
        return False

    # NGワード（セクションヘッダーや宣伝）を除外
    ng_words = [
        'その他',
        'おすすめ動画',
        'チャンネル登録',
        '関連動画',
        '動画一覧',
        'SNS',
        'Twitter',
        'Instagram',
        'LINE',
        'エッセンシャル版',
        '簡易版',
        'Audible',
        'Kindle',
        '本を聴く',
        '分解説',
        '要約',
        '解説',
        'まとめ',
        'プレゼント',
        'キャンペーン',
        '無料',
        'プロフィール',
        'お問い合わせ',
        'メンバーシップ',
        'サブチャンネル',
        # 七瀬アリーサ関連の宣伝を除外
        '七瀬制作',
        '商品紹介',
        'メッセージカード',
        'Success Book',
        'Your Success',
        '購入ページ',
        '特典',
        'おすすめ順ではない',
        '概要欄',
        'デジタル版',
        '冊子版',
        # YouTuber自著の宣伝を除外
        'OUTPUT読書術',
        '週刊SPA',
        '人生を変える 哲学者の言葉366',
        '瞬間英作文',
        # 化粧品・美容用品を除外
        'Etude House BB cream',
        'Biooil',
        'Biore Sunscreen',
        "Visse's stick concealer",
        'Blush, eyeshadow pallet',
        "Visse's powder foundation",
        'Eyeblow powder',
        "Eyebrow's mascara",
        'lip balm',
        "Visse's powder blush",
        'IVY lip stick PK-300',
        'Hair Spray',
        'Panasonic 32mm hair iron ionity',
        'Find out more about Star Wars',
        # その他商品を除外
        'フィーバーヒューティー',
        'コーヒー豆（成城石井の）',
        'シリカ水レジーナ',
        'ぺんてる',
        'ヨガマット',
        'シリカ',
        'VOX',
        'コーヒーメーカー',
        # 食品・日用品を除外
        '白丸とんこつ豆腐スープ',
        'ベジ玄米ラーメン（しお）',
        '国産こんにゃくラーメン（25パック入り）',
        '大豆麺（細麺3人前）',
        '河村通夫の大自然ラーメン',
        'ボタニカル除菌消臭ミスト(無香料)',
        'イオン消臭プラス　特大サイズ1.5kg（無香料）',
        'ゆず油　無添加ヘアオイル60mL',
        'UVイデアプロテクショントーンアップ',
        'オーガニック・フェアトレード・カフェインレス・インスタントコーヒー',
        '有機クコの実100g',
        'めぐりズム・蒸気でホットアイマスク',
        'スマイルザメディカルA・DX',
        'ぶどう山椒石臼挽き粉末12g',
        'ぶどう山椒粒15g',
        '国産プーアル茶・ティーバッグ2g×25包',
        'アンドグッドナイト薬用入浴剤',
        'デオドラントソープ80g',
        'ビューステージ・UVプロテクト・プレミアム',
        '無添加・焼肉のたれ',
        'ウィルキンソン「タンサンラベルレスボトル500ml×24本」',
        'カフェインレス有機ほうじ茶15P',
        'オルナ オーガニック シャンプー',
        'パキスタン産ヒマラヤ岩塩「ダークピンク」',
        '純りんご酢',
        'クイックルワイパー',
        'ビオスリーHi錠',
        'ミヤリサン錠',
        'べっぴんはとむぎスナックタイプ',
        '国産よもぎ粉末',
        'オーガニック・エキストラバージン・オリーブオイル',
        'ザプログラスフェッドプロテイン1Kgプレーン',
        'マウントハーゲンオーガニックフェアトレードインスタントコーヒー',
        '国産ひきわり納豆',
        '有機栽培・国産手作りグァバ茶',
        '低分子コラーゲン',
        'ゼラチン',
        'Lamicall（ラミコール）のスマホホルダー',
        'Tapo スマートプラグ',
        '象印の炎舞炊き ＮＸ‐ＡＡ１０',
        'グレゴリー スケッチ Sketch 30',
        'Apple AirPods Pro 3',
        '[Horus X] ゲーミンググラス',
        'ブルーライト 99.9% カット pcメガネ',
        'ERGOTRON エルゴトロン ノートブックトレー',
        'フェイク観葉植物似たやつ',
        'Mainichi Eikaiwa',
        'つばめのノート',
        'ザレトリック',
        '季節の珈琲（春が見つからない..)',
        '鍋(ティ●ールより安いし可愛い）',
        'チョーヤの梅酒',
    ]

    for ng in ng_words:
        if ng in title:
            return False

    # 「本」だけのタイトルを除外
    if title in ['本', '書籍', '図書', 'book', 'books']:
        return False

    # 「〇本セット」のような商品表記を除外
    if re.search(r'\d+(本|冊)セット', title):
        return False

    # 容量表記を含む商品を除外（例: 145g、250ml、1.5kg）
    if re.search(r'\d+(\.\d+)?\s*(g|kg|ml|mL|L)\b', title, re.IGNORECASE):
        return False

    # 価格/容量表記を除外（例: 円/g）
    if re.search(r'円/(g|kg|ml|mL|L)\b', title, re.IGNORECASE):
        return False

    # 著者名パターンを除外: 「〇〇(著)」「〇〇（著）」「〇〇さま」のみの行
    if re.search(r'[（(]著[）)]', title) and '『' not in title and '「' not in title:
        return False
    if re.match(r'^[\w\s・　]+さま[\s　]*$', title):
        return False

    # メタデータ行を除外: 「著者：〇〇」「出版社：〇〇」「出版社　〇〇」「著　者」「編集　〇〇」
    if re.match(r'^(著[\s　]*者|出版社|出版|発行|書籍|編集|翻訳|監修)[\s\u200f\u200e]*[：:.　\s]', title):
        return False
    # 「〇〇 (編集)」「〇〇 (編著)」「〇〇 (翻訳)」パターンを除外
    if re.search(r'[（(](編集|編著|監修|翻訳)[）)][\s]*$', title):
        return False

    # 著作権・許諾表記を除外
    if re.search(r'(許諾を得て|配信しております|提供でお送り|タイアップ)', title):
        return False
    # 説明文・案内文を除外
    if title.startswith('本動画は'):
        return False
    if re.search(r'(アマゾンで購入|Amazonで購入|購入できます|購入はこちら)', title):
        return False


    # URLっぽいものを除外
    if 'http' in title.lower() or '.com' in title.lower():
        return False

    # 全て記号のタイトルを除外
    if all(not c.isalnum() for c in title):
        return False

    # YouTuber名が入っているものを除外（自著宣伝の可能性）
    youtuber_names = ['アバタロー', 'サラタメ', '本要約チャンネル', '学識サロン', 'フェルミ', '三宅', '七瀬', 'アリーサ']
    for name in youtuber_names:
        if name in title:
            return False

    return True


def normalize_title_key(title):
    """表記揺れ統一用の正規化キーを生成"""
    t = title
    t = re.sub(r'[『』「」]', '', t)
    t = re.sub(r'[（(](単行本|文庫|新書|ハードカバー|Kindle版)[）)]', '', t)
    t = re.sub(r'^(改訂版|新版|新装版|増補版|決定版|完全版)\s*', '', t)
    t = re.sub(r'(改訂版です|改訂版)$', '', t)
    t = re.sub(r'[\s　、,：:]+', '', t)
    t = t.lower()
    return t


def merge_similar_books(all_books):
    """短いキーが長いキーの先頭に含まれる場合、同一書籍として統合"""
    keys = sorted(all_books.keys(), key=len)
    merge_map = {}  # short_key -> long_key (統合先)
    for i, short_key in enumerate(keys):
        if short_key in merge_map or len(short_key) < 5:
            continue
        for long_key in keys[i+1:]:
            if long_key in merge_map:
                continue
            if long_key.startswith(short_key):
                merge_map[short_key] = long_key
                break  # 最短の統合先に統合

    for src_key, dst_key in merge_map.items():
        src = all_books.pop(src_key, None)
        if not src or dst_key not in all_books:
            continue
        dst = all_books[dst_key]
        dst["count"] += src["count"]
        dst["total_views"] += src["total_views"]
        dst["total_likes"] += src["total_likes"]
        dst["videos"].extend(src["videos"])
        dst["_title_variants"].extend(src.get("_title_variants", [src["title"]]))
        if not dst.get("author") and src.get("author"):
            dst["author"] = src["author"]
        if not dst.get("publisher") and src.get("publisher"):
            dst["publisher"] = src["publisher"]


def choose_canonical_title(titles):
    """複数の表記揺れタイトルから最も正式なタイトルを選択"""
    cleaned = [re.sub(r'\s*[（(](単行本|文庫|新書|ハードカバー|Kindle版)[）)]', '', t) for t in titles]
    with_subtitle = [t for t in cleaned if '：' in t or ':' in t or '―' in t or '—' in t]
    candidates = with_subtitle if with_subtitle else cleaned
    return max(candidates, key=len)


def generate_amazon_search_url(book_title):
    """書籍タイトルからAmazon検索URLを生成（アソシエイトタグ付き）"""
    query = urllib.parse.quote(book_title)
    return f"https://www.amazon.co.jp/s?k={query}&i=stripbooks&tag={AMAZON_TRACKING_ID}"


def generate_book_id(title):
    """書籍タイトルからユニークIDを生成"""
    return hashlib.md5(title.encode()).hexdigest()[:12]


# =============================================================================
# メイン処理
# =============================================================================

def load_channels():
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["channels"]


def main():
    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY が設定されていません。.env または環境変数で設定してください。")
        sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)
    channels = load_channels()
    all_books = {}

    for ch in channels:
        channel_name = ch["name"]
        channel_id = ch["channel_id"]
        print(f"\n=== {channel_name} (ID: {channel_id}) ===")

        videos = fetch_all_channel_videos(channel_id)

        for video in videos:
            summary = video.get("summary", "")
            video_title = video.get("title", "")
            book_info_list = extract_book_info_list(summary, video_title)

            if not book_info_list:
                continue

            for book_info in book_info_list:
                book_title = book_info.get("title")
                if not book_title:
                    continue

                # タイトルクリーンアップ（著者名・出版社を分離）
                book_title = clean_book_title(book_title)
                book_info["title"] = book_title

                # タイトルの妥当性チェック
                if not is_valid_book_title(book_title):
                    continue

                # 自著宣伝スキップ
                if book_info.get("_is_first") and len(book_info_list) > 1:
                    continue

                # Amazonリンクから取得した場合は既にamazon_urlが設定されている
                amazon_url = book_info.get("amazon_url") or generate_amazon_search_url(book_title)

                # 表記揺れ統一: 正規化キーで同一書籍をグループ化
                norm_key = normalize_title_key(book_title)

                if norm_key not in all_books:
                    all_books[norm_key] = {
                        "id": generate_book_id(norm_key),
                        "title": book_title,
                        "_title_variants": [book_title],
                        "author": book_info.get("author"),
                        "publisher": book_info.get("publisher"),
                        "amazon_url": amazon_url,
                        "count": 0,
                        "total_views": 0,
                        "total_likes": 0,
                        "videos": [],
                    }
                else:
                    # 新しいバリエーションを記録
                    if book_title not in all_books[norm_key]["_title_variants"]:
                        all_books[norm_key]["_title_variants"].append(book_title)
                    # 著者・出版社が未設定なら補完
                    if not all_books[norm_key]["author"] and book_info.get("author"):
                        all_books[norm_key]["author"] = book_info["author"]
                    if not all_books[norm_key]["publisher"] and book_info.get("publisher"):
                        all_books[norm_key]["publisher"] = book_info["publisher"]

                all_books[norm_key]["count"] += 1
                all_books[norm_key]["total_views"] += video.get("view_count", 0)
                all_books[norm_key]["total_likes"] += video.get("like_count", 0)
                all_books[norm_key]["videos"].append({
                    "video_id": video["video_id"],
                    "video_title": video["title"],
                    "channel": channel_name,
                    "link": video["link"],
                    "published": video["published"],
                    "view_count": video.get("view_count", 0),
                    "like_count": video.get("like_count", 0),
                })

    # --- 表記揺れ統一 ---
    # 1. 短いキーが長いキーに含まれる場合を統合
    merge_similar_books(all_books)
    # 2. 各グループから正規タイトルを選択
    for book in all_books.values():
        variants = book.pop("_title_variants", [book["title"]])
        if len(variants) > 1:
            canonical = choose_canonical_title(variants)
            book["title"] = canonical
            book["amazon_url"] = generate_amazon_search_url(canonical)

    # --- 結果表示 ---
    books_list = list(all_books.values())
    print(f"\n=== 抽出結果 ===")
    print(f"書籍数: {len(books_list)}")

    # --- 既存データとのマージ（ISBN等を保持） ---
    books_file = os.path.join(DATA_DIR, "books.json")
    if os.path.exists(books_file):
        with open(books_file, "r", encoding="utf-8") as f:
            existing_books = json.load(f)
        # idでマップ化
        existing_map = {b["id"]: b for b in existing_books}
        # タイトル正規化キーでもマップ化（IDが変わった場合に対応）
        existing_by_title = {normalize_title_key(b["title"]): b for b in existing_books}
        # 新データに既存のISBN/ASIN/image_url等をマージ
        for book in books_list:
            # IDでマッチ、またはタイトル正規化キーでマッチ
            existing = existing_map.get(book["id"])
            if not existing:
                norm_key = normalize_title_key(book["title"])
                existing = existing_by_title.get(norm_key)
            if existing:
                for key in ["isbn", "asin", "image_url", "publication_date", "openbd_title"]:
                    if existing.get(key) and not book.get(key):
                        book[key] = existing[key]
                # amazon_urlはASIN付きのものを優先
                if existing.get("asin") and "/dp/" in existing.get("amazon_url", ""):
                    book["amazon_url"] = existing["amazon_url"]
                    book["asin"] = existing["asin"]

    # --- JSON生成 ---

    # books.json（紹介回数順）
    books_by_count = sorted(books_list, key=lambda x: x["count"], reverse=True)
    with open(books_file, "w", encoding="utf-8") as f:
        json.dump(books_by_count, f, ensure_ascii=False, indent=2)

    # ランキング用の軽量データを生成する関数
    def make_ranking_entry(book):
        return {
            "id": book["id"],
            "title": book["title"],
            "author": book.get("author"),
            "count": book["count"],
            "total_views": book["total_views"],
            "total_likes": book["total_likes"],
            "amazon_url": book["amazon_url"],
        }

    # rankings.json（紹介回数順）
    rankings_count = [make_ranking_entry(b) for b in books_by_count]
    with open(os.path.join(DATA_DIR, "rankings.json"), "w", encoding="utf-8") as f:
        json.dump(rankings_count, f, ensure_ascii=False, indent=2)

    # rankings_views.json（再生回数合計順）
    books_by_views = sorted(books_list, key=lambda x: x["total_views"], reverse=True)
    rankings_views = [make_ranking_entry(b) for b in books_by_views]
    with open(os.path.join(DATA_DIR, "rankings_views.json"), "w", encoding="utf-8") as f:
        json.dump(rankings_views, f, ensure_ascii=False, indent=2)

    # rankings_likes.json（いいね合計順）
    books_by_likes = sorted(books_list, key=lambda x: x["total_likes"], reverse=True)
    rankings_likes = [make_ranking_entry(b) for b in books_by_likes]
    with open(os.path.join(DATA_DIR, "rankings_likes.json"), "w", encoding="utf-8") as f:
        json.dump(rankings_likes, f, ensure_ascii=False, indent=2)

    print(f"\n--- TOP20（紹介回数順）---")
    for i, book in enumerate(books_by_count[:20], 1):
        print(f"  {i}. 『{book['title']}』 (紹介{book['count']}回 / 再生{book['total_views']:,} / いいね{book['total_likes']:,})")

    print(f"\n--- TOP10（再生回数順）---")
    for i, book in enumerate(books_by_views[:10], 1):
        print(f"  {i}. 『{book['title']}』 (再生{book['total_views']:,} / 紹介{book['count']}回)")

    print(f"\n--- TOP10（いいね順）---")
    for i, book in enumerate(books_by_likes[:10], 1):
        print(f"  {i}. 『{book['title']}』 (いいね{book['total_likes']:,} / 紹介{book['count']}回)")

    print(f"\nデータを {DATA_DIR} に保存しました。")


if __name__ == "__main__":
    main()
