import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import rembg
import io
from PIL import Image

app = FastAPI()

# 設定 CORS：允許所有來源，這在部署到 Cloudflare + Render 時最穩定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        # 執行去背
        output_image = rembg.remove(input_image)
        return Response(content=output_image, media_type="image/png")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"去背處理髮生錯誤: {str(e)}")

@app.get("/health")
@app.get("/")
def health_check():
    return {"status": "online"}
