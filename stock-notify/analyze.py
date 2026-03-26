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

# –––––––––––––––––––––––––
# Holdings
# –––––––––––––––––––––––––

US_STOCKS = [
"APLD", "ASML", "MRVL", "RXRX", "TSLA", "NVDA",
"GOOGL", "CRWV", "AMD", "NEE", "VST", "MU",
"VRT", "MP", "AVGO", "PANW", "AMZN"
]

TW_STOCKS = [
("2330", "TSMC"),
("2404", "HanTang"),
("2812", "TaichungBank"),
("2834", "TaiwanBiz"),
("2845", "FarEastBank"),
("3293", "IGS"),
]

# –––––––––––––––––––––––––
# US stock data (Yahoo Finance)
# –––––––––––––––––––––––––

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

# –––––––––––––––––––––––––
# TW stock data (TWSE)
# –––––––––––––––––––––––––

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

# –––––––––––––––––––––––––
# Market indices
# –––––––––––––––––––––––––

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

# –––––––––––––––––––––––––
# Tarot
# –––––––––––––––––––––––––

TAROT_CARDS = [
("The Fool", "New beginning, stay open, don’t over-calculate risk"),
("The Magician", "Resources ready, good time to act"),
("The High Priestess", "Wait and watch, avoid impulsive trades"),
("The Empress", "Harvest ahead, hold positions"),
("The Emperor", "Stay steady, manage position risk"),
("The Hierophant", "Follow discipline, don’t fight the trend"),
("The Lovers", "Need to choose, diversify risk"),
("The Chariot", "Strong breakout, consider adding"),
("Strength", "Be patient, market will reward"),
("The Hermit", "Think independently, don’t chase highs"),
("Wheel of Fortune", "Rotation in play, watch for sector shifts"),
("Justice", "Back to fundamentals, rational assessment"),
("The Hanged Man", "Pause, re-examine your strategy"),
("Death", "End of cycle, consider cutting losses"),
("Temperance", "Balance your portfolio, avoid concentration"),
("The Devil", "Greed warning, beware of chasing highs"),
("The Tower", "Sudden change, manage your risk"),
("The Star", "Long-term hope, buy the dip"),
("The Moon", "Market fog, cautious amid uncertainty"),
("The Sun", "Optimism rising, but don’t forget to take profit"),
("Judgement", "Re-evaluate your portfolio"),
("The World", "Cycle complete, time to consider profits"),
]

def draw_tarot():
    seed = int(date.today().strftime("%Y%m%d"))
    random.seed(seed)
    card = random.choice(TAROT_CARDS)
    return card[0], card[1]

# –––––––––––––––––––––––––
# Claude analysis
# –––––––––––––––––––––––––

def analyze_with_claude(us_data, tw_data, indices, tarot_name, tarot_meaning):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today_str = datetime.now().strftime("%Y/%m/%d")

    '''
    prompt = (
        ...
    )
    message = client.messages.create(
        ...
    )
    return message.content[0].text
    '''

# –––––––––––––––––––––––––
# HTML email builder
# –––––––––––––––––––––––––

def build_html_email(analysis, indices, us_data, tw_data, tarot_name, tarot_meaning):
    today_str = datetime.now().strftime("%Y/%m/%d")

    '''
    ...
    return html
    '''

# –––––––––––––––––––––––––
# Send Gmail
# –––––––––––––––––––––––––

def send_gmail(html_content, subject):
    sender = os.environ["GMAIL_SENDER"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ["GMAIL_RECIPIENT"]

    '''
    ...
    '''

# –––––––––––––––––––––––––
# Send LINE
# –––––––––––––––––––––––––

def send_line_message(message):
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
        print("LINE response: " + str(r.status_code))

# –––––––––––––––––––––––––
# Main
# –––––––––––––––––––––––––

def main():
    print("Starting daily analysis…")

    #'''
    print("Fetching indices...")
    indices = get_market_indices()

    print("Fetching US stocks...")
    us_data = get_us_stock_data(US_STOCKS)

    print("Fetching TW stocks...")
    tw_data = get_tw_stock_data(TW_STOCKS)

    print("Drawing tarot...")
    tarot_name, tarot_meaning = draw_tarot()
    print("Tarot: " + tarot_name)

    print("Analyzing with Claude...")
    analysis = analyze_with_claude(us_data, tw_data, indices, tarot_name, tarot_meaning)

    today_str = datetime.now().strftime("%m/%d")
    full_message = "Daily Report " + today_str + "\n" + "=" * 20 + "\n" + analysis

    print("Sending Gmail...")
    subject = "Daily Market Report " + today_str
    #html = build_html_email(analysis, indices, us_data, tw_data, tarot_name, tarot_meaning)
    #send_gmail(html, subject)

    print("Sending LINE...")
    send_line_message(full_message)

    print("Done!")
    #'''

if __name__ == "__main__":
    main()
