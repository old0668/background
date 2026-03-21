import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import rembg
import io
from PIL import Image

app = FastAPI()

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 建立去背處理器 (這會在第一次執行時載入模型)
# 在 Render 免費版建議在需要時才載入，或先預載
@app.post("/remove-bg")
async def remove_background(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="請上傳圖片檔案")

    try:
        input_image = await file.read()
        # 這裡會自動處理模型載入
        output_image = rembg.remove(input_image)
        return Response(content=output_image, media_type="image/png")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"去背處理髮生錯誤: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/")
def read_root():
    return {"message": "AI Background Removal API is online!"}

if __name__ == "__main__":
    # Render 會自動偵測 PORT 並指派
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
