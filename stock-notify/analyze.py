‘’’
Daily stock analysis + LINE & Gmail notification
‘’’

import os
import json
import requests
import anthropic
from datetime import datetime, date
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

US_STOCKS = [
‘APLD’, ‘ASML’, ‘MRVL’, ‘RXRX’, ‘TSLA’, ‘NVDA’,
‘GOOGL’, ‘CRWV’, ‘AMD’, ‘NEE’, ‘VST’, ‘MU’,
‘VRT’, ‘MP’, ‘AVGO’, ‘PANW’, ‘AMZN’
]

TW_STOCKS = [
(‘2330’, ‘TSMC’),
(‘2404’, ‘HanTang’),
(‘2812’, ‘TaichungBank’),
(‘2834’, ‘TaiwanBiz’),
(‘2845’, ‘FarEastBank’),
(‘3293’, ‘IGS’),
]

def get_us_stock_data(symbols):
results = {}
for sym in symbols:
try:
url = ‘https://query1.finance.yahoo.com/v8/finance/chart/’ + sym + ‘?interval=1d&range=2d’
headers = {‘User-Agent’: ‘Mozilla/5.0’}
r = requests.get(url, headers=headers, timeout=10)
data = r.json()
meta = data[‘chart’][‘result’][0][‘meta’]
price = meta.get(‘regularMarketPrice’, 0)
prev = meta.get(‘chartPreviousClose’, price)
change_pct = ((price - prev) / prev * 100) if prev else 0
results[sym] = {
‘price’: round(price, 2),
‘change_pct’: round(change_pct, 2),
‘currency’: ‘USD’
}
except Exception as e:
results[sym] = {‘price’: None, ‘change_pct’: None, ‘error’: str(e)}
return results

def get_tw_stock_data(stocks):
results = {}
today = date.today().strftime(’%Y%m%d’)
for code, name in stocks:
try:
url = ‘https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date=’ + today + ‘&stockNo=’ + code
r = requests.get(url, timeout=10)
data = r.json()
if data.get(‘stat’) == ‘OK’ and data.get(‘data’):
last_row = data[‘data’][-1]
close = float(last_row[6].replace(’,’, ‘’))
open_ = float(last_row[3].replace(’,’, ‘’))
change_pct = ((close - open_) / open_ * 100) if open_ else 0
results[code] = {
‘name’: name,
‘price’: round(close, 2),
‘change_pct’: round(change_pct, 2),
‘currency’: ‘TWD’
}
else:
results[code] = {‘name’: name, ‘price’: None, ‘change_pct’: None}
except Exception as e:
results[code] = {‘name’: name, ‘price’: None, ‘change_pct’: None, ‘error’: str(e)}
return results

def get_market_indices():
indices = {
‘^GSPC’: ‘S&P 500’,
‘^IXIC’: ‘NASDAQ’,
‘^DJI’: ‘DOW’,
‘^TWII’: ‘TAIEX’,
}
results = {}
for symbol, name in indices.items():
try:
url = ‘https://query1.finance.yahoo.com/v8/finance/chart/’ + symbol + ‘?interval=1d&range=2d’
headers = {‘User-Agent’: ‘Mozilla/5.0’}
r = requests.get(url, headers=headers, timeout=10)
data = r.json()
meta = data[‘chart’][‘result’][0][‘meta’]
price = meta.get(‘regularMarketPrice’, 0)
prev = meta.get(‘chartPreviousClose’, price)
change_pct = ((price - prev) / prev * 100) if prev else 0
results[name] = {
‘price’: round(price, 2),
‘change_pct’: round(change_pct, 2)
}
except Exception:
results[name] = {‘price’: None, ‘change_pct’: None}
return results

TAROT_CARDS = [
(‘The Fool’, ‘New beginning, stay open, avoid over-calculating risk’),
(‘The Magician’, ‘Resources ready, good time to act’),
(‘The High Priestess’, ‘Wait and watch, avoid impulsive trades’),
(‘The Empress’, ‘Harvest ahead, hold your positions’),
(‘The Emperor’, ‘Stay steady, manage position risk’),
(‘The Hierophant’, ‘Follow discipline, avoid fighting the trend’),
(‘The Lovers’, ‘Need to choose, diversify risk’),
(‘The Chariot’, ‘Strong breakout, consider adding’),
(‘Strength’, ‘Be patient, market will reward’),
(‘The Hermit’, ‘Think independently, avoid chasing highs’),
(‘Wheel of Fortune’, ‘Rotation in play, watch for sector shifts’),
(‘Justice’, ‘Back to fundamentals, rational assessment’),
(‘The Hanged Man’, ‘Pause, re-examine your strategy’),
(‘Death’, ‘End of cycle, consider cutting losses’),
(‘Temperance’, ‘Balance your portfolio, avoid concentration’),
(‘The Devil’, ‘Greed warning, beware of chasing highs’),
(‘The Tower’, ‘Sudden change, manage your risk’),
(‘The Star’, ‘Long-term hope, buy the dip’),
(‘The Moon’, ‘Market fog, cautious amid uncertainty’),
(‘The Sun’, ‘Optimism rising, but remember to take profit’),
(‘Judgement’, ‘Re-evaluate your portfolio’),
(‘The World’, ‘Cycle complete, time to consider profits’),
]

