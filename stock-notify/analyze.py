“””
每日股市分析 + LINE 推播
持股：美股 + 台股
時間：台灣時間 16:00（盤後）
“””

import os
import json
import requests
import anthropic
from datetime import datetime, date
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─────────────────────────────────────

# 持股設定

# ─────────────────────────────────────

US_STOCKS = [
“APLD”, “ASML”, “MRVL”, “RXRX”, “TSLA”, “NVDA”,
“GOOGL”, “CRWV”, “AMD”, “NEE”, “VST”, “MU”,
“VRT”, “MP”, “AVGO”, “PANW”, “AMZN”
]

TW_STOCKS = [
(“2330”, “台積電”),
(“2404”, “漢唐”),
(“2812”, “台中銀”),
(“2834”, “臺企銀”),
(“2845”, “遠東銀”),
(“3293”, “鈊象”),
]

# ─────────────────────────────────────

# 取得美股資料（Yahoo Finance 非官方）

# ─────────────────────────────────────

def get_us_stock_data(symbols: list[str]) -> dict:
results = {}
for sym in symbols:
try:
url = f”https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=2d”
headers = {“User-Agent”: “Mozilla/5.0”}
r = requests.get(url, headers=headers, timeout=10)
data = r.json()
meta = data[“chart”][“result”][0][“meta”]
price = meta.get(“regularMarketPrice”, 0)
prev  = meta.get(“chartPreviousClose”, price)
change_pct = ((price - prev) / prev * 100) if prev else 0
results[sym] = {
“price”: round(price, 2),
“change_pct”: round(change_pct, 2),
“currency”: “USD”
}
except Exception as e:
results[sym] = {“price”: None, “change_pct”: None, “error”: str(e)}
return results

# ─────────────────────────────────────

# 取得台股資料（TWSE 公開資料）

# ─────────────────────────────────────

def get_tw_stock_data(stocks: list[tuple]) -> dict:
results = {}
today = date.today().strftime(”%Y%m%d”)
for code, name in stocks:
try:
url = f”https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={today}&stockNo={code}”
r = requests.get(url, timeout=10)
data = r.json()
if data.get(“stat”) == “OK” and data.get(“data”):
last_row = data[“data”][-1]
close = float(last_row[6].replace(”,”, “”))
open_ = float(last_row[3].replace(”,”, “”))
change_pct = ((close - open_) / open_ * 100) if open_ else 0
results[code] = {
“name”: name,
“price”: round(close, 2),
“change_pct”: round(change_pct, 2),
“currency”: “TWD”
}
else:
results[code] = {“name”: name, “price”: None, “change_pct”: None}
except Exception as e:
results[code] = {“name”: name, “price”: None, “change_pct”: None, “error”: str(e)}
return results

# ─────────────────────────────────────

# 取得大盤指數

# ─────────────────────────────────────

def get_market_indices() -> dict:
indices = {
“^GSPC”: “S&P 500”,
“^IXIC”: “NASDAQ”,
“^DJI”: “道瓊斯”,
“^TWII”: “台股加權”,
}
results = {}
for symbol, name in indices.items():
try:
url = f”https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d”
headers = {“User-Agent”: “Mozilla/5.0”}
r = requests.get(url, headers=headers, timeout=10)
data = r.json()
meta = data[“chart”][“result”][0][“meta”]
price = meta.get(“regularMarketPrice”, 0)
prev  = meta.get(“chartPreviousClose”, price)
change_pct = ((price - prev) / prev * 100) if prev else 0
results[name] = {
“price”: round(price, 2),
“change_pct”: round(change_pct, 2)
}
except:
results[name] = {“price”: None, “change_pct”: None}
return results

# ─────────────────────────────────────

# 塔羅牌（每日固定主題）

# ─────────────────────────────────────

TAROT_CARDS = [
(“愚者”, “新的開始，保持開放心態，不要過度計算風險”),
(“魔術師”, “資源充足，主動出擊的好時機”),
(“女祭司”, “等待觀望，不宜衝動操作”),
(“皇后”, “豐收在望，持倉不動是明智之舉”),
(“皇帝”, “穩健為上，控制部位風險”),
(“教皇”, “遵循紀律，不要逆勢操作”),
(“戀人”, “需要做出選擇，分散風險”),
(“戰車”, “強勢突破，可適度加碼”),
(“力量”, “耐心等待，市場會回報”),
(“隱者”, “獨立思考，不要跟風追高”),
(“命運之輪”, “市場輪動，注意換股機會”),
(“正義”, “回歸基本面，理性評估”),
(“倒吊人”, “暫停，重新審視策略”),
(“死神”, “結束舊循環，止損離場思考”),
(“節制”, “平衡布局，不宜偏重單一持股”),
(“惡魔”, “貪婪警示，小心追高陷阱”),
(“高塔”, “突發變局，做好風險管理”),
(“星星”, “長線希望，逢低布局機會”),
(“月亮”, “市場迷霧，謹慎面對不確定性”),
(“太陽”, “樂觀情緒，但別忘記獲利了結”),
(“審判”, “重新評估投資組合”),
(“世界”, “完成一個循環，思考獲利時機”),
]

