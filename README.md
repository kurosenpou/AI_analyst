# AI Business Agent MVP

極簡型 WebApp，專為中小企業主與獨立創業者設計，自動上傳資料並生成商業報告書與投資建議書。

## 🎯 特色功能

- **終端風格界面**：Windows Terminal 風格的極簡 UI
- **拖拽上傳**：支援 CSV、PDF、Excel 文件直接拖拽上傳
- **AI 分析**：使用 GPT-4 進行智能數據分析
- **三種報告**：商業計劃書、市場分析報告、投資建議書
- **實時進度**：終端風格的實時處理進度顯示

## 🚀 快速開始

### 環境配置
創建 `.env` 文件：
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 後端啟動
```bash
cd backend
pip install fastapi uvicorn openai python-multipart pandas PyPDF2 openpyxl python-dotenv
python main.py
```

### 前端啟動
```bash
cd frontend
npm install
npm run dev
```

## 📁 項目結構

```
/ai-business-agent-mvp
├── backend/
│   ├── main.py              # FastAPI 主程序
│   ├── models/              # 數據模型
│   ├── routers/             # API 路由
│   └── services/            # 核心服務
├── frontend/
│   ├── app/                 # Next.js 頁面
│   ├── components/          # React 組件
│   └── lib/                 # 工具函數
├── .env                     # 環境變量
└── README.md               # 項目說明
```

## 🔧 技術棧

- **前端**：Next.js 14 + TypeScript + Tailwind CSS
- **後端**：Python FastAPI + OpenAI GPT-4
- **部署**：極簡單檔部署，無數據庫依賴

## 📝 使用方法

1. 啟動前後端服務
2. 訪問 http://localhost:3000
3. 拖拽文件到終端界面
4. 輸入特殊要求（可選）
5. 觀看實時處理進度
6. 查看生成的專業報告

## 🎨 界面特色

- **終端風格**：仿 Windows Terminal 的黑色主題
- **拖拽交互**：直觀的文件拖拽上傳體驗
- **實時反饋**：終端風格的處理日誌和進度顯示
- **側邊菜單**：簡潔的報告管理和系統設置

## 📊 支持格式

- **CSV**：數據表格文件
- **PDF**：文檔資料
- **Excel**：.xlsx/.xls 表格文件
- **最大文件**：10MB

## 🔒 極簡設計理念

- **零數據庫**：無需配置數據庫，直接運行
- **最少依賴**：精簡的依賴包，快速安裝
- **單檔部署**：前後端分離，獨立部署
- **終端美學**：專業的終端風格用戶界面
