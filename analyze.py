"""
Daily stock analysis + LINE & Gmail notification
"""

import os
import json
import requests
import anthropic
from datetime import datetime, date
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─────────────────────────
# Holdings (loaded from stocks.json)
# ─────────────────────────

def load_stocks():
    with open("stocks.json", "r") as f:
        data = json.load(f)
    return data["us"], [tuple(s) for s in data["tw"]]

US_STOCKS, TW_STOCKS = load_stocks()

# ─────────────────────────
# US stock data (Yahoo Finance)
# ─────────────────────────

def get_us_stock_data(symbols):
    results = {}
    for sym in symbols:
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/" + sym + "?interval=1d&range=2d"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            meta = data["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice", 0)
            prev = meta.get("chartPreviousClose", price)
            change_pct = ((price - prev) / prev * 100) if prev else 0
            results[sym] = {
                "price": round(price, 2),
                "change_pct": round(change_pct, 2),
                "currency": "USD"
            }
        except Exception as e:
            results[sym] = {"price": None, "change_pct": None, "error": str(e)}
    return results

# ─────────────────────────
# TW stock data (TWSE)
# ─────────────────────────

def get_tw_stock_data(stocks):
    results = {}
    today = date.today().strftime("%Y%m%d")
    for code, name in stocks:
        try:
            url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date=" + today + "&stockNo=" + code
            r = requests.get(url, timeout=10)
            data = r.json()
            if data.get("stat") == "OK" and data.get("data"):
                last_row = data["data"][-1]
                close = float(last_row[6].replace(",", ""))
                open_ = float(last_row[3].replace(",", ""))
                change_pct = ((close - open_) / open_ * 100) if open_ else 0
                results[code] = {
                    "name": name,
                    "price": round(close, 2),
                    "change_pct": round(change_pct, 2),
                    "currency": "TWD"
                }
            else:
                results[code] = {"name": name, "price": None, "change_pct": None}
        except Exception as e:
            results[code] = {"name": name, "price": None, "change_pct": None, "error": str(e)}
    return results

# ─────────────────────────
# Market indices
# ─────────────────────────

def get_market_indices():
    indices = {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ",
        "^DJI": "DOW",
        "^TWII": "TAIEX",
    }
    results = {}
    for symbol, name in indices.items():
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/" + symbol + "?interval=1d&range=2d"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            meta = data["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice", 0)
            prev = meta.get("chartPreviousClose", price)
            change_pct = ((price - prev) / prev * 100) if prev else 0
            results[name] = {
                "price": round(price, 2),
                "change_pct": round(change_pct, 2)
            }
        except Exception:
            results[name] = {"price": None, "change_pct": None}
    return results

# ─────────────────────────
# Tarot
# ─────────────────────────

TAROT_CARDS = [
    ("The Fool",           "愚者"),
    ("The Magician",       "魔術師"),
    ("The High Priestess", "女祭司"),
    ("The Empress",        "皇后"),
    ("The Emperor",        "皇帝"),
    ("The Hierophant",     "教皇"),
    ("The Lovers",         "戀人"),
    ("The Chariot",        "戰車"),
    ("Strength",           "力量"),
    ("The Hermit",         "隱士"),
    ("Wheel of Fortune",   "命運之輪"),
    ("Justice",            "正義"),
    ("The Hanged Man",     "倒吊人"),
    ("Death",              "死神"),
    ("Temperance",         "節制"),
    ("The Devil",          "惡魔"),
    ("The Tower",          "高塔"),
    ("The Star",           "星星"),
    ("The Moon",           "月亮"),
    ("The Sun",            "太陽"),
    ("Judgement",          "審判"),
    ("The World",          "世界"),
]

def draw_daily_tarot():
    """每日大盤塔羅（固定 seed，50/50 正逆位）"""
    seed = int(date.today().strftime("%Y%m%d"))
    random.seed(seed)
    card = random.choice(TAROT_CARDS)
    is_reversed = random.random() < 0.5
    orientation = "【逆位】" if is_reversed else "【正位】"
    return card[0], card[1], orientation

