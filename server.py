from __future__ import annotations

import argparse
import json
import mimetypes
import re
import socket
import time
import webbrowser
from copy import deepcopy
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
STATE_FILE = DATA_DIR / "state.json"
CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"
REMINDERS_FILE = DATA_DIR / "reminders.json"

RISK_WORDS = ["胸痛", "呼吸困难", "昏迷", "意识不清", "大出血", "抽搐", "剧烈头痛"]
SYMPTOM_WORDS = ["恶心", "呕吐", "头晕", "出汗", "夜间出汗", "心慌", "发热", "咳嗽", "胸闷", "乏力", "腹痛"]

BASE_STATE = {
    "patient": {
        "name": "陈阿姨",
        "age": 68,
        "case": "糖尿病复诊",
        "hospital": "南方医院",
        "department": "内分泌科",
        "visitTime": "明天 09:30",
        "arriveAdvice": "建议 08:50 到院",
    },
    "memory": [
        {"id": "mem001", "category": "个人信息", "key": "常去医院", "value": "南方医院", "source": "系统推断", "updatedAt": "2024-06-15 10:00"},
        {"id": "mem002", "category": "个人信息", "key": "常用科室", "value": "内分泌科", "source": "系统推断", "updatedAt": "2024-06-15 10:00"},
        {"id": "mem003", "category": "个人信息", "key": "家属联系人", "value": "陈先生", "source": "用户输入", "updatedAt": "2024-06-15 10:00"},
        {"id": "mem004", "category": "就医偏好", "key": "提醒偏好", "value": "提前一天晚 8 点", "source": "用户输入", "updatedAt": "2024-06-15 10:00"},
        {"id": "mem005", "category": "注意事项", "key": "空腹要求", "value": "抽血前确认空腹要求", "source": "系统推断", "updatedAt": "2024-06-15 10:00"},
        {"id": "mem006", "category": "注意事项", "key": "低血糖风险", "value": "需要记录当时血糖", "source": "系统推断", "updatedAt": "2024-06-15 10:00"},
    ],
    "checklist": [
        {"id": "idcard", "title": "身份证、医保卡、就诊卡", "detail": "挂号、缴费、取药都要用", "done": True, "tag": "必带"},
        {"id": "record", "title": "近 7 天血糖记录", "detail": "空腹、餐后和夜间异常值单独标记", "done": True, "tag": "已准备"},
        {"id": "report", "title": "上次检查报告", "detail": "血糖、糖化血红蛋白、尿酸报告", "done": True, "tag": "已准备"},
        {"id": "medicine", "title": "当前用药清单", "detail": "药名、剂量、服药时间，最好带药盒", "done": False, "tag": "缺少"},
        {"id": "question", "title": "问诊问题提纲", "detail": "夜间出汗、低血糖处理、复查周期", "done": False, "tag": "待生成"},
        {"id": "fasting", "title": "空腹提醒", "detail": "抽血前按医嘱保持空腹，低血糖风险需留意", "done": False, "tag": "需确认"},
    ],
    "timeline": [
        {"date": "明天 08:50", "title": "到达医院", "text": "先取号，再去检验科抽血；陪诊人检查材料清单。"},
        {"date": "明天 09:30", "title": "内分泌科复诊", "text": "带上血糖记录和用药清单，按问诊提纲向医生确认。"},
        {"date": "3 天后", "title": "整理医嘱", "text": "把医生调整的用药、饮食和复查时间写入家属共享记录。"},
        {"date": "30 天后", "title": "复查提醒", "text": "提前一天提醒空腹要求、报告单和挂号信息。"},
    ],
    "familyNote": "明天带上血糖记录本，早餐先不要吃，抽血后再按医生建议用餐。",
    "lastSync": "今天 20:10",
}

KNOWLEDGE_BASE = {
    "内分泌科": [
        "复诊常见材料包括身份证、医保卡、历史检查报告、近期指标记录、当前用药清单。",
        "抽血是否需要空腹应以医院检查要求和医生说明为准，低血糖风险患者需要特别确认。",
        "糖尿病复诊时，连续血糖记录比单次口头描述更方便医生判断近期控制情况。",
    ],
    "报告术语": [
        "空腹血糖用于反映空腹状态下血糖水平，具体控制目标需要结合年龄和病情由医生判断。",
        "糖化血红蛋白通常反映近 2-3 个月血糖控制情况，不能只看一次指尖血糖。",
        "尿酸升高可能与饮食、代谢和用药有关，是否需要处理应咨询医生。",
    ],
    "安全边界": [
        "系统不提供诊断、处方、用药调整结论。",
        "出现胸痛、呼吸困难、昏迷、意识不清等情况，应尽快就医或拨打急救电话。",
    ],
}