def draw_tarot() -> tuple[str, str]:
# 用日期當種子，同一天抽到同一張
seed = int(date.today().strftime(”%Y%m%d”))
random.seed(seed)
card = random.choice(TAROT_CARDS)
return card[0], card[1]

# ─────────────────────────────────────

# Claude 分析

# ─────────────────────────────────────

def analyze_with_claude(
us_data: dict,
tw_data: dict,
indices: dict,
tarot_name: str,
tarot_meaning: str
) -> str:
client = anthropic.Anthropic(api_key=os.environ[“ANTHROPIC_API_KEY”])

```
today_str = datetime.now().strftime("%Y/%m/%d")

prompt = f"""
```

你是一位資深台灣股市分析師，今天是 {today_str}。

請根據以下資料，用繁體中文生成一份簡潔的盤後分析報告，格式如下：

【大盤現況】
（用1-3行說明今日大盤氣氛）

【持股重點分析】
（每檔股票一行，格式：股票代號 現價 漲跌幅% → 操作建議）
（建議分為：強烈買入 / 買入 / 持有 / 減碼 / 賣出）

【今日重要財經訊號】
（2-3個今日最值得注意的市場訊號或風險）

【今日塔羅】
（根據今日塔羅牌給出整體操作心態建議，1-2行）

-----

大盤指數：
{json.dumps(indices, ensure_ascii=False, indent=2)}

美股持股：
{json.dumps(us_data, ensure_ascii=False, indent=2)}

台股持股：
{json.dumps(tw_data, ensure_ascii=False, indent=2)}

今日塔羅牌：{tarot_name}
牌意：{tarot_meaning}

注意：

- 語氣簡潔有力，像在跟朋友說話
- 每行不超過40個字
- 不要寫免責聲明
- 塔羅部分要融入當天市場情緒
  “””
  
  message = client.messages.create(
  model=“claude-opus-4-5-20251101”,
  max_tokens=1500,
  messages=[{“role”: “user”, “content”: prompt}]
  )
  return message.content[0].text

# ─────────────────────────────────────

# LINE Messaging API 推播

# ─────────────────────────────────────

def send_line_message(message: str):
token = os.environ[“LINE_CHANNEL_ACCESS_TOKEN”]
user_id = os.environ[“LINE_USER_ID”]
url = “https://api.line.me/v2/bot/message/push”
headers = {
“Authorization”: f”Bearer {token}”,
“Content-Type”: “application/json”
}

```
# LINE 單則訊息上限 5000 字，超過就分段
max_len = 4900
chunks = [message[i:i+max_len] for i in range(0, len(message), max_len)]

for chunk in chunks:
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": chunk}]
    }
    r = requests.post(url, headers=headers, json=payload)
    print(f"LINE Messaging API 回應：{r.status_code} {r.text}")
```

# ─────────────────────────────────────

# 產生 HTML Email 內容

# ─────────────────────────────────────

def build_html_email(analysis: str, indices: dict, us_data: dict, tw_data: dict, tarot_name: str, tarot_meaning: str) -> str:
today_str = datetime.now().strftime(”%Y/%m/%d”)

```
def pct_color(pct):
    if pct is None: return "#888888"
    return "#e74c3c" if pct >= 0 else "#27ae60"

def pct_str(pct):
    if pct is None: return "N/A"
    sign = "▲" if pct >= 0 else "▼"
    return f"{sign} {abs(pct):.2f}%"

# 大盤表格
index_rows = ""
for name, d in indices.items():
    color = pct_color(d.get("change_pct"))
    index_rows += f"""
    <tr>
        <td>{name}</td>
        <td>{d.get('price', 'N/A')}</td>
        <td style="color:{color};font-weight:bold">{pct_str(d.get('change_pct'))}</td>
    </tr>"""

# 美股表格
us_rows = ""
for sym, d in us_data.items():
    color = pct_color(d.get("change_pct"))
    us_rows += f"""
    <tr>
        <td><b>{sym}</b></td>
        <td>${d.get('price', 'N/A')}</td>
        <td style="color:{color};font-weight:bold">{pct_str(d.get('change_pct'))}</td>
    </tr>"""

# 台股表格
tw_rows = ""
for code, d in tw_data.items():
    color = pct_color(d.get("change_pct"))
    tw_rows += f"""
    <tr>
        <td><b>{d.get('name', code)} ({code})</b></td>
        <td>NT${d.get('price', 'N/A')}</td>
        <td style="color:{color};font-weight:bold">{pct_str(d.get('change_pct'))}</td>
    </tr>"""

# Claude 分析轉 HTML（把換行變 <br>）
analysis_html = analysis.replace("\n", "<br>")

html = f"""
```

