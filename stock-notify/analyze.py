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

# Holdings

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
    ("3293", "IGS")
]

def get_us_stock_data(symbols):
    results = {}
    for sym in symbols:
        try:
            url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
                   + sym + "?interval=1d&range=2d")
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

def get_tw_stock_data(stocks):
    results = {}
    today = date.today().strftime("%Y%m%d")
    for code, name in stocks:
        try:
            url = ("https://www.twse.com.tw/exchangeReport/STOCK_DAY?"
                   + f"response=json&date={today}&stockNo={code}")
            r = requests.get(url, timeout=10)
            data = r.json()
            if data.get("stat") == "OK" and data.get("data"):
                last_row = data["data"][-1]
                close = float(last_row[6].replace(",", ""))
                open_ = float(last_row[3].replace(",", ""))
                change_pct = (((close - open_) / open_) * 100) if open_ else 0
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

def get_market_indices():
    indices = {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ",
        "^DJI": "DOW",
        "^TWII": "TAIEX"
    }
    results = {}
    for symbol, name in indices.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            meta = data["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice", 0)
            prev = meta.get("chartPreviousClose", price)
            change_pct = (((price - prev) / prev) * 100) if prev else 0
            results[name] = {
                "price": round(price, 2),
                "change_pct": round(change_pct, 2)
            }
        except Exception:
            results[name] = {"price": None, "change_pct": None}
    return results

TAROT_CARDS = [
    ("The Fool", "New beginning, stay open, don't over-calculate risk"),
    ("The Magician", "Resources ready, good time to act"),
    ("The High Priestess", "Wait and watch, avoid impulsive trades"),
    ("The Empress", "Harvest ahead, hold positions"),
    ("The Emperor", "Stay steady, manage position risk"),
    ("The Hierophant", "Follow discipline, don't fight the trend"),
    ("The Lovers", "Need to choose, diversify risk"),
    ("The Chariot", "Strong breakout, consider adding"),
    ("Strength", "Be patient, market will reward"),
    ("The Hermit", "Think independently, don't chase highs"),
    ("Wheel of Fortune", "Rotation in play, watch for sector shifts"),
    ("Justice", "Back to fundamentals, rational assessment"),
    ("The Hanged Man", "Pause, re-examine your strategy"),
    ("Death", "End of cycle, consider cutting losses"),
    ("Temperance", "Balance your portfolio, avoid concentration"),
    ("The Devil", "Greed warning, beware of chasing highs"),
    ("The Tower", "Sudden change, manage your risk"),
    ("The Star", "Long-term hope, buy the dip"),
    ("The Moon", "Market fog, cautious amid uncertainty"),
    ("The Sun", "Optimism rising, but don't forget to take profit"),
    ("Judgement", "Re-evaluate your portfolio"),
    ("The World", "Cycle complete, time to consider profits")
]

def draw_tarot():
    seed = int(date.today().strftime("%Y%m%d"))
    random.seed(seed)
    card = random.choice(TAROT_CARDS)
    return card[0], card[1]