def draw_tarot():
seed = int(date.today().strftime(’%Y%m%d’))
random.seed(seed)
card = random.choice(TAROT_CARDS)
return card[0], card[1]

def analyze_with_claude(us_data, tw_data, indices, tarot_name, tarot_meaning):
client = anthropic.Anthropic(api_key=os.environ[‘ANTHROPIC_API_KEY’])
today_str = datetime.now().strftime(’%Y/%m/%d’)

```
prompt = (
    'You are a senior Taiwan stock analyst. Today is ' + today_str + '.\n\n'
    'Based on the data below, write a concise after-market report in Traditional Chinese.\n\n'
    'Use this exact format:\n\n'
    '[大盤現況]\n'
    '(1-3 lines on today market mood)\n\n'
    '[持股重點分析]\n'
    '(one line per stock: symbol price change% arrow suggestion)\n'
    '(suggestions: 強烈買入 / 買入 / 持有 / 減碼 / 賣出)\n\n'
    '[今日重要財經訊號]\n'
    '(2-3 key signals or risks)\n\n'
    '[今日塔羅]\n'
    '(1-2 lines blending tarot with today market mood)\n\n'
    '---\n'
    'Indices:\n' + json.dumps(indices, ensure_ascii=False) + '\n\n'
    'US stocks:\n' + json.dumps(us_data, ensure_ascii=False) + '\n\n'
    'TW stocks:\n' + json.dumps(tw_data, ensure_ascii=False) + '\n\n'
    'Tarot card: ' + tarot_name + '\n'
    'Meaning: ' + tarot_meaning + '\n\n'
    'Rules: concise, friendly tone, max 40 chars per line, no disclaimers.'
)

message = client.messages.create(
    model='claude-opus-4-5-20251101',
    max_tokens=1500,
    messages=[{'role': 'user', 'content': prompt}]
)
return message.content[0].text
```

def build_html_email(analysis, indices, us_data, tw_data, tarot_name, tarot_meaning):
today_str = datetime.now().strftime(’%Y/%m/%d’)