<!DOCTYPE html>

<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, Arial, sans-serif; background:#f5f6fa; margin:0; padding:20px; }}
  .container {{ max-width:640px; margin:0 auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.08); }}
  .header {{ background:linear-gradient(135deg,#1a1a2e,#16213e); color:#fff; padding:24px 28px; }}
  .header h1 {{ margin:0; font-size:22px; letter-spacing:1px; }}
  .header p {{ margin:4px 0 0; opacity:0.6; font-size:13px; }}
  .section {{ padding:20px 28px; border-bottom:1px solid #f0f0f0; }}
  .section h2 {{ font-size:14px; color:#888; text-transform:uppercase; letter-spacing:1px; margin:0 0 12px; }}
  table {{ width:100%; border-collapse:collapse; font-size:14px; }}
  th {{ background:#f8f9fa; padding:8px 10px; text-align:left; color:#666; font-weight:600; font-size:12px; }}
  td {{ padding:8px 10px; border-bottom:1px solid #f5f5f5; }}
  tr:last-child td {{ border-bottom:none; }}
  .analysis {{ line-height:1.8; font-size:14px; color:#333; }}
  .tarot {{ background:#f8f0ff; border-left:4px solid #9b59b6; padding:14px 18px; border-radius:0 8px 8px 0; }}
  .tarot-name {{ font-size:18px; font-weight:bold; color:#9b59b6; }}
  .footer {{ padding:16px 28px; text-align:center; font-size:12px; color:#aaa; background:#fafafa; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📊 每日盤後分析</h1>
    <p>{today_str} · 台灣時間 16:00</p>
  </div>

  <div class="section">
    <h2>🌍 大盤指數</h2>
    <table>
      <tr><th>指數</th><th>價格</th><th>漲跌</th></tr>
      {index_rows}
    </table>
  </div>

  <div class="section">
    <h2>🇺🇸 美股持股</h2>
    <table>
      <tr><th>股票</th><th>現價</th><th>漲跌</th></tr>
      {us_rows}
    </table>
  </div>

  <div class="section">
    <h2>🇹🇼 台股持股</h2>
    <table>
      <tr><th>股票</th><th>現價</th><th>漲跌</th></tr>
      {tw_rows}
    </table>
  </div>

  <div class="section">
    <h2>🤖 Claude 分析</h2>
    <div class="analysis">{analysis_html}</div>
  </div>

  <div class="section">
    <h2>🔮 今日塔羅</h2>
    <div class="tarot">
      <div class="tarot-name">{tarot_name}</div>
      <div style="margin-top:6px;color:#555;font-size:14px">{tarot_meaning}</div>
    </div>
  </div>

  <div class="footer">本報告由 Claude AI 自動生成 · 僅供參考</div>
</div>
</body>
</html>"""
    return html

# ─────────────────────────────────────

# 寄送 Gmail

# ─────────────────────────────────────

def send_gmail(html_content: str, subject: str):
sender    = os.environ[“GMAIL_SENDER”]
password  = os.environ[“GMAIL_APP_PASSWORD”]
recipient = os.environ[“GMAIL_RECIPIENT”]

```
msg = MIMEMultipart("alternative")
msg["Subject"] = subject
msg["From"]    = sender
msg["To"]      = recipient
msg.attach(MIMEText(html_content, "html", "utf-8"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(sender, password)
    server.sendmail(sender, recipient, msg.as_string())
print(f"✅ Gmail 已寄出到 {recipient}")
```

# ─────────────────────────────────────

# 主程式

# ─────────────────────────────────────

def main():
print(f”[{datetime.now()}] 開始執行盤後分析…”)

```
print("📈 抓取大盤指數...")
indices = get_market_indices()

print("🇺🇸 抓取美股資料...")
us_data = get_us_stock_data(US_STOCKS)

print("🇹🇼 抓取台股資料...")
tw_data = get_tw_stock_data(TW_STOCKS)

print("🔮 抽塔羅牌...")
tarot_name, tarot_meaning = draw_tarot()
print(f"   今日塔羅：{tarot_name} - {tarot_meaning}")

print("🤖 Claude 分析中...")
analysis = analyze_with_claude(us_data, tw_data, indices, tarot_name, tarot_meaning)

today_str = datetime.now().strftime("%m/%d")
header = f"📊 {today_str} 盤後分析\n{'─'*20}\n"
full_message = header + analysis

print("📧 寄送 Gmail...")
subject = f"📊 {today_str} 每日盤後分析"
html = build_html_email(analysis, indices, us_data, tw_data, tarot_name, tarot_meaning)
send_gmail(html, subject)

print("📲 推播到 LINE...")
send_line_message(full_message)

print("✅ 完成！")
```

if **name** == “**main**”:
main()