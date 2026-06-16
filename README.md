# 医陪帮 - 智能就医助手系统

**版本：** v3.0  
**开发状态：** 期末汇报演示版  
**技术栈：** FastAPI + 原生前端 + SSE流式输出 + RAG知识库 + 记忆系统 + 主动提醒

---

## 🎯 项目简介

医陪帮是一个面向老年慢病患者和陪诊家属的智能就医助手系统。系统不是通用聊天框，而是把自然语言映射为就医准备、报告解读、长期记忆、知识库检索、主动提醒、家属协同和急症安全拦截等操作。

### 核心特性

- ✅ **高端医疗AI工作台** - 左侧用户画像，中间流式对话，右侧实时智能体决策轨迹
- ✅ **候选问题与病例样例库** - 糖尿病复诊、胸痛急症、高血压随访、术后复查、儿童发热
- ✅ **流式对话** - SSE实时输出，不依赖外部大模型也能稳定现场演示
- ✅ **意图识别路由** - ACTION / HYBRID / RAG / SAFE 四类路由显式展示
- ✅ **聊天即操作** - 一句话触发材料清单、问诊提纲、提醒、家属摘要
- ✅ **记忆系统** - 展示记忆内容、存储格式与更新策略
- ✅ **RAG知识库** - 报告术语、复诊材料、安全边界等知识命中可见
- ✅ **主动服务** - 复诊提醒、材料缺项提醒、家属同步
- ✅ **安全边界** - 胸痛、呼吸困难等急症触发 SAFE 拦截

---

## 📦 快速开始

### 1. 环境要求

- Python 3.10+
- 8GB+ 内存（用于嵌入模型）
- 稳定的网络连接（API调用）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

编辑 `services/llm_service.py`，配置您的API密钥：

```python
API_KEYS = {
    LLMProvider.GEMINI: "YOUR_GEMINI_API_KEY",
    LLMProvider.CLAUDE: "YOUR_CLAUDE_API_KEY",  # 可选
    LLMProvider.OPENAI: "YOUR_OPENAI_API_KEY",  # 可选
}
```

### 4. 启动服务器

```bash
.\start.ps1
```

或直接运行：

```bash
python -m uvicorn server_fastapi:app --host 127.0.0.1 --port 8120
```

### 5. 访问应用

- **Web界面：** http://127.0.0.1:8120/
- **API文档：** http://127.0.0.1:8120/docs
- **记忆管理：** http://127.0.0.1:8120/memory.html

## 期末汇报演示入口

建议按 `docs/DEMO_SCRIPT.md` 的 3 分钟流程演示。核心输入：

```text
明天内分泌科复诊，空腹血糖8.2，最近夜里出汗，要带什么？
```

系统会同时展示：

- HYBRID 意图路由
- RAG 知识库命中
- 记忆写入
- 复诊材料清单
- 问诊问题提纲
- 主动提醒和家属摘要

安全边界演示输入：

```text
我胸痛、呼吸困难、脸色发白，现在怎么办？
```

---

## 🏗️ 项目架构

```
yipeibang/
├── server_fastapi.py          # FastAPI主服务器
├── server.py                  # 业务逻辑
├── index.html                 # 智能对话页面
├── memory.html                # 记忆管理页面
├── app.js                     # 前端JavaScript
│
├── styles/                    # 样式文件
│   ├── design-system.css     # 设计系统
│   ├── components.css        # 组件库
│   ├── main.css              # 主样式
│   └── centered-input.css    # 居中输入框
│
├── services/                  # 业务服务
│   ├── llm_service.py        # 统一LLM服务
│   ├── gemini_service.py     # Gemini专用服务
│   ├── rag_service.py        # 简单RAG检索
│   ├── semantic_search_service.py  # 语义搜索
│   ├── memory_service.py     # 智能记忆提取
│   └── reminder_service.py   # 定时提醒
│
├── utils/                     # 工具函数
│   └── database.py           # SQLite操作
│
├── data/                      # 数据文件
│   ├── yipeibang.db          # SQLite数据库
│   └── knowledge/            # 知识库
│       ├── medical_knowledge.json  # 100条医疗知识
│       └── embeddings.pkl    # 嵌入向量缓存
│
└── docs/                      # 文档
    ├── REFACTOR_PLAN.md      # 完整重构计划
    ├── PROGRESS.md           # 开发进度报告
    └── README.md             # 本文档
```

---

## 🔌 API接口

### 对话接口

#### POST `/api/chat/stream`
流式对话接口（SSE）

**请求体：**
```json
{
  "text": "空腹血糖正常范围是多少？",
  "provider": "gemini",
  "conversation_id": "conv_123"
}
```

**响应：** Server-Sent Events流

```
event: intent
data: {"route": "RAG", "keywords": ["血糖", "范围"]}

event: token
data: {"content": "空"}

event: done
data: {"conversation_id": "conv_123"}
```

### 记忆管理接口

#### GET `/api/memory/list`
获取记忆列表

**参数：**
- `user_id`: 用户ID（默认：default_user）
- `category`: 分类过滤（可选）

**响应：**
```json
{
  "memories": [
    {
      "id": "mem_abc123",
      "category": "个人信息",
      "content": "陈阿姨，65岁，2型糖尿病患者",
      "created_at": "2026-06-16T10:30:00"
    }
  ]
}
```

#### POST `/api/memory/create`
创建新记忆

**请求体：**
```json
{
  "category": "用药信息",
  "content": "每天服用二甲双胍500mg，一天三次"
}
```