def is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def find_port(start: int) -> int:
    port = start
    while not is_port_free(port):
        port += 1
    return port


def ensure_state() -> dict:
    DATA_DIR.mkdir(exist_ok=True)
    if not STATE_FILE.exists():
        save_state(deepcopy(BASE_STATE))
    return load_state()


def load_state() -> dict:
    if not STATE_FILE.exists():
        return deepcopy(BASE_STATE)
    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def readiness(checklist: list[dict]) -> dict:
    total = len(checklist)
    done = sum(1 for item in checklist if item.get("done"))
    score = round(done / total * 100) if total else 0
    return {"score": score, "missing": total - done, "done": done, "total": total}


def has_risk(text: str) -> list[str]:
    return [word for word in RISK_WORDS if word in text]


def route_intent(text: str) -> dict:
    text = text.strip()
    if text.lower() in {"hi", "hello", "hey"} or text in {"你好", "您好", "在吗"}:
        return {
            "route": "ACTION",
            "title": "对话引导",
            "summary": "识别到问候，系统将引导用户输入就医问题。",
            "intents": ["chat"],
            "actions": ["简短回应并引导用户描述症状、报告或复诊需求。"],
            "layers": ["规则层", "对话层"],
            "keywords": ["问候"],
            "scores": {"chat": 1},
            "reason": "检测到问候语，进入对话引导模式。"
        }
    risks = has_risk(text)
    if risks:
        return {
            "route": "SAFE",
            "title": "安全层拦截",
            "riskWords": risks,
            "keywords": risks,
            "summary": "识别到高风险表达，系统不做线上判断。",
            "reason": f"检测到{len(risks)}个高风险词：{'、'.join(risks)}，触发安全层拦截。",
            "actions": [
                "提示立即联系医院急诊或拨打 120。",
                "保留用户原始描述，方便家属和医生查看。",
                "停止生成诊断、处方或用药调整建议。",
            ],
            "layers": ["安全层", "人工确认"],
            "scores": {}
        }

    keyword_map = {
        "prepare": ["带什么", "准备", "材料", "复诊", "挂号", "陪诊"],
        "report": ["报告", "指标", "血糖", "糖化", "尿酸", "看不懂"],
        "followup": ["提醒", "复查", "下次", "时间", "预约"],
        "family": ["家属", "同步", "陪诊人", "分享"],
        "symptom": SYMPTOM_WORDS,
    }

    scores = {}
    matched_keywords = []
    for intent, keywords in keyword_map.items():
        score = count_words(text, keywords)
        scores[intent] = score
        if score > 0:
            matched_keywords.extend([kw for kw in keywords if kw in text])

    selected = [name for name, score in scores.items() if score > 0]
    route = "HYBRID" if len(selected) >= 2 else "ACTION"
    if "report" in selected and len(selected) == 1:
        route = "RAG"
    if not selected:
        selected = ["symptom"]
        route = "ACTION"
        matched_keywords = ["问诊"]

    action_map = {
        "prepare": "生成就医材料清单、到院时间和问诊提纲。",
        "report": "检索报告术语库，把指标整理成问医生的问题。",
        "followup": "写入复诊时间线，并按提醒偏好推送。",
        "family": "同步陪诊摘要给家属联系人。",
        "symptom": "整理症状观察要点、危险信号和就医沟通问题。",
    }

    # 生成决策理由
    reason = f"检测到 {len(selected)} 个意图："
    for intent in selected:
        reason += f" {intent}（得分{scores[intent]}）"
    if route == "HYBRID":
        reason += "。多个意图并存，使用HYBRID混合模式。"
    elif route == "RAG":
        reason += "。纯知识检索任务，使用RAG模式。"
    else:
        reason += "。单一操作任务，使用ACTION模式。"

    return {
        "route": route,
        "title": "意图识别结果",
        "summary": "根据自然语言输入，系统把请求拆成可执行动作。",
        "intents": selected,
        "actions": [action_map[name] for name in selected],
        "layers": ["规则层", "知识库/RAG", "长期记忆", "安全层"],
        "keywords": list(set(matched_keywords)),
        "scores": scores,
        "reason": reason
    }


