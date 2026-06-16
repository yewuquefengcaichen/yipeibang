"""
演示数据初始化脚本
"""
from utils.database import (
    create_conversation, save_message, save_memory, create_reminder
)
from datetime import datetime, timedelta

def setup_demo_data():
    """初始化演示数据"""

    # 创建演示对话
    conv_id = create_conversation("糖尿病复诊咨询")

    # 对话1：复诊准备
    save_message(conv_id, "user", "明天内分泌科复诊要带什么材料？")
    save_message(
        conv_id,
        "assistant",
        "根据您的内分泌科复诊，需要准备以下材料...",
        {"route": "ACTION", "intents": ["prepare"], "keywords": ["复诊", "材料"]}
    )

    # 对话2：报告解读
    save_message(conv_id, "user", "空腹血糖8.2 mmol/L，糖化血红蛋白7.4%，这说明什么？")
    save_message(
        conv_id,
        "assistant",
        "根据医学知识库为您解读：\n\n1. 糖尿病患者空腹血糖正常范围是3.9-6.1 mmol/L...",
        {"route": "RAG", "intents": ["report"], "keywords": ["空腹血糖", "糖化血红蛋白"]}
    )

    # 对话3：安全边界
    save_message(conv_id, "user", "患者突然胸痛，伴随呼吸困难")
    save_message(
        conv_id,
        "assistant",
        "检测到高风险症状描述。请立即拨打120或前往急诊...",
        {"route": "SAFE", "intents": [], "keywords": ["胸痛", "呼吸困难"]}
    )

    # 创建演示记忆
    save_memory("个人信息", "常去医院", "南方医院", "用户输入")
    save_memory("个人信息", "常用科室", "内分泌科", "系统推断")
    save_memory("个人信息", "家属联系人", "陈先生 138****5678", "用户输入")
    save_memory("就医偏好", "提醒时间", "复诊前一天晚8点", "用户输入")
    save_memory("就医偏好", "到院方式", "地铁3号线", "用户输入")
    save_memory("注意事项", "药物过敏", "青霉素过敏", "用户输入")
    save_memory("注意事项", "低血糖风险", "夜间易发生低血糖", "系统推断")
    save_memory("用药记录", "当前用药", "二甲双胍 500mg 每日三次", "用户输入")

    # 创建演示提醒
    tomorrow = datetime.now() + timedelta(days=1)
    create_reminder({
        "type": "复诊提醒",
        "title": "明天09:30内分泌科复诊",
        "content": "记得带血糖记录本、检查报告、用药清单。建议08:50到院。",
        "trigger_time": tomorrow.replace(hour=20, minute=0).isoformat(),
        "trigger_type": "once",
        "priority": "high"
    })

    next_week = datetime.now() + timedelta(days=7)
    create_reminder({
        "type": "材料准备",
        "title": "复诊材料准备检查",
        "content": "请检查材料完整度：身份证、医保卡、血糖记录本、检查报告",
        "trigger_time": next_week.replace(hour=19, minute=0).isoformat(),
        "trigger_type": "once",
        "priority": "medium"
    })

    print("Demo data initialized successfully!")
    print(f"- Conversation ID: {conv_id}")
    print(f"- Messages: 6")
    print(f"- Memories: 8")
    print(f"- Reminders: 2")


if __name__ == "__main__":
    setup_demo_data()
