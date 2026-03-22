🟢 正確安裝與執行步驟
請依序在 PowerShell 執行以下指令：

1. 安裝基礎圖片與運算庫

PowerShell
python -m pip install Pillow numpy
2. 安裝去背核心引擎 (含 CPU 運算組件)
這是最關鍵的一步，必須加上 [cpu] 確保安裝對應的運算後端：

PowerShell
python -m pip install "rembg[cpu]"
3. 驗證環境是否正常
執行這行指令，若出現「環境配置成功」且沒有報錯，代表所有套件都已到位：

PowerShell
python -c "import PIL; import numpy; import rembg; print('環境配置成功！')"
4. 啟動程式

PowerShell
python .\remover_app_win.py