def draw_tarot_per_stock(symbol):
    """每支個股各自抽牌，seed = 日期+代號，50/50 正逆位"""
    seed_str = date.today().strftime("%Y%m%d") + symbol
    seed = sum(ord(c) for c in seed_str)
    rng = random.Random(seed)
    card = rng.choice(TAROT_CARDS)
    is_reversed = rng.random() < 0.5
    orientation = "逆位" if is_reversed else "正位"
    return card[0], card[1], orientation, is_reversed

# ─────────────────────────
# Claude analysis — 精簡版（broadcast 用）
# ─────────────────────────

def analyze_with_claude_lite(us_data, tw_data, indices, tarot_name, tarot_zh, orientation):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today_str = datetime.now().strftime("%Y/%m/%d")
    prompt = (
        "你是資深台股分析師。今天是 " + today_str + "。\n"
        "用繁體中文寫一份簡短的盤後快報，給一般投資人看，不需要個股細節。\n\n"
        "格式如下：\n\n"
        "📊 大盤現況\n"
        "（2-3行，今日市場整體氣氛與走勢）\n\n"
        "📰 重要財經新聞預警\n"
        "（近期2-3個會影響市場的重要事件或數據）\n\n"
        "⚙️ 今日市場主要驅動力\n"
        "（2-3個關鍵因素）\n\n"
        "🔑 三大重點\n"
        "1. \n2. \n3. \n\n"
        "🌡️ 今日情緒：（一個詞，例：偏多 / 震盪 / 偏空）\n\n"
        "🃏 今日塔羅：" + tarot_name + " " + tarot_zh + " " + orientation + "\n"
        "（1行塔羅與大盤結合的解讀）\n\n"
        "---\n"
        "大盤資料：\n" + json.dumps(indices, ensure_ascii=False) + "\n"
        "規則：簡潔、親切，不超過300字，不加免責聲明。"
    )
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# ─────────────────────────
# Claude analysis — 完整版（push 給我用）
# ─────────────────────────

def analyze_with_claude_full(us_data, tw_data, indices, tarot_name, tarot_zh, orientation, stock_tarots):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today_str = datetime.now().strftime("%Y/%m/%d")

    stock_tarot_lines = []
    for sym, (card_en, card_zh, ori, is_rev) in stock_tarots.items():
        price_info = us_data.get(sym) or next(
            (tw_data[c] for c in tw_data if tw_data[c].get("name") == sym), {}
        )
        pct = price_info.get("change_pct", "N/A")
        stock_tarot_lines.append(
            f"{sym} | {card_zh}({card_en}) {ori} | 當日漲跌:{pct}%"
        )
    stock_tarot_text = "\n".join(stock_tarot_lines)

    prompt = (
        "你是資深台股分析師兼塔羅解讀師。今天是 " + today_str + "。\n"
        "用繁體中文寫完整盤後分析報告，結合當日股市實際數據、國際時事與塔羅牌解讀。\n\n"
        "=== 格式 ===\n\n"
        "【大盤現況】\n"
        "（2-3行，今日市場整體氣氛與走勢）\n\n"
        "【重要財經新聞預警】\n"
        "（列出近期2-3個會影響持股的重要事件或數據）\n\n"
        "【今日市場主要驅動力】\n"
        "（2-3個關鍵因素）\n\n"
        "【個股塔羅解牌＋操作建議】\n"
        "針對以下每一支股票，根據當日漲跌、塔羅牌正逆位、國際時事，給出：\n"
        "- 塔羅解讀（正位強調機遇，逆位強調警示）\n"
        "- 明確操作建議：強烈買入 / 買入 / 持有 / 減碼 / 賣出\n"
        "格式：\n"
        "▸ [股票代號] [牌名] [正/逆位]\n"
        "  解讀：（1-2行）\n"
        "  建議：[操作] — [一句理由]\n\n"
        "【今日買賣優先清單】\n"
        "🔴 優先買入：（最多3支，附簡短理由）\n"
        "🟢 考慮減碼：（最多3支，附簡短理由）\n\n"
        "【風險提示】\n"
        "（針對持股集中度與當前市況的風險警示）\n\n"
        "【今日大盤塔羅】\n"
        "牌：" + tarot_name + " " + tarot_zh + " " + orientation + "\n"
        "（2行，結合今日大盤氣氛做整體解讀）\n\n"
        "=== 數據 ===\n"
        "大盤指數：\n" + json.dumps(indices, ensure_ascii=False) + "\n\n"
        "美股持倉：\n" + json.dumps(us_data, ensure_ascii=False) + "\n\n"
        "台股持倉：\n" + json.dumps(tw_data, ensure_ascii=False) + "\n\n"
        "個股塔羅牌（已抽好，請依此解牌）：\n" + stock_tarot_text + "\n\n"
        "規則：繁體中文、每行不超過40字、語氣親切專業、不加免責聲明。"
    )

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# ─────────────────────────
# HTML email builder
# ─────────────────────────

