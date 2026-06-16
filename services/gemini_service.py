"""
Google Gemini API集成服务
"""
import os
import asyncio
import json
from typing import AsyncGenerator, Optional, Dict, Any
import google.generativeai as genai

# 配置API密钥
GEMINI_API_KEY = "AIzaSyBw4IOq5v8SxHbh6OAnHr9TfmRdbCocX9g"
genai.configure(api_key=GEMINI_API_KEY)

# 配置模型
MODEL_NAME = "gemini-1.5-flash"  # 使用Flash版本，速度快

# 系统提示词
SYSTEM_PROMPT = """你是"医陪帮"智能就医助手，专为老年慢性病患者及陪诊家属设计。

你的角色：
- 温和、耐心、专业的医疗陪诊助手
- 帮助患者理解检查报告、准备复诊材料、记录重要信息
- 不做诊断、不开药、不替代医生

你的特点：
1. 简洁易懂 - 用老年人能理解的语言，避免医学术语
2. 结构清晰 - 使用分点、标题、列表让信息易读
3. 安全第一 - 遇到紧急症状立即提示拨打120
4. 引导就医 - 复杂问题建议咨询医生，不擅自解答

回复格式：
- 使用Markdown格式
- 标题用 ** **
- 列表用数字或 -
- 重要提示用"提示："开头

禁止：
- 不做诊断（"您这是XXX病"）
- 不推荐具体药物剂量
- 不替代医生建议
"""


def get_model():
    """获取配置好的模型"""
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        safety_settings=safety_settings,
        system_instruction=SYSTEM_PROMPT
    )

    return model


async def generate_stream(
    prompt: str,
    context: Optional[list] = None
) -> AsyncGenerator[str, None]:
    """
    流式生成回复

    Args:
        prompt: 用户输入
        context: 对话上下文（可选）

    Yields:
        生成的文本片段
    """
    try:
        model = get_model()

        # 构建对话历史
        chat = model.start_chat(history=context or [])

        # 流式生成
        response = await asyncio.to_thread(
            chat.send_message,
            prompt,
            stream=True
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        print(f"Gemini API error: {e}")
        yield f"抱歉，AI服务暂时不可用。请稍后重试。"


async def generate_response(
    prompt: str,
    context: Optional[list] = None
) -> str:
    """
    非流式生成回复

    Args:
        prompt: 用户输入
        context: 对话上下文（可选）

    Returns:
        完整的回复文本
    """
    try:
        model = get_model()

        # 构建对话历史
        chat = model.start_chat(history=context or [])

        # 生成回复
        response = await asyncio.to_thread(
            chat.send_message,
            prompt
        )

        return response.text

    except Exception as e:
        print(f"Gemini API error: {e}")
        return "抱歉，AI服务暂时不可用。请稍后重试。"


def format_context_for_gemini(messages: list) -> list:
    """
    将对话历史格式化为Gemini API格式

    Args:
        messages: 消息列表 [{"role": "user", "content": "..."}, ...]

    Returns:
        Gemini格式的历史记录
    """
    history = []

    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        history.append({
            "role": role,
            "parts": [msg["content"]]
        })

    return history


if __name__ == "__main__":
    # 测试代码
    async def test():
        print("Testing Gemini API...")

        # 测试流式生成
        print("\n=== 流式生成测试 ===")
        async for chunk in generate_stream("你好，我想了解空腹血糖的正常范围"):
            print(chunk, end="", flush=True)
        print("\n")

        # 测试非流式生成
        print("\n=== 非流式生成测试 ===")
        response = await generate_response("明天复诊要带什么材料？")
        print(response)

    asyncio.run(test())