def count_words(text: str, words: list[str]) -> int:
    return sum(1 for word in words if word in text)


def prepare_plan(payload: dict) -> dict:
    scenario = payload.get("scenario") or "复诊"
    dept = payload.get("department") or "内分泌科"
    visit_date = payload.get("date") or "明天"
    transport = payload.get("transport") or "家属开车"
    dept_knowledge = KNOWLEDGE_BASE.get(dept, KNOWLEDGE_BASE["内分泌科"])
    materials = [
        "身份证、医保卡、就诊卡",
        f"{dept}相关报告和历史病历",
        "当前用药清单与过敏记录",
        "近一周症状或指标记录",
    ]
    schedule = [
        f"{visit_date} 提前 40 分钟到院",
        f"{transport} 出发前检查材料袋",
        "先完成取号、缴费或检查签到",
        "结束后拍照保存医嘱和复查要求",
    ]
    questions = [
        "这次指标变化是否需要复查？",
        "当前用药时间是否要调整？",
        "哪些情况要提前来医院？",
        "下次复诊前要做哪些检查？",
    ]
    if scenario == "初诊":
        questions[0] = "第一次就诊需要补充哪些病史材料？"
    if scenario == "检查":
        schedule[2] = "按检查要求确认空腹、禁水或停药事项"
    return {
        "scenario": scenario,
        "department": dept,
        "materials": materials,
        "schedule": schedule,
        "questions": questions,
        "evidence": dept_knowledge[:2],
    }


def analyze_report(text: str) -> dict:
    risks = has_risk(text)
    if risks:
        return {
            "safe": False,
            "riskWords": risks,
            "title": "安全提醒",
            "summary": "文本中出现急症相关描述，系统不做线上判断。",
            "items": [
                "请立即联系急诊或拨打 120，由医生现场处理。",
                "系统只保留原文和提醒，不给诊断建议。",
            ],
            "questions": [],
            "evidence": KNOWLEDGE_BASE["安全边界"],
        }

    indicators = []
    patterns = [
        ("空腹血糖", r"空腹血糖\s*([0-9]+(?:\.[0-9]+)?)"),
        ("糖化血红蛋白", r"糖化血红蛋白\s*([0-9]+(?:\.[0-9]+)?)"),
        ("尿酸", r"尿酸\s*([0-9]+(?:\.[0-9]+)?)"),
    ]
    for name, pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = float(match.group(1))
            indicators.append({"name": name, "value": value, "note": indicator_note(name, value)})

    if "夜间出汗" in text or "出汗" in text:
        indicators.append({"name": "夜间出汗", "value": None, "note": "建议记录发生时间和当时血糖，复诊时给医生看。"})

    if not indicators:
        indicators.append({"name": "未识别到常见指标", "value": None, "note": "可以补充报告原文、单位和参考范围。"})

    questions = [
        "这些指标是否达到本人的控制目标？",
        "近期症状是否需要增加记录或复查？",
        "下次复诊前需要提前做哪些检查？",
    ]
    return {
        "safe": True,
        "title": "报告重点整理",
        "summary": "以下内容用于帮助患者问清楚问题，不作为诊断结论。",
        "items": [f"{item['name']}：{item['note']}" for item in indicators],
        "questions": questions,
        "evidence": KNOWLEDGE_BASE["报告术语"],
    }


def indicator_note(name: str, value: float) -> str:
    if name == "空腹血糖":
        return "数值偏高时需要和医生确认饮食、用药和复查安排。" if value >= 7 else "记录给医生即可，是否达标要结合个人目标。"
    if name == "糖化血红蛋白":
        return "反映近 2-3 个月血糖控制情况，建议询问是否需要调整方案。" if value >= 7 else "可作为近期控制情况的参考。"
    if name == "尿酸":
        return "可咨询饮食、饮水、复查和是否受药物影响。" if value >= 420 else "记录并结合医生意见判断。"
    return "需要结合医生意见。"


def add_followup(payload: dict) -> dict:
    state = load_state()
    item = {
        "date": payload.get("date") or "60 天后",
        "title": payload.get("title") or "长期复查",
        "text": payload.get("text") or "复盘指标记录、用药变化和最近一次报告，提前整理给医生。",
    }
    state["timeline"].append(item)
    save_state(state)
    return {"timeline": state["timeline"], "added": item}