def build_html_email(analysis, indices, us_data, tw_data, tarot_name, tarot_zh, orientation, stock_tarots):
    today_str = datetime.now().strftime("%Y/%m/%d")

    def pct_color(pct):
        if pct is None: return "#888888"
        return "#e74c3c" if pct >= 0 else "#27ae60"

    def pct_str(pct):
        if pct is None: return "N/A"
        sign = "+" if pct >= 0 else ""
        return sign + str(round(pct, 2)) + "%"

    index_rows = ""
    for name, d in indices.items():
        color = pct_color(d.get("change_pct"))
        index_rows += f"<tr><td>{name}</td><td>{d.get('price','N/A')}</td><td style='color:{color};font-weight:bold'>{pct_str(d.get('change_pct'))}</td></tr>"

    us_rows = ""
    for sym, d in us_data.items():
        color = pct_color(d.get("change_pct"))
        card_en, card_zh, ori, is_rev = stock_tarots.get(sym, ("—", "—", "", False))
        ori_color = "#c0392b" if is_rev else "#8e44ad"
        us_rows += (
            f"<tr><td><b>{sym}</b></td><td>${d.get('price','N/A')}</td>"
            f"<td style='color:{color};font-weight:bold'>{pct_str(d.get('change_pct'))}</td>"
            f"<td>{card_zh} <span style='font-size:11px;color:{ori_color}'>{ori}</span></td></tr>"
        )

    tw_rows = ""
    for code, d in tw_data.items():
        color = pct_color(d.get("change_pct"))
        name = d.get("name", code)
        card_en, card_zh, ori, is_rev = stock_tarots.get(name, ("—", "—", "", False))
        ori_color = "#c0392b" if is_rev else "#8e44ad"
        tw_rows += (
            f"<tr><td><b>{name} ({code})</b></td><td>NT${d.get('price','N/A')}</td>"
            f"<td style='color:{color};font-weight:bold'>{pct_str(d.get('change_pct'))}</td>"
            f"<td>{card_zh} <span style='font-size:11px;color:{ori_color}'>{ori}</span></td></tr>"
        )

    analysis_html = analysis.replace("\n", "<br>")

    css = (
        "body{font-family:Arial,sans-serif;background:#f5f6fa;margin:0;padding:20px}"
        ".wrap{max-width:660px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08)}"
        ".hdr{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:24px 28px}"
        ".hdr h1{margin:0;font-size:22px}"
        ".hdr p{margin:4px 0 0;opacity:0.6;font-size:13px}"
        ".sec{padding:20px 28px;border-bottom:1px solid #f0f0f0}"
        ".sec h2{font-size:13px;color:#888;text-transform:uppercase;letter-spacing:1px;margin:0 0 12px}"
        "table{width:100%;border-collapse:collapse;font-size:14px}"
        "th{background:#f8f9fa;padding:8px 10px;text-align:left;color:#666;font-weight:600;font-size:12px}"
        "td{padding:8px 10px;border-bottom:1px solid #f5f5f5}"
        "tr:last-child td{border-bottom:none}"
        ".analysis{line-height:1.8;font-size:14px;color:#333;white-space:pre-wrap}"
        ".tarot{background:#f8f0ff;border-left:4px solid #9b59b6;padding:14px 18px;border-radius:0 8px 8px 0}"
        ".tname{font-size:18px;font-weight:bold;color:#9b59b6}"
        ".ftr{padding:16px 28px;text-align:center;font-size:12px;color:#aaa;background:#fafafa}"
    )

    html = (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{css}</style></head><body>"
        f"<div class='wrap'>"
        f"<div class='hdr'><h1>🌟 每日完整股市報告</h1><p>{today_str}（VIP 專屬版）</p></div>"
        f"<div class='sec'><h2>大盤指數</h2><table><tr><th>指數</th><th>點位</th><th>漲跌</th></tr>{index_rows}</table></div>"
        f"<div class='sec'><h2>美股持倉</h2><table><tr><th>代號</th><th>股價</th><th>漲跌</th><th>今日塔羅</th></tr>{us_rows}</table></div>"
        f"<div class='sec'><h2>台股持倉</h2><table><tr><th>股票</th><th>股價</th><th>漲跌</th><th>今日塔羅</th></tr>{tw_rows}</table></div>"
        f"<div class='sec'><h2>Claude 完整分析</h2><div class='analysis'>{analysis_html}</div></div>"
        f"<div class='sec'><h2>大盤塔羅</h2><div class='tarot'><div class='tname'>{tarot_name} {tarot_zh} {orientation}</div></div></div>"
        f"<div class='ftr'>Auto-generated by Claude AI · VIP Only</div>"
        f"</div></body></html>"
    )
    return html

