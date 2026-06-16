"""
多供应商LLM服务统一接口
支持: Gemini, Claude, OpenAI, DeepSeek等
"""
import os
import asyncio
from typing import AsyncGenerator, Optional, Dict, Any
from enum import Enum

# ========== 供应商枚举 ==========
class LLMProvider(str, Enum):
    GEMINI = "gemini"
    CLAUDE = "claude"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"

# ========== API密钥配置 ==========
API_KEYS = {
    LLMProvider.GEMINI: "AIzaSyBw4IOq5v8SxHbh6OAnHr9TfmRdbCocX9g",
    LLMProvider.CLAUDE: os.getenv("CLAUDE_API_KEY", ""),
    LLMProvider.OPENAI: os.getenv("OPENAI_API_KEY", ""),
    LLMProvider.DEEPSEEK: os.getenv("DEEPSEEK_API_KEY", ""),
}

# ========== 模型配置 ==========
MODELS = {
    LLMProvider.GEMINI: {
        "default": "gemini-1.5-flash",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
    },
    LLMProvider.CLAUDE: {
        "default": "claude-3-5-sonnet-20241022",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]
    },
    LLMProvider.OPENAI: {
        "default": "gpt-4o",
        "models": ["gpt-4o", "gpt-4o-mini", "o1", "o1-mini"]
    },
    LLMProvider.DEEPSEEK: {
        "default": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-coder"]
    }
}

# ========== 系统提示词 ==========
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
- 重要提示用"⚠️ 提示："开头

禁止：
- 不做诊断（"您这是XXX病"）
- 不推荐具体药物剂量
- 不替代医生建议
"""

# ========== Gemini Provider ==========
async def generate_gemini_stream(
    prompt: str,
    model: str = "gemini-1.5-flash",
    context: Optional[list] = None
) -> AsyncGenerator[str, None]:
    """Gemini流式生成"""
    try:
        import google.generativeai as genai

        genai.configure(api_key=API_KEYS[LLMProvider.GEMINI])

        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

        model_instance = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            system_instruction=SYSTEM_PROMPT
        )

        chat = model_instance.start_chat(history=context or [])
        response = await asyncio.to_thread(chat.send_message, prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        yield f"Gemini API错误: {str(e)}"

# ========== Claude Provider ==========
async def generate_claude_stream(
    prompt: str,
    model: str = "claude-3-5-sonnet-20241022",
    context: Optional[list] = None
) -> AsyncGenerator[str, None]:
    """Claude流式生成"""
    try:
        import anthropic

        if not API_KEYS[LLMProvider.CLAUDE]:
            yield "Claude API密钥未配置"
            return

        client = anthropic.AsyncAnthropic(api_key=API_KEYS[LLMProvider.CLAUDE])

        messages = context or []
        messages.append({"role": "user", "content": prompt})

        async with client.messages.stream(
            model=model,
            max_tokens=2048,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            messages=messages
        ) as stream:
            async for text in stream.text_stream:
                yield text

    except Exception as e:
        yield f"Claude API错误: {str(e)}"

# ========== OpenAI Provider ==========
async def generate_openai_stream(
    prompt: str,
    model: str = "gpt-4o",
    context: Optional[list] = None
) -> AsyncGenerator[str, None]:
    """OpenAI流式生成"""
    try:
        from openai import AsyncOpenAI

        if not API_KEYS[LLMProvider.OPENAI]:
            yield "OpenAI API密钥未配置"
            return

        client = AsyncOpenAI(api_key=API_KEYS[LLMProvider.OPENAI])

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})

        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield f"OpenAI API错误: {str(e)}"

# ========== 统一接口 ==========
async def generate_stream(
    prompt: str,
    provider: LLMProvider = LLMProvider.GEMINI,
    model: Optional[str] = None,
    context: Optional[list] = None
) -> AsyncGenerator[str, None]:
    """
    统一的流式生成接口

    Args:
        prompt: 用户输入
        provider: LLM供应商
        model: 模型名称（可选，默认使用该供应商的默认模型）
        context: 对话上下文

    Yields:
        生成的文本片段
    """
    if not model:
        model = MODELS[provider]["default"]

    if provider == LLMProvider.GEMINI:
        async for chunk in generate_gemini_stream(prompt, model, context):
            yield chunk
    elif provider == LLMProvider.CLAUDE:
        async for chunk in generate_claude_stream(prompt, model, context):
            yield chunk
    elif provider == LLMProvider.OPENAI:
        async for chunk in generate_openai_stream(prompt, model, context):
            yield chunk
    else:
        yield f"不支持的供应商: {provider}"


def get_available_models(provider: LLMProvider) -> list:
    """获取指定供应商的可用模型列表"""
    return MODELS.get(provider, {}).get("models", [])


def get_available_providers() -> list:
    """获取所有可用的供应商列表"""
    return [
        {
            "id": provider.value,
            "name": provider.value.title(),
            "models": get_available_models(provider),
            "default_model": MODELS[provider]["default"],
            "enabled": bool(API_KEYS.get(provider))
        }
        for provider in LLMProvider
    ]


if __name__ == "__main__":
    # 测试代码
    async def test():
        print("=== 测试多供应商LLM服务 ===\n")

        # 测试Gemini
        print("测试 Gemini:")
        async for chunk in generate_stream("你好，简单介绍一下你自己", LLMProvider.GEMINI):
            print(chunk, end="", flush=True)
        print("\n")

    asyncio.run(test())