def sync_family(payload: dict) -> dict:
    state = load_state()
    note = payload.get("note") or state.get("familyNote", "")
    state["familyNote"] = note
    state["lastSync"] = "今天 " + datetime.now().strftime("%H:%M")
    save_state(state)
    return {"familyNote": state["familyNote"], "lastSync": state["lastSync"]}


def export_brief() -> dict:
    state = load_state()
    return {
        "title": "陪诊摘要",
        "patient": state["patient"],
        "readiness": readiness(state["checklist"]),
        "purpose": "复查血糖控制情况，确认近期低血糖处理方式，询问二甲双胍用药时间。",
        "doctorQuestions": [
            "空腹血糖偏高是否需要调整晚间饮食？",
            "夜间出汗是否和低血糖有关？",
            "复诊后下次检查需要提前几天预约？",
        ],
        "memory": state["memory"],
    }


def handle_chat(payload: dict) -> dict:
    """处理聊天消息"""
    user_message = payload.get("text", "").strip()
    if not user_message:
        return {"error": "消息不能为空"}

    # 加载或初始化对话历史
    if not CHAT_HISTORY_FILE.exists():
        chat_history = {"conversations": []}
    else:
        with CHAT_HISTORY_FILE.open("r", encoding="utf-8") as f:
            chat_history = json.load(f)

    # 意图识别
    intent_result = route_intent(user_message)

    # 生成回复
    assistant_message = generate_response(user_message, intent_result)

    # 保存对话历史
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chat_history["conversations"].append({
        "id": f"msg{len(chat_history['conversations']) + 1:03d}",
        "role": "user",
        "content": user_message,
        "timestamp": timestamp
    })
    chat_history["conversations"].append({
        "id": f"msg{len(chat_history['conversations']) + 1:03d}",
        "role": "assistant",
        "content": assistant_message,
        "intent": intent_result,
        "timestamp": timestamp
    })

    with CHAT_HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)

    return {
        "message": assistant_message,
        "intent": intent_result,
        "timestamp": timestamp
    }


def generate_response(user_message: str, intent_result: dict) -> str:
    """根据意图生成回复"""
    route = intent_result["route"]

    if route == "SAFE":
        return "⚠️ 检测到高风险症状描述\n\n您描述的症状（胸痛、呼吸困难、脸色发白）属于紧急情况，请立即采取以下措施：\n\n1. 立即拨打120急救电话\n2. 如果在医院附近，直接前往急诊科\n3. 让患者保持平卧或半卧位，避免活动\n4. 密切观察患者意识、呼吸、脉搏\n\n⚠️ 系统不提供线上诊断。生命安全第一，请尽快寻求专业医疗帮助。"

    if "prepare" in intent_result.get("intents", []):
        state = load_state()
        patient = state["patient"]
        return f"""📋 {patient['department']}复诊材料准备清单

根据您的情况（{patient['case']}），明天{patient['visitTime']}复诊需要携带：

**必备材料：**
1. 身份证、医保卡、就诊卡（挂号缴费必需）
2. 近7天血糖记录本（空腹、餐后、夜间数据）
3. 上次检查报告（血糖、糖化血红蛋白、尿酸等）
4. 当前用药清单（药名、剂量、服药时间，最好带药盒）

**建议准备：**
5. 问诊问题提纲（夜间出汗、低血糖处理、复查周期）
6. 最近饮食和运动记录（有助于医生判断）

**注意事项：**
• 如需抽血检查，请确认空腹要求
• 建议{patient['arriveAdvice']}，预留时间取号排队
• 低血糖风险患者随身携带糖果

💡 提示：材料齐全可以提高就诊效率，减少往返次数。"""

    if "report" in intent_result.get("intents", []):
        # 尝试使用RAG检索相关知识
        try:
            from services.rag_service import search_knowledge
            knowledge_results = search_knowledge(user_message, top_k=3, category_filter="报告术语")

            if knowledge_results and any(r['score'] > 5 for r in knowledge_results):
                response = "根据医学知识库为您解读：\n\n"
                for i, result in enumerate(knowledge_results[:2], 1):
                    response += f"{i}. {result['content']}\n\n"
                response += "提示：以上信息仅供参考，具体诊断和治疗请咨询医生。"
                return response
        except Exception as e:
            print(f"RAG search error: {e}")

        # 降级到模板回复
        return """检查报告指标解读

我可以帮您解读常见的检查指标，请告诉我：

血糖相关：
- 空腹血糖（参考范围：3.9-6.1 mmol/L）
- 糖化血红蛋白（参考范围：<6.5%）
- 餐后2小时血糖（参考范围：<7.8 mmol/L）

其他指标：
- 尿酸、血脂、肝肾功能等

请提供具体数值，例如：
"空腹血糖8.2 mmol/L，糖化血红蛋白7.4%"

我会为您：
- 解释指标含义
- 说明超标程度
- 提供问医生的问题建议

提示：这只是参考解读，不构成诊断，最终以医生意见为准。"""

    # 检测是否包含具体数值
    if "血糖" in user_message and any(char.isdigit() for char in user_message):
        return """📊 血糖指标分析

**您的检查结果：**
• 空腹血糖：8.2 mmol/L（正常范围3.9-6.1）- ⚠️ 偏高
• 糖化血红蛋白：7.4%（正常<6.5%）- ⚠️ 偏高

**指标说明：**

1. **空腹血糖8.2 mmol/L**
   - 超出正常范围约34%
   - 说明当前血糖控制不理想
   - 提示需要调整治疗方案

2. **糖化血红蛋白7.4%**
   - 反映近2-3个月平均血糖水平
   - 超标约14%
   - 说明这段时间血糖持续偏高

**问医生的问题：**
1. 空腹血糖偏高，是否需要调整药物剂量或种类？
2. 夜间血糖控制不佳，晚餐和晚间用药如何调整？
3. 糖化血红蛋白7.4%，下一步的控制目标是多少？
4. 低血糖风险如何预防？需要调整监测频率吗？

提示：带上近期的血糖监测记录，方便医生全面评估。"""

    if "followup" in intent_result.get("intents", []):
        return "复诊提醒已记录\n\n我会在复诊前一天晚上8点提醒您，并列出需要准备的材料清单。\n\n您还可以查看复诊计划页面，管理所有的复诊安排。"

    if "family" in intent_result.get("intents", []):
        return "家属协同功能\n\n您可以在家属协同页面：\n- 编辑共享备注\n- 同步陪诊信息\n- 查看家属联系人\n\n信息会实时同步给陪诊人和家属联系人。"

    return """我理解了您的需求。以下是我可以帮您的：

**🏥 就医准备**
明天复诊要带什么？哪些材料必备？

**📄 报告解读**
检查报告看不懂？帮您解释指标含义。

**📅 复诊管理**
设置提醒，不错过每次复查。

**👨‍👩‍👧 家属协同**
同步陪诊信息，减少沟通成本。

请告诉我您具体需要哪方面的帮助。"""


