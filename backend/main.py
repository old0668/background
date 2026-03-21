import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import rembg
import io
from PIL import Image

app = FastAPI()

# 設定 CORS：允許你的 Cloudflare Pages 網域與開發環境
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 正式部署後，建議將 "*" 改為你的 Cloudflare 網址以增強安全性
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/remove-bg")
async def remove_background(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="請上傳圖片檔案")

    try:
        input_image = await file.read()
        output_image = rembg.remove(input_image)
        return Response(content=output_image, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"去背處理髮生錯誤: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "background-remover"}

@app.get("/")
def read_root():
    return {"message": "AI Background Removal API is online!"}

if __name__ == "__main__":
    import uvicorn
    # Render 會提供一個名為 PORT 的環境變數
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
