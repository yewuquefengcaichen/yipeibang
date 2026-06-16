"""
FastAPI 主服务器
医陪帮智能应用系统
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import asyncio
import re
import os
import urllib.request
import urllib.error
from urllib.parse import urlsplit
from datetime import datetime
from typing import Optional

# 初始化FastAPI应用
app = FastAPI(title="医陪帮智能助手", version="2.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 项目根目录
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
STATE_FILE = DATA_DIR / "state.json"
AI_CONFIG_FILE = DATA_DIR / "api_config.json"

# 导入工具函数
from utils.database import (
    init_database, save_message, get_conversation_history,
    create_conversation, get_all_memories, save_memory,
    update_memory, delete_memory
)

# 导入RAG服务
from services.rag_service import search_knowledge, load_knowledge

# 导入统一LLM服务
from services.llm_service import (
    generate_stream as llm_generate_stream,
    get_available_providers,
    LLMProvider
)

# 初始化数据库和知识库
init_database()
load_knowledge()


DEMO_CASES = [
    {
        "id": "case-diabetes",
        "title": "糖尿病复诊准备",
        "patient": "陈阿姨，68岁，2型糖尿病",
        "scenario": "复诊材料、报告解读、问诊提纲、家属摘要",
        "prompt": "明天内分泌科复诊，空腹血糖8.2，最近夜里出汗，要带什么？",
        "tags": ["HYBRID", "记忆更新", "RAG", "清单生成"],
    },
    {
        "id": "case-emergency",
        "title": "胸痛急症安全拦截",
        "patient": "李叔叔，62岁，高血压史",
        "scenario": "识别高风险症状，停止普通问答，提示急救",
        "prompt": "我胸痛、呼吸困难、脸色发白，现在怎么办？",
        "tags": ["SAFE", "安全层", "风险预警"],
    },
    {
        "id": "case-pressure",
        "title": "高血压用药随访",
        "patient": "王先生，55岁，高血压",
        "scenario": "记录血压趋势，生成复查问题和用药提醒",
        "prompt": "最近三天血压150/96，头有点胀，帮我记录并提醒复查",
        "tags": ["ACTION", "主动服务", "趋势记录"],
    },
    {
        "id": "case-surgery",
        "title": "术后复查陪诊",
        "patient": "赵女士，45岁，甲状腺术后",
        "scenario": "整理复查材料、病理报告、下一步问题",
        "prompt": "甲状腺术后两周复查，需要带哪些资料，报告要问什么？",
        "tags": ["RAG", "复查清单", "问诊提纲"],
    },
    {
        "id": "case-child",
        "title": "儿童发热就诊准备",
        "patient": "6岁儿童，反复发热",
        "scenario": "整理体温曲线、用药记录、就诊科室建议",
        "prompt": "孩子反复发热两天，最高38.8，去医院前要准备什么？",
        "tags": ["HYBRID", "家属协同", "材料准备"],
    },
]


REQUIREMENT_MAP = [
    {
        "title": "目标用户分析与差异化",
        "score": 25,
        "detail": "聚焦老年慢病患者和陪诊家属，强调少填表、强提醒、家属同步、安全边界。",
    },
    {
        "title": "功能实现深度",
        "score": 30,
        "detail": "聊天即操作、长期记忆、RAG知识库、主动服务、病例样例和数据闭环全部可见。",
    },
    {
        "title": "智能特性现场演示",
        "score": 20,
        "detail": "用户说一句话，系统现场展示识别、检索、写入、提醒、摘要生成和安全拦截。",
    },
    {
        "title": "演示效果与表达",
        "score": 10,
        "detail": "按3分钟流程组织，不讲代码细节，直接展示核心价值。",
    },
    {
        "title": "用户验证与迭代",
        "score": 15,
        "detail": "保留真实用户反馈与改进入口，支持展示改进前后差异。",
    },
]


def read_state_file() -> dict:
    if STATE_FILE.exists():
        with STATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def calc_readiness(state: dict) -> dict:
    checklist = state.get("checklist", [])
    total = len(checklist)
    done = sum(1 for item in checklist if item.get("done"))
    return {"score": round(done / total * 100) if total else 0, "done": done, "total": total}


def visible_knowledge(limit: int = 12) -> list[dict]:
    items = []
    for query in ["空腹血糖", "糖化血红蛋白", "复诊材料", "胸痛", "高血压", "术后复查"]:
        for item in search_knowledge(query, top_k=2):
            key = item.get("content")
            if key and all(existing.get("content") != key for existing in items):
                items.append(item)
    return items[:limit]


def derive_memories(text: str, intent: dict) -> list[dict]:
    memories = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if "内分泌" in text:
        memories.append({"category": "个人信息", "key": "常用科室", "value": "内分泌科", "source": "对话抽取", "updatedAt": now})
    if "复诊" in text:
        memories.append({"category": "就医任务", "key": "近期任务", "value": "需要准备复诊材料和问诊提纲", "source": "对话抽取", "updatedAt": now})
    sugar = re.search(r"血糖\s*([0-9]+(?:\.[0-9]+)?)", text)
    if sugar:
        memories.append({"category": "指标记录", "key": "空腹血糖", "value": f"{sugar.group(1)} mmol/L", "source": "对话抽取", "updatedAt": now})
    if "夜里出汗" in text or "夜间出汗" in text or "出汗" in text:
        memories.append({"category": "风险关注", "key": "夜间出汗", "value": "复诊时询问低血糖相关处理", "source": "对话抽取", "updatedAt": now})
    if "家属" in text or "同步" in text:
        memories.append({"category": "协同偏好", "key": "家属同步", "value": "重要就医摘要同步给陪诊家属", "source": "用户输入", "updatedAt": now})
    if "晚上8点" in text or "晚8点" in text:
        memories.append({"category": "就医偏好", "key": "提醒偏好", "value": "复诊前一天晚上8点提醒", "source": "用户输入", "updatedAt": now})
    if intent.get("route") == "SAFE":
        memories = []
    return memories


def derive_actions(text: str, intent: dict) -> list[str]:
    if intent.get("route") == "SAFE":
        return ["触发急症安全拦截", "停止普通医疗建议生成", "保留原始描述供家属和医生查看"]
    if "chat" in intent.get("intents", []):
        return ["引导用户描述症状、报告或复诊需求"]
    if any(word in text for word in ["出汗", "头晕", "心慌", "恶心", "呕吐", "发热", "咳嗽", "胸闷", "乏力"]):
        return ["整理症状观察要点", "生成就医问诊问题", "写入症状关注记忆"]
    actions = []
    intents = set(intent.get("intents", []))
    if "prepare" in intents or "复诊" in text or "带什么" in text:
        actions.append("生成复诊材料清单")
        actions.append("生成问诊问题提纲")
    if "report" in intents or "血糖" in text or "糖化" in text or "尿酸" in text:
        actions.append("检索报告术语知识库")
        actions.append("整理指标解释和问医生的问题")
    if "followup" in intents or "提醒" in text:
        actions.append("创建复诊前主动提醒")
    if "family" in intents or "家属" in text or "同步" in text:
        actions.append("生成家属陪诊摘要")
    if not actions:
        actions.append("识别问题类型并返回就医准备建议")
    return actions


def compose_response(text: str, intent: dict, knowledge: list[dict], memories: list[dict], actions: list[str]) -> str:
    if intent.get("route") == "SAFE":
        return (
            "**安全提醒：这不是普通咨询场景**\n\n"
            "你描述了胸痛、呼吸困难、脸色发白等高风险症状。医陪帮不会在这种情况下给线上诊断或用药建议。\n\n"
            "1. 立即拨打120，或由家属陪同前往最近急诊。\n"
            "2. 让患者保持安静，避免自行走动和剧烈活动。\n"
            "3. 准备身份证、医保卡、既往病史、当前用药和过敏记录。\n"
            "4. 把刚才的原始描述给急救人员或急诊医生看。\n\n"
            "系统已经触发安全层拦截，优先保障生命安全。"
        )

    knowledge_lines = "\n".join([f"- {item['content']}" for item in knowledge[:2]]) or "- 暂未命中知识库，使用基础就医流程模板。"
    memory_lines = "\n".join([f"- {item['category']}：{item['key']} = {item['value']}" for item in memories]) or "- 本轮没有写入新的长期记忆。"
    action_lines = "\n".join([f"{idx}. {item}" for idx, item in enumerate(actions, 1)])

    if "血压" in text:
        return (
            "**高血压随访已整理**\n\n"
            "我把你的描述识别为血压趋势记录和复查提醒任务。150/96 属于需要重视的偏高记录，但具体处理要由医生结合病史判断。\n\n"
            f"**系统已执行**\n{action_lines}\n\n"
            "**建议带给医生的信息**\n"
            "1. 最近三天每次测量时间、血压值和心率。\n"
            "2. 是否头胀、胸闷、头晕，以及症状出现时间。\n"
            "3. 当前降压药名称、剂量和漏服情况。\n\n"
            "如果出现胸痛、呼吸困难、意识不清等情况，应立即急诊。"
        )

    if "术后" in text or "甲状腺" in text:
        return (
            "**术后复查陪诊清单已生成**\n\n"
            "复查重点不是只带报告，而是让医生能快速看到手术、病理、用药和恢复情况。\n\n"
            "1. 带出院小结、手术记录、病理报告、近期化验单和当前用药。\n"
            "2. 记录伤口恢复、声音变化、吞咽不适、手足麻木等症状。\n"
            "3. 问医生：复查项目、用药周期、下次复诊时间、哪些异常需要提前就医。\n\n"
            f"**知识库依据**\n{knowledge_lines}"
        )

    if "孩子" in text or "发热" in text:
        return (
            "**儿童发热就诊准备已整理**\n\n"
            "我会先帮助家属把信息整理清楚，方便医生判断病程，不直接给诊断。\n\n"
            "1. 记录体温曲线：测量时间、最高温、退热后变化。\n"
            "2. 带上已用药名称、剂量、时间，以及是否过敏。\n"
            "3. 观察精神状态、饮水、尿量、皮疹、咳嗽、腹泻等伴随症状。\n"
            "4. 若精神差、抽搐、呼吸困难、持续高热不退，应及时急诊。\n\n"
            f"**系统动作**\n{action_lines}"
        )

    return (
        "**复诊准备和报告问题已经整理好**\n\n"
        "我把你的话拆成了复诊准备、报告解读、风险关注和家属协同几个任务。这样演示时能看到：不是只回答文字，而是把对话变成数据和动作。\n\n"
        "**一、明天建议携带**\n"
        "1. 身份证、医保卡、就诊卡。\n"
        "2. 近7天血糖记录，最好标出空腹、餐后和夜间异常值。\n"
        "3. 上次检查报告，包括血糖、糖化血红蛋白、尿酸等。\n"
        "4. 当前用药清单，写清药名、剂量、服药时间，最好带药盒。\n"
        "5. 问诊问题提纲：夜间出汗、低血糖处理、复查周期和控制目标。\n\n"
        "**二、这次要重点问医生**\n"
        "1. 空腹血糖偏高时，个人控制目标应该是多少。\n"
        "2. 夜里出汗是否需要记录当时血糖，是否和低血糖风险有关。\n"
        "3. 当前用药和晚餐安排是否需要由医生评估调整。\n"
        "4. 下次复查前需要提前做哪些检查。\n\n"
        f"**三、知识库依据**\n{knowledge_lines}\n\n"
        f"**四、本轮记忆写入**\n{memory_lines}\n\n"
        f"**五、系统已触发动作**\n{action_lines}\n\n"
        "以上内容用于复诊准备和沟通辅助，不替代医生诊断或处方。"
    )


def chunk_text(text: str, size: int = 18) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)]


DEFAULT_AI_CONFIG = {
    "active_provider": "anyrouter",
    "providers": {
        "anyrouter": {
            "id": "anyrouter",
            "name": "AnyRouter",
            "base_url": "https://anyrouter.top",
            "api_key": "sk-FPY8UpvAtZw08mhZvJ3J5cFwxjRtkXmsDGlfqTnRsmUDhAjO",
            "model": "gpt-5.5",
            "models": ["gpt-5.5"],
            "enabled": True,
            "built_in": True,
        },
        "elysia": {
            "id": "elysia",
            "name": "Elysia",
            "base_url": "https://elysia.h-e.top",
            "api_key": "sk-X3w6yf3d3zz04E5LQPgUe0yaC111KuYcQO6zYXMRJSa0VAcW",
            "model": "deepseek-v4-pro",
            "models": ["deepseek-v4-pro"],
            "enabled": True,
            "built_in": True,
        },
        "windhub": {
            "id": "windhub",
            "name": "Windhub备用",
            "base_url": "https://windhub.cc",
            "api_key": "sk-icuT5guhhvteUPS60PpGoNv7L0k12QxSfbaPxkA8d21hyaRv",
            "model": "deepseek-v3-2-251201",
            "models": ["deepseek-v3-2-251201"],
            "enabled": True,
            "built_in": True,
        },
        "custom": {
            "id": "custom",
            "name": "自定义",
            "base_url": "",
            "api_key": "",
            "model": "",
            "models": [],
            "enabled": False,
            "built_in": False,
        },
    },
}


def masked_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 10:
        return "已配置"
    return f"{api_key[:5]}...{api_key[-4:]}"


def api_root(base_url: str) -> str:
    base = (base_url or "").strip().rstrip("/")
    if not base:
        return ""
    return base if base.endswith("/v1") else f"{base}/v1"


def request_headers(provider: dict) -> dict:
    base = (provider.get("base_url") or "").strip().rstrip("/")
    parsed = urlsplit(base)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else base
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {provider.get('api_key', '')}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
        "Accept": "application/json,text/event-stream,*/*",
        "Origin": origin,
        "Referer": origin + "/" if origin else "",
    }


def merge_provider(default_provider: dict, saved_provider: dict) -> dict:
    merged = {**default_provider, **(saved_provider or {})}
    merged["id"] = merged.get("id") or default_provider.get("id")
    merged["name"] = merged.get("name") or default_provider.get("name") or merged["id"]
    merged["models"] = merged.get("models") or ([merged["model"]] if merged.get("model") else [])
    merged["enabled"] = bool(merged.get("enabled", True))
    return merged


def normalize_ai_config(raw: dict | None = None) -> dict:
    config = json.loads(json.dumps(DEFAULT_AI_CONFIG, ensure_ascii=False))
    raw = raw or {}
    if "providers" not in raw:
        legacy = {
            "id": "windhub",
            "name": "Windhub备用",
            "base_url": raw.get("base_url", "https://windhub.cc"),
            "api_key": raw.get("api_key", ""),
            "model": raw.get("model", "deepseek-v3-2-251201"),
            "models": [raw.get("model", "deepseek-v3-2-251201")],
            "enabled": True,
            "built_in": True,
        }
        raw = {"active_provider": "anyrouter", "providers": {"windhub": legacy}}
    for provider_id, provider in raw.get("providers", {}).items():
        default_provider = config["providers"].get(provider_id, {"id": provider_id, "name": provider.get("name", provider_id)})
        config["providers"][provider_id] = merge_provider(default_provider, provider)
    active = raw.get("active_provider") or config.get("active_provider")
    if active not in config["providers"] or not config["providers"][active].get("enabled"):
        active = next((pid for pid, item in config["providers"].items() if item.get("enabled")), "anyrouter")
    config["active_provider"] = active
    return config


def load_ai_config() -> dict:
    raw = {}
    if AI_CONFIG_FILE.exists():
        with AI_CONFIG_FILE.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    config = normalize_ai_config(raw)
    env_key = os.getenv("WINDHUB_API_KEY")
    if env_key:
        config["providers"]["windhub"]["api_key"] = env_key
    return config


def save_ai_config(config: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with AI_CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(normalize_ai_config(config), f, ensure_ascii=False, indent=2)


def public_provider(provider: dict) -> dict:
    return {
        "id": provider.get("id"),
        "name": provider.get("name"),
        "base_url": provider.get("base_url", ""),
        "model": provider.get("model", ""),
        "models": provider.get("models", []),
        "enabled": bool(provider.get("enabled")),
        "built_in": bool(provider.get("built_in")),
        "api_key_set": bool(provider.get("api_key")),
        "api_key_preview": masked_key(provider.get("api_key", "")),
    }


def fetch_provider_models(provider: dict) -> list[str]:
    if not provider.get("base_url") or not provider.get("api_key"):
        raise RuntimeError("请先填写 Base URL 和 API Key")
    endpoint = api_root(provider["base_url"]) + "/models"
    request = urllib.request.Request(endpoint, headers=request_headers(provider), method="GET")
    with urllib.request.urlopen(request, timeout=25) as response:
        data = json.loads(response.read().decode("utf-8"))
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        models = [item.get("id") or item.get("name") for item in data["data"] if isinstance(item, dict)]
    elif isinstance(data, dict) and isinstance(data.get("models"), list):
        models = [item.get("id") if isinstance(item, dict) else str(item) for item in data["models"]]
    elif isinstance(data, list):
        models = [item.get("id") if isinstance(item, dict) else str(item) for item in data]
    else:
        models = []
    models = sorted({model for model in models if model})
    if not models:
        raise RuntimeError("模型接口没有返回可用模型")
    return models


def call_provider_chat(provider: dict, user_message: str, conversation_id: str, knowledge: list[dict], memories: list[dict]) -> str:
    api_key = provider.get("api_key", "")
    model = provider.get("model", "")
    if not api_key:
        raise RuntimeError(f"{provider.get('name', '供应商')} 未配置 API Key")
    if not provider.get("base_url") or not model:
        raise RuntimeError(f"{provider.get('name', '供应商')} 未配置 URL 或模型")

    endpoint = api_root(provider["base_url"]) + "/chat/completions"
    history = get_conversation_history(conversation_id, limit=8)
    history_messages = [
        {"role": item["role"], "content": item["content"]}
        for item in history
        if item.get("role") in {"user", "assistant"} and item.get("content")
    ]
    if user_message.strip().lower() in {"hi", "hello", "hey"} or user_message.strip() in {"你好", "您好", "在吗"}:
        history_messages = []
    knowledge_text = "\n".join([f"- {item.get('category', '知识')}：{item.get('content', '')}" for item in knowledge[:4]])
    memory_text = "\n".join([f"- {item.get('key', item.get('category', '记忆'))}：{item.get('value', item.get('content', ''))}" for item in memories[:8]])
    system_prompt = (
        "你是医陪帮，一个面向慢病患者和陪诊家属的中文就医助手。"
        "你需要像真实产品一样自然回答，优先解决用户当下问题。"
        "可以解释检查指标、整理复诊材料、生成问医生的问题、提醒家属协同。"
        "医疗安全要求：不做诊断，不开处方，不给药物剂量调整结论；遇到胸痛、呼吸困难、意识不清、大出血、抽搐等急症，优先建议立即拨打120或急诊。"
        "必须以最后一条用户消息为准，历史对话只能作为背景参考，不能拿上一轮问题来替代当前问题。"
        "如果最后一条只是问候或闲聊，应简短回应并引导用户输入就医问题。"
        "回答要具体、分点、可执行，不要说自己是模板，不要提课堂、作业、评分标准。"
    )
    context_prompt = (
        f"可参考的知识库内容：\n{knowledge_text or '暂无'}\n\n"
        f"用户长期记忆：\n{memory_text or '暂无'}"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": context_prompt},
            *history_messages,
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.35,
        "max_tokens": 1400,
        "stream": False,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=request_headers(provider),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def provider_order(config: dict, provider_id: str | None = None, model: str | None = None) -> list[dict]:
    providers = config["providers"]
    ordered_ids = []
    preferred = provider_id or config.get("active_provider")
    if preferred in providers:
        ordered_ids.append(preferred)
    for pid, item in providers.items():
        if pid not in ordered_ids and item.get("enabled"):
            ordered_ids.append(pid)
    ordered = []
    for pid in ordered_ids:
        item = dict(providers[pid])
        if pid == preferred and model:
            item["model"] = model
        if item.get("enabled") and item.get("base_url") and item.get("api_key") and item.get("model"):
            ordered.append(item)
    return ordered


def persist_memories(memories: list[dict]) -> None:
    for item in memories:
        key = item.get("key") or item.get("category") or "记忆"
        value = item.get("value") or item.get("content") or ""
        if not value:
            continue
        save_memory(
            user_id="default_user",
            category=item.get("category", "对话记忆"),
            content=f"{key}：{value}",
            source=item.get("source", "对话抽取"),
        )


def update_conversation_title(conversation_id: str, user_message: str) -> None:
    from utils.database import get_connection

    title = re.sub(r"\s+", " ", user_message).strip()
    if len(title) > 22:
        title = title[:22] + "..."
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND (title IS NULL OR title = '新对话')",
        (title or "新对话", conversation_id),
    )
    conn.commit()
    conn.close()


def list_conversations(limit: int = 30) -> list[dict]:
    from utils.database import get_connection, dict_from_row

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, message_count, created_at, updated_at FROM conversations WHERE message_count > 0 ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    )
    rows = [dict_from_row(row) for row in cursor.fetchall()]
    for row in rows:
        if not row.get("title") or row.get("title") == "新对话":
            cursor.execute(
                "SELECT content FROM messages WHERE conversation_id = ? AND role = 'user' ORDER BY created_at ASC LIMIT 1",
                (row["id"],),
            )
            first = cursor.fetchone()
            if first and first["content"]:
                title = re.sub(r"\s+", " ", first["content"]).strip()
                row["title"] = title[:22] + ("..." if len(title) > 22 else "")
    conn.close()
    deduped = []
    seen_titles = set()
    for row in rows:
        title = row.get("title") or "新对话"
        if title in seen_titles:
            continue
        seen_titles.add(title)
        deduped.append(row)
        if len(deduped) >= 10:
            break
    return deduped


# ========== 健康检查 ==========
@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/app-data")
async def get_app_data():
    """前端工作台所需演示数据"""
    state = read_state_file()
    db_memories = get_all_memories()
    return {
        "cases": DEMO_CASES,
        "knowledge": visible_knowledge(),
        "memories": db_memories or state.get("memory", []),
        "conversations": list_conversations(),
        "reminders": [
            {
                "type": "复诊提醒",
                "title": "明天09:30内分泌科复诊",
                "content": "08:50到院，带血糖记录、报告、用药清单。",
                "triggerTime": "今天20:00",
                "priority": "high",
            },
            {
                "type": "材料准备",
                "title": "就医材料完整度67%",
                "content": "缺少用药清单、问诊提纲、空腹确认。",
                "triggerTime": "今天18:30",
                "priority": "medium",
            },
            {
                "type": "家属同步",
                "title": "陪诊摘要待发送",
                "content": "自动整理给陈先生，减少反复沟通。",
                "triggerTime": "就诊前",
                "priority": "medium",
            },
        ],
        "requirements": REQUIREMENT_MAP,
        "readiness": calc_readiness(state),
    }


@app.get("/api/conversations")
async def get_conversations():
    """获取历史对话列表"""
    return {"conversations": list_conversations()}


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """获取单个对话消息"""
    return {"conversation_id": conversation_id, "messages": get_conversation_history(conversation_id, limit=80)}


# ========== 状态接口（兼容旧版） ==========
@app.get("/api/state")
async def get_state():
    """获取患者状态（兼容旧版API）"""
    state_file = STATE_FILE
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"error": "State file not found"}


# ========== 对话接口（传统非流式） ==========
@app.post("/api/chat")
async def chat(request: Request):
    """传统非流式对话接口"""
    payload = await request.json()
    user_message = payload.get("text", "").strip()
    provider_id = payload.get("provider_id")
    requested_model = payload.get("model")

    if not user_message:
        return {"error": "消息不能为空"}

    # 创建或获取会话ID
    conversation_id = payload.get("conversation_id") or create_conversation()

    # 意图识别
    from server import route_intent, generate_response
    intent_result = route_intent(user_message)

    # 生成回复
    response_text = generate_response(user_message, intent_result)

    # 保存消息
    save_message(conversation_id, "user", user_message)
    save_message(conversation_id, "assistant", response_text, intent_result)

    return {
        "message": response_text,
        "intent": intent_result,
        "conversation_id": conversation_id
    }


# ========== 记忆管理接口 ==========
@app.get("/api/memory/list")
async def list_memories(user_id: str = "default_user", category: Optional[str] = None):
    """获取记忆列表"""
    from utils.database import get_memories
    memories = get_memories(user_id, category)
    return {"memories": memories}


@app.post("/api/memory/create")
async def create_memory(request: Request):
    """创建新记忆"""
    from utils.database import save_memory
    data = await request.json()

    memory_id = save_memory(
        user_id=data.get("user_id", "default_user"),
        category=data.get("category", "其他"),
        content=data.get("content", ""),
        conversation_id=data.get("conversation_id")
    )

    return {"id": memory_id, "success": True}


@app.delete("/api/memory/{memory_id}")
async def delete_memory(memory_id: str):
    """删除记忆"""
    from utils.database import delete_memory
    success = delete_memory(memory_id)
    return {"success": success}


@app.get("/api/memory/search")
async def search_memories(query: str, user_id: str = "default_user", top_k: int = 5):
    """搜索相关记忆"""
    from services.memory_service import get_relevant_memories
    memories = get_relevant_memories(query, user_id, top_k)
    return {"memories": memories}


# ========== 获取可用的LLM供应商列表 ==========
@app.get("/api/llm/providers")
async def get_providers():
    """获取所有可用的LLM供应商和模型"""
    providers = get_available_providers()
    return {"providers": providers}


@app.get("/api/providers")
async def get_api_providers():
    """获取前端模型设置所需的供应商配置，不返回明文 Key。"""
    config = load_ai_config()
    return {
        "active_provider": config["active_provider"],
        "providers": [public_provider(provider) for provider in config["providers"].values()],
    }


@app.post("/api/providers/select")
async def select_api_provider(request: Request):
    """切换当前供应商和模型。"""
    data = await request.json()
    provider_id = data.get("provider_id")
    model = (data.get("model") or "").strip()
    config = load_ai_config()
    if provider_id not in config["providers"]:
        return JSONResponse({"error": "供应商不存在"}, status_code=404)
    provider = config["providers"][provider_id]
    provider["enabled"] = True
    if model:
        provider["model"] = model
        if model not in provider.get("models", []):
            provider.setdefault("models", []).append(model)
    config["active_provider"] = provider_id
    save_ai_config(config)
    return {"success": True, "active_provider": provider_id, "provider": public_provider(provider)}


@app.post("/api/providers/save")
async def save_api_provider(request: Request):
    """保存或更新供应商配置。空 Key 表示沿用原 Key。"""
    data = await request.json()
    provider_id = re.sub(r"[^a-zA-Z0-9_-]", "", data.get("id") or data.get("provider_id") or "custom") or "custom"
    config = load_ai_config()
    existing = config["providers"].get(provider_id, {"id": provider_id, "name": provider_id, "models": []})
    provider = {**existing}
    provider["id"] = provider_id
    provider["name"] = (data.get("name") or existing.get("name") or provider_id).strip()
    provider["base_url"] = (data.get("base_url") or existing.get("base_url") or "").strip().rstrip("/")
    if data.get("api_key"):
        provider["api_key"] = data.get("api_key").strip()
    else:
        provider["api_key"] = existing.get("api_key", "")
    provider["model"] = (data.get("model") or existing.get("model") or "").strip()
    incoming_models = data.get("models") if isinstance(data.get("models"), list) else existing.get("models", [])
    provider["models"] = sorted({str(item).strip() for item in incoming_models if str(item).strip()})
    if provider["model"] and provider["model"] not in provider["models"]:
        provider["models"].append(provider["model"])
    provider["enabled"] = bool(data.get("enabled", True))
    provider["built_in"] = bool(existing.get("built_in", False))
    config["providers"][provider_id] = provider
    if data.get("set_active", True):
        config["active_provider"] = provider_id
    save_ai_config(config)
    return {"success": True, "active_provider": config["active_provider"], "provider": public_provider(provider)}


@app.get("/api/providers/{provider_id}/models")
async def get_provider_models(provider_id: str):
    """从当前供应商拉取模型列表并缓存。"""
    config = load_ai_config()
    if provider_id not in config["providers"]:
        return JSONResponse({"error": "供应商不存在"}, status_code=404)
    provider = config["providers"][provider_id]
    try:
        models = fetch_provider_models(provider)
        provider["models"] = models
        if not provider.get("model") or provider["model"] not in models:
            provider["model"] = models[0]
        config["providers"][provider_id] = provider
        save_ai_config(config)
        return {"success": True, "models": models, "provider": public_provider(provider)}
    except Exception as error:
        return JSONResponse(
            {"success": False, "error": str(error), "models": provider.get("models", []), "provider": public_provider(provider)},
            status_code=502,
        )


# ========== 流式对话接口（SSE + 多供应商LLM） ==========
@app.post("/api/chat/stream")
async def chat_stream(request: Request):
    """流式对话接口 - 支持多个LLM供应商"""

    payload = await request.json()
    user_message = payload.get("text", "").strip()
    provider_id = payload.get("provider_id")
    requested_model = payload.get("model")

    if not user_message:
        return JSONResponse({"error": "消息不能为空"}, status_code=400)

    conversation_id = payload.get("conversation_id") or create_conversation()

    async def event_generator():
        """SSE事件生成器"""
        try:
            from server import route_intent

            intent_result = route_intent(user_message)
            knowledge_results = []
            if intent_result["route"] in {"RAG", "HYBRID"} or any(word in user_message for word in ["报告", "血糖", "糖化", "尿酸", "胸痛", "复诊", "术后", "发热", "血压"]):
                knowledge_results = search_knowledge(user_message, top_k=4)
                if not knowledge_results:
                    knowledge_results = visible_knowledge(4)
            memories = derive_memories(user_message, intent_result)
            actions = derive_actions(user_message, intent_result)

            for event_name, data in [
                ("intent", intent_result),
                ("thinking", {"step": "规则层、RAG层、记忆层、安全层协同判断", "status": "done"}),
                ("knowledge", {"results": knowledge_results}),
                ("memory", {"memories": memories}),
                ("action", {"actions": actions}),
            ]:
                yield f"event: {event_name}\n"
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.08)

            source = "fallback"
            used_provider = None
            used_model = None
            api_errors = []
            try:
                config = load_ai_config()
                for provider in provider_order(config, provider_id, requested_model):
                    yield "event: thinking\n"
                    yield f"data: {json.dumps({'step': '正在连接' + provider.get('name', provider.get('id', '模型服务')), 'status': 'running'}, ensure_ascii=False)}\n\n"
                    try:
                        response_text = await asyncio.to_thread(
                            call_provider_chat,
                            provider,
                            user_message,
                            conversation_id,
                            knowledge_results,
                            memories,
                        )
                        source = "api"
                        used_provider = provider.get("id")
                        used_model = provider.get("model")
                        break
                    except Exception as provider_error:
                        api_errors.append(f"{provider.get('name', provider.get('id'))}: {provider_error}")
                        print(f"Provider API error: {api_errors[-1]}")
                        yield "event: thinking\n"
                        yield f"data: {json.dumps({'step': provider.get('name', provider.get('id', '模型服务')) + '暂不可用，正在切换备用通道', 'status': 'retry'}, ensure_ascii=False)}\n\n"
                else:
                    raise RuntimeError("；".join(api_errors) or "没有可用 API 供应商")
            except Exception as api_error:
                print(f"LLM API fallback: {api_error}")
                yield "event: thinking\n"
                yield f"data: {json.dumps({'step': '正在使用本地安全策略完成回答', 'status': 'fallback'}, ensure_ascii=False)}\n\n"
                response_text = compose_response(user_message, intent_result, knowledge_results, memories, actions)

            full_response = ""
            for chunk in chunk_text(response_text, size=12):
                full_response += chunk
                yield "event: token\n"
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.035)

            update_conversation_title(conversation_id, user_message)
            save_message(conversation_id, "user", user_message)
            save_message(conversation_id, "assistant", full_response, intent_result)
            persist_memories(memories)

            yield "event: done\n"
            yield f"data: {json.dumps({'conversation_id': conversation_id, 'intent': intent_result, 'actions': actions, 'source': source, 'provider': used_provider, 'model': used_model}, ensure_ascii=False)}\n\n"

        except Exception as e:
            print(f"Stream error: {e}")
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ========== 对话历史 ==========
@app.get("/api/chat/history/{conversation_id}")
async def get_history(conversation_id: str, limit: int = 50):
    """获取对话历史"""
    messages = get_conversation_history(conversation_id, limit)
    return {"messages": messages}


# ========== 记忆管理 ==========
@app.get("/api/memories")
async def get_memories(category: Optional[str] = None):
    """获取所有记忆"""
    memories = get_all_memories(category)
    return {"memories": memories}


@app.post("/api/memories")
async def create_memory(request: Request):
    """创建新记忆"""
    data = await request.json()
    memory_id = save_memory(
        category=data['category'],
        key=data['key'],
        value=data['value'],
        source=data.get('source', '用户输入')
    )
    return {"id": memory_id, "status": "created"}


@app.put("/api/memories/{memory_id}")
async def update_memory_api(memory_id: str, request: Request):
    """更新记忆"""
    data = await request.json()
    update_memory(memory_id, data['value'])
    return {"status": "updated"}


@app.delete("/api/memories/{memory_id}")
async def delete_memory_api(memory_id: str):
    """删除记忆"""
    delete_memory(memory_id)
    return {"status": "deleted"}


# ========== 提醒管理 ==========
@app.get("/api/reminders")
async def get_reminders(status: Optional[str] = None):
    """获取提醒列表"""
    from utils.database import get_connection, dict_from_row

    conn = get_connection()
    cursor = conn.cursor()

    if status:
        cursor.execute("SELECT * FROM reminders WHERE status = ? ORDER BY trigger_time DESC", (status,))
    else:
        cursor.execute("SELECT * FROM reminders ORDER BY trigger_time DESC LIMIT 50")

    reminders = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()

    return {"reminders": reminders}


@app.post("/api/reminders/{reminder_id}/mark-read")
async def mark_reminder_read_api(reminder_id: str):
    """标记提醒为已读"""
    from utils.database import mark_reminder_read
    mark_reminder_read(reminder_id)
    return {"status": "marked as read"}


@app.get("/api/reminders/stats")
async def get_reminder_stats():
    """获取提醒统计"""
    from utils.database import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM reminders")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) as unread FROM reminders WHERE status = 'pending'")
    unread = cursor.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "unread": unread
    }


# ========== 静态文件服务 ==========
@app.get("/")
async def serve_index():
    """返回首页"""
    return FileResponse(str(ROOT / "index.html"))

@app.get("/{file_path:path}")
async def serve_static_file(file_path: str):
    """返回静态文件"""
    file = ROOT / file_path
    if file.exists() and file.is_file():
        return FileResponse(str(file))
    return JSONResponse({"error": "File not found"}, status_code=404)


# ========== 启动信息 ==========
@app.on_event("startup")
async def startup_event():
    """启动时执行"""
    print("=" * 60)
    print("医陪帮智能助手 v2.0 - FastAPI后端")
    print("=" * 60)
    print(f"Server running at: http://127.0.0.1:8120")
    print(f"Database: {ROOT / 'data' / 'yipeibang.db'}")
    print(f"API Docs: http://127.0.0.1:8120/docs")
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8120, log_level="info")