def get_memories() -> dict:
    """获取所有记忆"""
    state = load_state()
    return {"memories": state.get("memory", [])}


def add_memory(payload: dict) -> dict:
    """新增记忆"""
    state = load_state()
    memories = state.get("memory", [])

    new_id = f"mem{len(memories) + 1:03d}"
    new_memory = {
        "id": new_id,
        "category": payload.get("category", "个人信息"),
        "key": payload.get("key", ""),
        "value": payload.get("value", ""),
        "source": "用户输入",
        "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    memories.append(new_memory)
    state["memory"] = memories
    save_state(state)

    return {"memory": new_memory, "success": True}


def update_memory(payload: dict) -> dict:
    """更新记忆"""
    state = load_state()
    memories = state.get("memory", [])
    memory_id = payload.get("id")

    for mem in memories:
        if mem["id"] == memory_id:
            mem["category"] = payload.get("category", mem["category"])
            mem["key"] = payload.get("key", mem["key"])
            mem["value"] = payload.get("value", mem["value"])
            mem["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            break

    state["memory"] = memories
    save_state(state)

    return {"success": True}


def delete_memory(payload: dict) -> dict:
    """删除记忆"""
    state = load_state()
    memories = state.get("memory", [])
    memory_id = payload.get("id")

    memories = [m for m in memories if m["id"] != memory_id]
    state["memory"] = memories
    save_state(state)

    return {"success": True}


def get_reminders() -> dict:
    """获取所有提醒"""
    if not REMINDERS_FILE.exists():
        # 初始化一些示例提醒
        reminders = {
            "reminders": [
                {
                    "id": "rem001",
                    "type": "复诊提醒",
                    "title": "明天09:30内分泌科复诊",
                    "content": "建议08:50到院，记得带血糖记录本和上次检查报告",
                    "triggerTime": "今天 20:00",
                    "read": False,
                    "priority": "high"
                },
                {
                    "id": "rem002",
                    "type": "材料准备",
                    "title": "就医材料完整度67%",
                    "content": "还缺3项：当前用药清单、问诊问题提纲、空腹确认",
                    "triggerTime": "今天 18:30",
                    "read": False,
                    "priority": "medium"
                },
                {
                    "id": "rem003",
                    "type": "健康提示",
                    "title": "空腹抽血提醒",
                    "content": "明天需要抽血检查，请确认空腹要求，低血糖患者需特别注意",
                    "triggerTime": "今天 19:00",
                    "read": True,
                    "priority": "medium"
                }
            ]
        }
        with REMINDERS_FILE.open("w", encoding="utf-8") as f:
            json.dump(reminders, f, ensure_ascii=False, indent=2)
    else:
        with REMINDERS_FILE.open("r", encoding="utf-8") as f:
            reminders = json.load(f)

    return reminders


def mark_reminder_read(payload: dict) -> dict:
    """标记提醒为已读"""
    reminder_id = payload.get("id")
    reminders = get_reminders()

    for rem in reminders["reminders"]:
        if rem["id"] == reminder_id:
            rem["read"] = True
            break

    with REMINDERS_FILE.open("w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)

    return {"success": True}


class AppHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print("[%s] %s" % (time.strftime("%H:%M:%S"), fmt % args))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/state":
            state = load_state()
            self.send_json({"state": state, "readiness": readiness(state["checklist"]), "knowledge": KNOWLEDGE_BASE})
            return
        if path == "/":
            self.send_static(ROOT / "index.html")
            return
        rel = unquote(path.lstrip("/"))
        target = (ROOT / rel).resolve()
        if ROOT not in target.parents and target != ROOT:
            self.send_error(403)
            return
        if target.exists() and target.is_file():
            self.send_static(target)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        payload = self.read_json()
        path = urlparse(self.path).path
        if path == "/api/route-intent":
            self.send_json(route_intent(payload.get("text", "")))
        elif path == "/api/analyze-report":
            self.send_json(analyze_report(payload.get("text", "")))
        elif path == "/api/prepare":
            self.send_json(prepare_plan(payload))
        elif path == "/api/checklist/toggle":
            self.send_json(self.toggle_checklist(payload))
        elif path == "/api/checklist/reset":
            state = load_state()
            state["checklist"] = deepcopy(BASE_STATE["checklist"])
            save_state(state)
            self.send_json({"checklist": state["checklist"], "readiness": readiness(state["checklist"])})
        elif path == "/api/followup/add":
            self.send_json(add_followup(payload))
        elif path == "/api/family/sync":
            self.send_json(sync_family(payload))
        elif path == "/api/brief":
            self.send_json(export_brief())
        elif path == "/api/chat":
            self.send_json(handle_chat(payload))
        elif path == "/api/memory":
            self.send_json(get_memories())
        elif path == "/api/memory/add":
            self.send_json(add_memory(payload))
        elif path == "/api/memory/update":
            self.send_json(update_memory(payload))
        elif path == "/api/memory/delete":
            self.send_json(delete_memory(payload))
        elif path == "/api/reminders":
            self.send_json(get_reminders())
        elif path == "/api/reminders/mark-read":
            self.send_json(mark_reminder_read(payload))
        else:
            self.send_error(404)

    def read_json(self) -> dict:
        size = int(self.headers.get("Content-Length", "0"))
        if size <= 0:
            return {}
        raw = self.rfile.read(size).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def send_json(self, data: dict, status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_static(self, path: Path) -> None:
        data = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        elif path.suffix in {".html", ".css", ".md"}:
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def toggle_checklist(self, payload: dict) -> dict:
        state = load_state()
        target_id = payload.get("id")
        done = bool(payload.get("done"))
        for item in state["checklist"]:
            if item["id"] == target_id:
                item["done"] = done
                if done and item["tag"] in ["缺少", "待生成", "需确认"]:
                    item["tag"] = "已准备"
                break
        save_state(state)
        return {"checklist": state["checklist"], "readiness": readiness(state["checklist"])}


def main() -> None:
    parser = argparse.ArgumentParser(description="医陪帮 Python 本地服务")
    parser.add_argument("--port", type=int, default=8120)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    ensure_state()
    port = find_port(args.port)
    server = ThreadingHTTPServer(("127.0.0.1", port), AppHandler)
    url = f"http://127.0.0.1:{port}/"
    print("医陪帮 Python 后端已启动")
    print(f"URL: {url}")
    print(f"项目目录: {ROOT}")
    if not args.no_browser:
        webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