# ─────────────────────────
# Send Gmail
# ─────────────────────────

def send_gmail(html_content, subject):
    sender = os.environ["GMAIL_SENDER"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ["GMAIL_RECIPIENT"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
    print("Gmail sent to " + recipient)

# ─────────────────────────
# Send LINE — broadcast 精簡版
# ─────────────────────────

def send_line_broadcast(message):
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }
    max_len = 4900
    chunks = [message[i:i + max_len] for i in range(0, len(message), max_len)]
    for chunk in chunks:
        r = requests.post(url, headers=headers, json={"messages": [{"type": "text", "text": chunk}]})
        print("LINE broadcast: " + str(r.status_code))

# ─────────────────────────
# Send LINE — push 完整版給我
# ─────────────────────────

def send_line_push_me(message):
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }
    max_len = 4900
    chunks = [message[i:i + max_len] for i in range(0, len(message), max_len)]
    for chunk in chunks:
        payload = {
            "to": user_id,
            "messages": [{"type": "text", "text": chunk}]
        }
        r = requests.post(url, headers=headers, json=payload)
        print("LINE push to me: " + str(r.status_code))

# ─────────────────────────
# Main
# ─────────────────────────

def main():
    print("Starting daily analysis…")
    today_str = datetime.now().strftime("%m/%d")

    print("Fetching indices...")
    indices = get_market_indices()

    print("Fetching US stocks...")
    us_data = get_us_stock_data(US_STOCKS)

    print("Fetching TW stocks...")
    tw_data = get_tw_stock_data(TW_STOCKS)

    print("Drawing daily tarot...")
    tarot_name, tarot_zh, orientation = draw_daily_tarot()
    print(f"Daily tarot: {tarot_name} {orientation}")

    print("Drawing per-stock tarots...")
    stock_tarots = {}
    for sym in US_STOCKS:
        stock_tarots[sym] = draw_tarot_per_stock(sym)
    for code, name in TW_STOCKS:
        stock_tarots[name] = draw_tarot_per_stock(name)

    print("Analyzing lite version...")
    lite_analysis = analyze_with_claude_lite(us_data, tw_data, indices, tarot_name, tarot_zh, orientation)

    print("Analyzing full version...")
    full_analysis = analyze_with_claude_full(us_data, tw_data, indices, tarot_name, tarot_zh, orientation, stock_tarots)

    print("Sending Gmail...")
    subject = f"🌟 每日完整股市報告 {today_str}"
    html = build_html_email(full_analysis, indices, us_data, tw_data, tarot_name, tarot_zh, orientation, stock_tarots)
    send_gmail(html, subject)

    print("Sending LINE broadcast (lite)...")
    lite_message = f"📊 每日股市快報 {today_str}\n{'='*20}\n{lite_analysis}"
    send_line_broadcast(lite_message)

    print("Sending LINE push to me (full)...")
    full_message = f"🌟 完整報告 {today_str}\n{'='*20}\n{full_analysis}"
    send_line_push_me(full_message)

    print("Done!")

if __name__ == "__main__":
    main()