#### DELETE `/api/memory/{memory_id}`
删除记忆

### LLM供应商接口

#### GET `/api/llm/providers`
获取可用的AI供应商列表

**响应：**
```json
{
  "providers": [
    {
      "id": "gemini",
      "name": "Gemini",
      "models": ["gemini-1.5-flash", "gemini-1.5-pro"],
      "default_model": "gemini-1.5-flash",
      "enabled": true
    }
  ]
}
```

---

## 💾 数据库设计

### 表结构

#### 1. conversations - 对话会话
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. messages - 对话消息
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    role TEXT,  -- 'user' or 'assistant'
    content TEXT,
    intent_data TEXT,  -- JSON格式的意图数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. memories - 记忆存储
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    category TEXT,  -- 分类
    key TEXT,       -- 用户ID或键
    value TEXT,     -- 记忆内容
    source TEXT,    -- 来源
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. reminders - 提醒任务
```sql
CREATE TABLE reminders (
    id TEXT PRIMARY KEY,
    type TEXT,  -- 'appointment', 'medication', 'custom'
    title TEXT,
    content TEXT,
    trigger_time TEXT,
    trigger_type TEXT,  -- 'once' or 'recurring'
    priority TEXT,  -- 'low', 'medium', 'high'
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🧠 知识库说明

### 知识库统计

- **总条数：** 100条
- **分类：**
  - 报告术语：25条
  - 用药指导：20条
  - 健康管理：18条
  - 就医流程：10条
  - 急救知识：12条
  - 检查指导：5条
  - 特殊人群：5条
  - 科室介绍：2条
  - 其他：3条

### 知识检索方式

1. **简单文本检索** - 关键词匹配（`rag_service.py`）
2. **语义搜索** - 使用sentence-transformers生成嵌入向量（`semantic_search_service.py`）
3. **混合搜索** - 语义搜索 + 关键词加权

### 嵌入模型

- **模型：** `paraphrase-multilingual-MiniLM-L12-v2`
- **维度：** 384
- **缓存：** `data/knowledge/embeddings.pkl`

---

## 🎨 UI设计系统

### 配色方案

```css
/* 主色调 */
--color-primary: #3B82F6;        /* 医疗蓝 */
--color-secondary: #14B8A6;      /* 治愈绿 */
--color-accent: #8B5CF6;         /* 强调紫 */

/* 背景色 */
--bg-primary: #FFFFFF;
--bg-secondary: #F9FAFB;
--bg-tertiary: #F3F4F6;

/* 文字色 */
--text-primary: #111827;
--text-secondary: #6B7280;
--text-tertiary: #9CA3AF;
```

### 圆角系统

```css
--radius-sm: 6px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-2xl: 20px;
```

### 阴影系统

```css
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
```

---

## 🔧 配置说明

### LLM供应商配置

编辑 `services/llm_service.py`：

```python
# API密钥
API_KEYS = {
    LLMProvider.GEMINI: "YOUR_API_KEY",
    LLMProvider.CLAUDE: "YOUR_API_KEY",
    LLMProvider.OPENAI: "YOUR_API_KEY",
}

# 模型选择
MODELS = {
    LLMProvider.GEMINI: {
        "default": "gemini-1.5-flash",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro"]
    }
}
```

### 系统提示词

编辑 `services/llm_service.py` 中的 `SYSTEM_PROMPT` 变量。

### 知识库更新

1. 编辑 `data/knowledge/medical_knowledge.json`
2. 删除 `data/knowledge/embeddings.pkl`（强制重新生成嵌入）
3. 重启服务器

---

## 📊 开发进度

### 已完成（80%）

- ✅ Day 1: UI设计系统
- ✅ Day 5-7: 多AI供应商集成
- ✅ Day 9: RAG知识库（100条）
- ✅ Day 10-12: 语义搜索（部分）
- ✅ Day 13-15: 智能记忆系统
- ✅ Day 16-18: 提醒系统（基础）

### 待完成（20%）

- ⏸️ ChromaDB向量数据库部署（因环境问题改用简化方案）
- ⏸️ 数据可视化（Chart.js图表）
- ⏸️ 浏览器通知API
- ⏸️ 演示数据完善
- ⏸️ 性能优化
- ⏸️ 单元测试

---

## 🚀 部署建议

### 开发环境

```bash
python server_fastapi.py
```

### 生产环境

```bash
uvicorn server_fastapi:app --host 0.0.0.0 --port 8120 --workers 4
```

### Docker部署（推荐）

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server_fastapi:app", "--host", "0.0.0.0", "--port", "8120"]
```

---

## 📚 参考资料

### 设计参考
- [Dribbble医疗设计](https://dribbble.com/tags/medical-app)
- [Healthcare UX Best Practices](https://eleken.co/blog-posts/user-interface-design-for-healthcare-applications)
- [ChatGPT界面设计](https://www.ideaplan.io/case-studies/chatgpt-conversational-design)

### 技术文档
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Google Gemini API](https://ai.google.dev/docs)
- [Sentence Transformers](https://www.sbert.net/)

---

## 📄 许可证

MIT License

---

## 👥 开发团队

- 项目负责人：Adasanxia
- 技术架构：Adasanxia
- 前端开发：Adasanxia
- 后端开发：Adasanxia

---

## 📞 联系方式

- 项目地址：D:\Adasanxia\智能应用系统开发\project\yipeibang
- 文档：`docs/` 目录

---

**最后更新：** 2026年6月16日
