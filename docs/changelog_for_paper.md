# 课程论文变更记录

## 架构改进

- 从单页问答改为 FastAPI + SQLite + JSON 知识库的闭环健康助手。
- 增加规则/RAG/LLM/安全四层路由，输出 `action_trace`。
- 增加健康记录、提醒、动作日志三类运行时表。
- API Key 从仓库默认值移除，改为页面配置、环境变量或本地忽略配置。

## 智能特性

- SSE 流式输出：`thinking`、`token`、`action`、`done`。
- 意图识别：ACTION、HYBRID、RAG、SAFE。
- 长期记忆：从对话提取科室、风险关注、就医任务、提醒偏好。
- RAG：结构化知识命中后进入回答上下文。
- 主动服务：复诊、提醒、家属同步语义可创建提醒。
- 安全分层：胸痛、呼吸困难、意识异常、大出血、抽搐、卒中信号等触发 SAFE。

## 数据改进

- `data/cases.json`：12 个病例，覆盖夜汗低血糖、糖尿病复诊、高血压随访、胸痛急症等。
- `data/knowledge.json`：46 条五类知识，包含红旗、记录字段、何时就医、来源。
- `data/media_sources.json`：记录本地图片来源和 PMC/CDC PHIL 参考来源。

## UI 改进

- 温暖可信医疗风格：奶白、浅青、暖金、医疗蓝。
- 组件：Button、Badge、Toast、Dialog、Card、Tabs、Timeline、Checklist、RiskAlert、ActionTrace、SourcePanel。
- 移动端适配，输入框固定悬浮，候选问题可复制/发送。
- 侧栏包含新建对话、历史、档案、知识库、健康记录、提醒、模型设置、演示路线。

