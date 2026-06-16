"""
简化的RAG服务 - 使用文本匹配而非向量搜索
避免ChromaDB的依赖问题
"""
import json
from pathlib import Path
from typing import List, Dict, Optional

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"
KNOWLEDGE_FILE = DATA_DIR / "knowledge" / "medical_knowledge.json"

# 全局知识库缓存
knowledge_base = []


def load_knowledge():
    """加载知识库"""
    global knowledge_base

    if not KNOWLEDGE_FILE.exists():
        print(f"Knowledge file not found: {KNOWLEDGE_FILE}")
        return

    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        knowledge_base = json.load(f)

    print(f"Loaded {len(knowledge_base)} knowledge items")


def simple_search(query: str, top_k: int = 5, category_filter: Optional[str] = None) -> List[Dict]:
    """简单的文本匹配搜索"""
    if not knowledge_base:
        load_knowledge()

    results = []

    for item in knowledge_base:
        # 类别过滤
        if category_filter and item['category'] != category_filter:
            continue

        # 计算相关性得分（简单的关键词匹配）
        score = 0

        # 检查查询词是否在内容中
        if query in item['content']:
            score += 10

        # 检查查询词的每个字是否在内容中
        for char in query:
            if char in item['content']:
                score += 1

        # 检查标签匹配
        for tag in item['tags']:
            if tag in query or query in tag:
                score += 5

        if score > 0:
            results.append({
                'content': item['content'],
                'category': item['category'],
                'tags': item['tags'],
                'source': item['source'],
                'score': score
            })

    # 按得分排序并返回top_k
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]


def search_knowledge(query: str, top_k: int = 5, category_filter: Optional[str] = None) -> List[Dict]:
    """搜索知识库（对外接口）"""
    return simple_search(query, top_k, category_filter)


if __name__ == "__main__":
    # 测试搜索
    load_knowledge()

    print("\n=== Testing Search ===")
    print("\nQuery: 空腹血糖正常范围")
    results = search_knowledge("空腹血糖正常范围", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']}")
        print(f"   Content: {result['content'][:80]}...")
        print(f"   Category: {result['category']}")

    print("\n\nQuery: 胸痛")
    results = search_knowledge("胸痛", top_k=2)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']}")
        print(f"   Content: {result['content'][:80]}...")
        print(f"   Category: {result['category']}")
