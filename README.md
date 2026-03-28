# 📊 每日股市分析 LINE 推播

每天台灣時間 **20:00**（美股盤前），自動分析持股並推播到你的 LINE。

## 功能

- ✅ 美股 + 台股持股個股分析
- ✅ 大盤現況（S&P 500 / NASDAQ / 台股加權）
- ✅ 操作建議（買入 / 持有 / 減碼 / 賣出）
- ✅ 重要財經訊號
- ✅ 每日塔羅牌建議

-----

## 設定步驟（10分鐘完成）

### 1. 取得 LINE Notify Token

1. 前往 https://notify-bot.line.me/
1. 登入 LINE 帳號
1. 點選「個人頁面」→「發行權杖」
1. 輸入名稱（例如：股市分析），選「透過1對1聊天接收LINE Notify的通知」
1. 複製 Token（只會顯示一次！）

### 2. 取得 Anthropic API Key

1. 前往 https://console.anthropic.com/
1. 「API Keys」→「Create Key」
1. 複製 Key

### 3. 建立 GitHub Repo

```bash
# 建立新 repo（可設為 private）
git init
git add .
git commit -m "init"
git remote add origin https://github.com/你的帳號/stock-notify.git
git push -u origin main
```

### 4. 設定 GitHub Secrets

1. 進入你的 GitHub Repo
1. Settings → Secrets and variables → Actions
1. 新增兩個 Secret：

|Name               |Value               |
|-------------------|--------------------|
|`ANTHROPIC_API_KEY`|你的 Anthropic API Key|
|`LINE_NOTIFY_TOKEN`|你的 LINE Notify Token|

### 5. 啟用 GitHub Actions

1. 點選 Repo 的「Actions」頁籤
1. 確認 workflow 已啟用
1. 手動觸發測試：Actions → 「每日股市分析推播」→「Run workflow」

-----

## 測試本地執行

```bash
pip install anthropic requests

export ANTHROPIC_API_KEY="你的key"
export LINE_NOTIFY_TOKEN="你的token"

python analyze.py
```

-----

## 更新持股

編輯 `analyze.py` 最上方的設定區：

```python
US_STOCKS = ["NVDA", "TSLA", ...]   # 美股
TW_STOCKS = [("2330", "台積電"), ...]  # 台股
```

-----

## 費用估算

|項目            |費用               |
|--------------|-----------------|
|GitHub Actions|免費（每月 2000 分鐘）   |
|LINE Notify   |完全免費             |
|Claude API    |約 $0.03~0.10 美元/次|

每月約 **$1~2 美元** 的 Claude API 費用。