```
def pct_color(pct):
    if pct is None:
        return '#888888'
    return '#e74c3c' if pct >= 0 else '#27ae60'

def pct_str(pct):
    if pct is None:
        return 'N/A'
    sign = '+' if pct >= 0 else ''
    return sign + str(round(pct, 2)) + '%'

index_rows = ''
for name, d in indices.items():
    color = pct_color(d.get('change_pct'))
    index_rows += '<tr><td>' + name + '</td><td>' + str(d.get('price', 'N/A')) + '</td><td style="color:' + color + ';font-weight:bold">' + pct_str(d.get('change_pct')) + '</td></tr>'

us_rows = ''
for sym, d in us_data.items():
    color = pct_color(d.get('change_pct'))
    us_rows += '<tr><td><b>' + sym + '</b></td><td>$' + str(d.get('price', 'N/A')) + '</td><td style="color:' + color + ';font-weight:bold">' + pct_str(d.get('change_pct')) + '</td></tr>'

tw_rows = ''
for code, d in tw_data.items():
    color = pct_color(d.get('change_pct'))
    tw_rows += '<tr><td><b>' + d.get('name', code) + ' (' + code + ')</b></td><td>NT$' + str(d.get('price', 'N/A')) + '</td><td style="color:' + color + ';font-weight:bold">' + pct_str(d.get('change_pct')) + '</td></tr>'

analysis_html = analysis.replace('\n', '<br>')

css = (
    'body{font-family:Arial,sans-serif;background:#f5f6fa;margin:0;padding:20px}'
    '.wrap{max-width:640px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08)}'
    '.hdr{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:24px 28px}'
    '.hdr h1{margin:0;font-size:22px}'
    '.hdr p{margin:4px 0 0;opacity:0.6;font-size:13px}'
    '.sec{padding:20px 28px;border-bottom:1px solid #f0f0f0}'
    '.sec h2{font-size:13px;color:#888;text-transform:uppercase;letter-spacing:1px;margin:0 0 12px}'
    'table{width:100%;border-collapse:collapse;font-size:14px}'
    'th{background:#f8f9fa;padding:8px 10px;text-align:left;color:#666;font-weight:600;font-size:12px}'
    'td{padding:8px 10px;border-bottom:1px solid #f5f5f5}'
    'tr:last-child td{border-bottom:none}'
    '.analysis{line-height:1.8;font-size:14px;color:#333}'
    '.tarot{background:#f8f0ff;border-left:4px solid #9b59b6;padding:14px 18px;border-radius:0 8px 8px 0}'
    '.tname{font-size:18px;font-weight:bold;color:#9b59b6}'
    '.ftr{padding:16px 28px;text-align:center;font-size:12px;color:#aaa;background:#fafafa}'
)

html = (
    '<!DOCTYPE html><html><head><meta charset="utf-8"><style>' + css + '</style></head><body>'
    '<div class="wrap">'
    '<div class="hdr"><h1>Daily Market Report</h1><p>' + today_str + '</p></div>'
    '<div class="sec"><h2>Market Indices</h2><table><tr><th>Index</th><th>Price</th><th>Change</th></tr>' + index_rows + '</table></div>'
    '<div class="sec"><h2>US Holdings</h2><table><tr><th>Symbol</th><th>Price</th><th>Change</th></tr>' + us_rows + '</table></div>'
    '<div class="sec"><h2>TW Holdings</h2><table><tr><th>Stock</th><th>Price</th><th>Change</th></tr>' + tw_rows + '</table></div>'
    '<div class="sec"><h2>Claude Analysis</h2><div class="analysis">' + analysis_html + '</div></div>'
    '<div class="sec"><h2>Tarot</h2><div class="tarot"><div class="tname">' + tarot_name + '</div><div style="margin-top:6px;color:#555;font-size:14px">' + tarot_meaning + '</div></div></div>'
    '<div class="ftr">Auto-generated by Claude AI</div>'
    '</div></body></html>'
)
return html
```

def send_gmail(html_content, subject):
sender = os.environ[‘GMAIL_SENDER’]
password = os.environ[‘GMAIL_APP_PASSWORD’]
recipient = os.environ[‘GMAIL_RECIPIENT’]

```
msg = MIMEMultipart('alternative')
msg['Subject'] = subject
msg['From'] = sender
msg['To'] = recipient
msg.attach(MIMEText(html_content, 'html', 'utf-8'))

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
    server.login(sender, password)
    server.sendmail(sender, recipient, msg.as_string())
print('Gmail sent to ' + recipient)
```

def send_line_message(message):
token = os.environ[‘LINE_CHANNEL_ACCESS_TOKEN’]
user_id = os.environ[‘LINE_USER_ID’]
url = ‘https://api.line.me/v2/bot/message/push’
headers = {
‘Authorization’: ’Bearer ’ + token,
‘Content-Type’: ‘application/json’
}
max_len = 4900
chunks = [message[i:i + max_len] for i in range(0, len(message), max_len)]
for chunk in chunks:
payload = {
‘to’: user_id,
‘messages’: [{‘type’: ‘text’, ‘text’: chunk}]
}
r = requests.post(url, headers=headers, json=payload)
print(’LINE response: ’ + str(r.status_code))

def main():
print(‘Starting daily analysis…’)

```
print('Fetching indices...')
indices = get_market_indices()

print('Fetching US stocks...')
us_data = get_us_stock_data(US_STOCKS)

print('Fetching TW stocks...')
tw_data = get_tw_stock_data(TW_STOCKS)

print('Drawing tarot...')
tarot_name, tarot_meaning = draw_tarot()
print('Tarot: ' + tarot_name)

print('Analyzing with Claude...')
analysis = analyze_with_claude(us_data, tw_data, indices, tarot_name, tarot_meaning)

today_str = datetime.now().strftime('%m/%d')
full_message = 'Daily Report ' + today_str + '\n' + '=' * 20 + '\n' + analysis

print('Sending Gmail...')
subject = 'Daily Market Report ' + today_str
html = build_html_email(analysis, indices, us_data, tw_data, tarot_name, tarot_meaning)
send_gmail(html, subject)

print('Sending LINE...')
send_line_message(full_message)

print('Done!')
```

if **name** == ‘**main**’:
main()