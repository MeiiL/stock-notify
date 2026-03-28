# 每日股市分析 LINE & Gmail 推播

每天台灣時間 **20:00**（盤前），自動分析持股並同時推播到 Gmail 和 LINE。

## 功能

- 美股 + 台股持股個股分析
- 大盤現況（S&P 500 / NASDAQ / 台股加權）
- 操作建議（強烈買入 / 買入 / 持有 / 減碼 / 賣出）
- 重要財經訊號
- 每日塔羅牌建議
- Gmail HTML 排版報告
- LINE Bot 推播

-----

## 檔案結構

```
stock-notify/
├── analyze.py
├── README.md
└── .github/
    └── workflows/
        └── daily_stock.yml
```

-----

## 設定步驟

### 1. 取得 Anthropic API Key

1. 去 https://console.anthropic.com/
1. 點「API Keys」→「Create Key」
1. 複製 Key

-----

### 2. 設定 Gmail

#### 2-1. 開啟兩步驟驗證

1. 去 https://myaccount.google.com/
1. 搜尋「兩步驟驗證」→ 開啟

#### 2-2. 產生應用程式密碼

1. 搜尋「應用程式密碼」
1. 選「郵件」→「其他裝置」→ 輸入名稱（例如：股市分析）
1. 複製那組 **16 碼密碼**（不是你的 Gmail 登入密碼！）

-----

### 3. 設定 LINE Messaging API

#### 3-1. 建立 LINE Official Account

1. 去 https://manager.line.biz/
1. 點「建立帳號」→「Messaging API」
1. 填寫基本資料

#### 3-2. 啟用 Messaging API

1. 進入帳號 → 「設定」→「Messaging API」
1. 點「啟用 Messaging API」

#### 3-3. 取得 Channel Access Token（長效型）

1. 去 **https://developers.line.biz/**
1. 登入 → 點你的 Provider → 點你的 Channel
1. 上方 tab 點「**Messaging API**」
1. 滑到**最下面**找到「Channel access token」
1. 點「**Issue**」→ 複製那串很長的 token（200+ 字元）

> ⚠️ 不是 Channel Secret！Token 非常長。

#### 3-4. 加 Bot 為好友

1. 在「Messaging API」頁籤找到 QR code
1. 用你的 LINE 掃描加好友
1. **一定要加好友才能收到訊息！**

-----

### 4. 建立 GitHub Repo 並上傳檔案

```bash
git init
git add .
git commit -m "init"
git remote add origin https://github.com/你的帳號/stock-notify.git
git push -u origin main
```

-----

### 5. 設定 GitHub Secrets

Repo → Settings → Secrets and variables → Actions → **New repository secret**

|Secret 名稱                  |內容                                 |
|---------------------------|-----------------------------------|
|`ANTHROPIC_API_KEY`        |Anthropic API Key                  |
|`GMAIL_SENDER`             |寄件 Gmail（例如 abc@gmail.com）         |
|`GMAIL_APP_PASSWORD`       |Gmail 應用程式密碼（16碼）                  |
|`GMAIL_RECIPIENT`          |收件信箱                               |
|`LINE_CHANNEL_ACCESS_TOKEN`|LINE 長效 Channel Access Token       |
|`LINE_USER_ID`             |你的 LINE User ID（Basic settings 頁籤找）|

-----

### 6. 測試

Actions → 「每日股市分析推播」→「Run workflow」

-----

## 費用估算

|項目                |費用                           |
|------------------|-----------------------------|
|GitHub Actions    |免費（每月 2000 分鐘）               |
|LINE Messaging API|每月 200 則免費                   |
|Gmail SMTP        |完全免費                         |
|Claude API        |約 $0.03 - 0.10 美元/次，每月約 $1~2 美元|

-----

## 常見問題

**LINE 401 錯誤**

- Token 要用長效型（Issue 出來那個），不是 Channel Secret
- Token 要完整複製，非常長（200+ 字元）
- 要先加 Bot 為好友才能收訊息

**Gmail 認證失敗**

- 要用應用程式密碼，不是 Gmail 登入密碼
- 需要先開啟兩步驟驗證才能產生應用程式密碼
