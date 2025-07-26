# AI Analyst - 智能分析系統

一個基於多模型辯論機制的智能分析系統，提供高質量的數據分析和決策支持。

## 🚀 功能特性

### 核心功能
- **三模型辯論引擎**: 使用多個AI模型進行辯論式分析，提高結果準確性
- **智能議事錄生成**: 自動生成結構化的分析報告和會議記錄
- **高級辯論功能**: 支持複雜的多輪辯論和動態模型輪換
- **實時監控系統**: 完整的性能監控和日誌記錄

### 技術特性
- **容器化部署**: 使用Docker和Docker Compose進行一鍵部署
- **微服務架構**: 前後端分離，易於擴展和維護
- **高可用性**: 內建容錯機制和降級策略
- **監控告警**: 集成Prometheus和Grafana監控系統
- **CI/CD**: 自動化測試和部署流程

## 🏗️ 系統架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │     Redis       │              │
         │              │   (Cache)       │              │
         │              │   Port: 6379    │              │
         │              └─────────────────┘              │
         │                                                │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │    Grafana      │    │   AI Models     │
│  (Monitoring)   │    │  (Dashboard)    │    │ (OpenRouter)    │
│   Port: 9090    │    │   Port: 3001    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 系統要求

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Node.js**: 18+ (開發環境)
- **Python**: 3.11+ (開發環境)
- **內存**: 最少 4GB RAM
- **存儲**: 最少 10GB 可用空間

## 🚀 快速開始

### 1. 克隆項目

```bash
git clone <repository-url>
cd AI_analyst
```

### 2. 環境配置

創建 `.env` 文件：

```bash
cp .env.example .env
```

編輯 `.env` 文件，設置必要的環境變量：

```env
# API Keys
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Database
DATABASE_URL=postgresql://ai_analyst_user:ai_analyst_password@postgres:5432/ai_analyst
REDIS_URL=redis://redis:6379

# Environment
ENVIRONMENT=production

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
```

### 3. 啟動服務

```bash
# 構建並啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

### 4. 訪問應用

- **前端應用**: http://localhost:3000
- **後端API**: http://localhost:8000
- **API文檔**: http://localhost:8000/docs
- **Grafana監控**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090

## 📁 項目結構

```
AI_analyst/
├── backend/                 # 後端服務
│   ├── main.py             # FastAPI 主應用
│   ├── models/             # 數據模型
│   ├── routers/            # API 路由
│   ├── services/           # 業務邏輯
│   ├── utils/              # 工具函數
│   └── requirements.txt    # Python 依賴
├── frontend/               # 前端應用
│   ├── src/                # 源代碼
│   ├── public/             # 靜態資源
│   ├── package.json        # Node.js 依賴
│   └── next.config.js      # Next.js 配置
├── docker/                 # Docker 配置
│   ├── Dockerfile.backend  # 後端容器配置
│   ├── Dockerfile.frontend # 前端容器配置
│   ├── init-db.sql        # 數據庫初始化
│   ├── prometheus.yml     # Prometheus 配置
│   └── grafana/           # Grafana 配置
├── .github/workflows/      # CI/CD 配置
├── docs/                   # 文檔
├── tests/                  # 測試文件
├── docker-compose.yml      # 服務編排
└── README.md              # 項目說明
```

## 🔧 技術棧

- **前端**：Next.js 14 + TypeScript + Tailwind CSS
- **後端**：Python FastAPI + OpenRouter API
- **數據庫**：PostgreSQL + Redis
- **監控**：Prometheus + Grafana
- **部署**：Docker + Docker Compose

## 📝 使用方法

1. 啟動所有服務
2. 訪問 http://localhost:3000
3. 上傳分析文件或輸入問題
4. 選擇辯論模式和參與模型
5. 觀看實時辯論過程
6. 查看生成的分析報告

## 🎨 界面特色

- **現代化設計**：響應式的現代化用戶界面
- **實時辯論**：可視化的多模型辯論過程
- **智能分析**：深度的數據分析和洞察
- **監控面板**：完整的系統監控和性能指標

## 📊 支持格式

- **CSV**：數據表格文件
- **PDF**：文檔資料
- **Excel**：.xlsx/.xls 表格文件
- **JSON**：結構化數據
- **最大文件**：50MB

## 🔒 企業級特性

- **容器化部署**：使用Docker進行標準化部署
- **微服務架構**：模塊化設計，易於擴展
- **監控告警**：完整的系統監控和告警機制
- **高可用性**：內建容錯和降級策略
