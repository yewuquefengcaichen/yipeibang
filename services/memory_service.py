"""
智能记忆提取服务
使用LLM自动从对话中提取关键信息
"""
import json
from typing import Dict, List, Optional
from services.llm_service import generate_stream, LLMProvider
import asyncio


# 记忆提取提示词
MEMORY_EXTRACTION_PROMPT = """你是一个信息提取助手。从下面的对话中提取重要的医疗和个人信息。

对话内容：
用户：{user_message}
助手：{assistant_message}

请提取以下类型的信息（如果有的话）：
1. **个人信息**：姓名、年龄、性别、职业等
2. **疾病信息**：诊断、病史、症状等
3. **用药信息**：药物名称、剂量、频次等
4. **检查信息**：检查项目、结果、时间等
5. **就医信息**：医院、科室、医生、就诊时间等
6. **偏好信息**：饮食偏好、过敏信息等
7. **注意事项**：需要特别注意的事项

要求：
- 只提取明确提到的信息，不要推测
- 使用简洁的短语或句子
- 如果没有相关信息，返回空数组
- 返回JSON格式

返回格式：
{{
  "personal_info": ["信息1", "信息2"],
  "disease_info": ["信息1"],
  "medication_info": ["信息1", "信息2"],
  "examination_info": ["信息1"],
  "hospital_info": ["信息1"],
  "preference_info": ["信息1"],
  "notes": ["信息1"]
}}
"""


async def extract_memory_from_conversation(
    user_message: str,
    assistant_message: str,
    provider: LLMProvider = LLMProvider.GEMINI
) -> Dict:
    """从对话中提取记忆信息"""

    prompt = MEMORY_EXTRACTION_PROMPT.format(
        user_message=user_message,
        assistant_message=assistant_message
    )

    # 调用LLM提取
    full_response = ""
    async for chunk in generate_stream(prompt, provider):
        full_response += chunk

    # 解析JSON
    try:
        # 提取JSON部分
        start = full_response.find('{')
        end = full_response.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = full_response[start:end]
            extracted = json.loads(json_str)
            return extracted
        else:
            return {}
    except Exception as e:
        print(f"Failed to parse memory extraction: {e}")
        return {}


def save_extracted_memories(
    extracted: Dict,
    conversation_id: str,
    user_id: str = "default_user"
) -> List[str]:
    """保存提取的记忆到数据库"""
    from utils.database import save_memory

    saved_ids = []
    category_mapping = {
        'personal_info': '个人信息',
        'disease_info': '疾病信息',
        'medication_info': '用药信息',
        'examination_info': '检查信息',
        'hospital_info': '就医信息',
        'preference_info': '偏好',
        'notes': '注意事项'
    }

    for key, items in extracted.items():
        if not items:
            continue

        category = category_mapping.get(key, '其他')
        for item in items:
            if item.strip():
                memory_id = save_memory(
                    user_id=user_id,
                    category=category,
                    content=item.strip(),
                    conversation_id=conversation_id
                )
                if memory_id:
                    saved_ids.append(memory_id)

    return saved_ids


# 记忆类型定义
MEMORY_CATEGORIES = [
    "个人信息",
    "疾病信息",
    "用药信息",
    "检查信息",
    "就医信息",
    "偏好",
    "注意事项",
    "其他"
]


def get_relevant_memories(
    query: str,
    user_id: str = "default_user",
    top_k: int = 5,
    category: Optional[str] = None
) -> List[Dict]:
    """获取相关记忆"""
    from utils.database import get_memories

    # 获取所有记忆
    memories = get_memories(user_id, category)

    if not memories:
        return []

    # 简单的关键词匹配排序
    query_lower = query.lower()
    scored_memories = []

    for memory in memories:
        content_lower = memory['content'].lower()
        score = 0

        # 完整匹配
        if query_lower in content_lower:
            score += 10

        # 单字匹配
        for char in query_lower:
            if char in content_lower:
                score += 0.5

        if score > 0:
            memory['relevance_score'] = score
            scored_memories.append(memory)

    # 排序
    scored_memories.sort(key=lambda x: x['relevance_score'], reverse=True)

    return scored_memories[:top_k]


async def auto_extract_and_save(
    user_message: str,
    assistant_message: str,
    conversation_id: str,
    user_id: str = "default_user"
) -> Dict:
    """自动提取并保存记忆"""

    # 提取记忆
    extracted = await extract_memory_from_conversation(
        user_message,
        assistant_message
    )

    # 保存记忆
    saved_ids = save_extracted_memories(
        extracted,
        conversation_id,
        user_id
    )

    return {
        "extracted": extracted,
        "saved_count": len(saved_ids),
        "saved_ids": saved_ids
    }


if __name__ == "__main__":
    # 测试代码
    async def test():
        print("=== Memory Extraction Test ===\n")

        # 测试对话
        user_msg = "我是陈阿姨，今年65岁，患有2型糖尿病，每天服用二甲双胍500mg，一天三次"
        assistant_msg = "您好陈阿姨！我了解到您是65岁的2型糖尿病患者，正在服用二甲双胍500mg，每天三次。这是很常见的治疗方案。"

        print(f"User: {user_msg}")
        print(f"Assistant: {assistant_msg}\n")

        print("Extracting memories...")
        extracted = await extract_memory_from_conversation(user_msg, assistant_msg)

        print("\nExtracted memories:")
        print(json.dumps(extracted, ensure_ascii=False, indent=2))

        # 测试保存
        print("\n\nSaving to database...")
        result = await auto_extract_and_save(
            user_msg,
            assistant_msg,
            conversation_id="test_conv_001"
        )
        print(f"Saved {result['saved_count']} memories")

    asyncio.run(test())
