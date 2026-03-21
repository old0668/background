# 🚀 圖片自動去背網頁：雲端部署指南

本專案採用 **Cloudflare Pages (前端)** + **Render (後端 AI 引擎)** 的黃金組合。

---

## 1. 準備程式碼並上傳至 GitHub
1. 在 GitHub 上建立一個新的私有或公開 Repository。
2. 在本地終端機執行：
   ```bash
   git init
   git add .
   git commit -m "feat: 準備雲端部署版本"
   git branch -M main
   git remote add origin https://github.com/你的帳號/你的專案名.git
   git push -u origin main
   ```

---

## 2. 部署後端 (Render)
1. 註冊/登入 [Render.com](https://render.com/)。
2. 點擊 **New+** -> **Web Service**。
3. 連接你的 GitHub Repository。
4. 設定如下：
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Plan:** 選 `Free` (免費版)。
5. **重要：** 部署成功後，你會得到一個網址（例如 `https://remover-api.onrender.com`），請複製它。

---

## 3. 部署前端 (Cloudflare Pages)
1. 註冊/登入 [Cloudflare Dashboard](https://dash.cloudflare.com/)。
2. 進入 **Workers & Pages** -> **Create application** -> **Pages**。
3. 連接你的 GitHub Repository。
4. 設定如下：
   - **Project name:** 隨意取名。
   - **Framework preset:** `Vite` (或是選擇 `None` 並手動設定)。
   - **Root directory:** `frontend`
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
5. **關鍵步驟 (串接 API)：**
   - 在 **Environment variables (環境變數)** 區塊點擊 **Add variable**。
   - **Variable name:** `VITE_API_URL`
   - **Value:** 貼上你剛才在 Render 得到的網址 (例如 `https://remover-api.onrender.com`)。
6. 點擊 **Save and Deploy**。

---

## 💡 溫馨小提醒
- **Render 免費版啟動較慢：** 如果網頁第一次按下去背沒反應，可能是 Render 的伺服器正在「冷啟動」，通常需要 30-50 秒。
- **CORS 設定：** 如果之後遇到跨網域問題，請到 `backend/main.py` 修改 `allow_origins` 為你正式的 Cloudflare 網址。

祝你部署順利！✨
