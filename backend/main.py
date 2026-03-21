import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

app = FastAPI()

# 設定 CORS
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
        from rembg import remove, new_session
        from PIL import Image
        import io
        
        # 讀取圖片
        input_data = await file.read()
        img = Image.open(io.BytesIO(input_data))
        
        # 轉換為 RGB (如果是 RGBA 先處理)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 縮小圖片解析度以加速運算 (如果長寬超過 1200px)
        max_size = 1200
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size))
        
        # 將縮小後的圖片轉回 bytes
        temp_buffer = io.BytesIO()
        img.save(temp_buffer, format="PNG")
        resized_data = temp_buffer.getvalue()

        # 執行去背 (使用輕量級模型)
        session = new_session("u2netp")
        output_image = remove(resized_data, session=session)
        
        return Response(content=output_image, media_type="image/png")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"去背處理髮生錯誤: {str(e)}")

@app.get("/health")
@app.get("/")
def health_check():
    return {"status": "online"}
