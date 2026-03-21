import { useState, useCallback, ChangeEvent, DragEvent } from 'react';
import './App.css';

function App() {
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [originalUrl, setOriginalUrl] = useState<string | null>(null);
  const [processedUrl, setProcessedUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('請上傳圖片檔案 (JPG, PNG, WEBP)');
      return;
    }
    setError(null);
    setOriginalFile(file);
    setOriginalUrl(URL.createObjectURL(file));
    setProcessedUrl(null);
  };

  const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const onDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const removeBackground = async () => {
    if (!originalFile) return;

    setIsProcessing(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', originalFile);

    // 從環境變數讀取後端網址，如果沒有則預設為 localhost:8000
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    try {
      const response = await fetch(`${API_URL}/remove-bg`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('去背處理失敗，請稍後再試。');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setProcessedUrl(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : '發生未知錯誤');
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadImage = () => {
    if (!processedUrl) return;
    const link = document.createElement('a');
    link.href = processedUrl;
    link.download = `no-bg-${originalFile?.name.split('.')[0] || 'image'}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="container">
      <header>
        <h1>AI 圖片去背</h1>
        <p>一鍵去除背景，獲得高品質透明 PNG</p>
      </header>

      <main>
        {!originalUrl ? (
          <div 
            className="drop-zone" 
            onDrop={onDrop} 
            onDragOver={onDragOver}
            onClick={() => document.getElementById('fileInput')?.click()}
          >
            <input 
              type="file" 
              id="fileInput" 
              hidden 
              onChange={onFileChange} 
              accept="image/*" 
            />
            <div className="icon">📸</div>
            <p>點擊或拖曳圖片到這裡</p>
            <span>支援 JPG, PNG, WEBP</span>
          </div>
        ) : (
          <div className="preview-container">
            <div className="preview-grid">
              <div className="preview-box">
                <h3>原始圖片</h3>
                <img src={originalUrl} alt="Original" />
              </div>
              
              <div className="preview-box result">
                <h3>去背結果</h3>
                {isProcessing ? (
                  <div className="loading">
                    <div className="spinner"></div>
                    <p>AI 正在處理中...</p>
                  </div>
                ) : processedUrl ? (
                  <img src={processedUrl} alt="Processed" className="checkerboard" />
                ) : (
                  <div className="placeholder">
                    <button className="primary-btn" onClick={removeBackground}>
                      開始去背
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="actions">
              <button className="secondary-btn" onClick={() => {
                setOriginalUrl(null);
                setProcessedUrl(null);
                setOriginalFile(null);
              }}>
                重新上傳
              </button>
              {processedUrl && (
                <button className="download-btn" onClick={downloadImage}>
                  下載透明 PNG
                </button>
              )}
            </div>
          </div>
        )}

        {error && <p className="error-msg">{error}</p>}
      </main>

      <footer>
        <p>Powered by FastAPI & Rembg</p>
      </footer>
    </div>
  );
}

export default App;
