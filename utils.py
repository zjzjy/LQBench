"""
工具函数，用于支持LeBench的各种功能
"""
import json
import os
import datetime
from typing import Dict, List, Any, Optional


def format_timestamp(timestamp: float) -> str:
    """
    格式化时间戳为可读字符串
    
    Args:
        timestamp: 时间戳
        
    Returns:
        格式化的时间字符串
    """
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_mood(mood_value: float) -> str:
    """
    将情绪值转换为描述性文本
    
    Args:
        mood_value: 情绪值(-1到1)
        
    Returns:
        描述性文本
    """
    if mood_value >= 0.7:
        return "非常积极"
    elif mood_value >= 0.3:
        return "积极"
    elif mood_value >= -0.3:
        return "中性"
    elif mood_value >= -0.7:
        return "消极"
    else:
        return "非常消极"


def format_mood_trend(trend: str) -> str:
    """
    将情绪趋势转换为描述性文本
    
    Args:
        trend: 情绪趋势标识
        
    Returns:
        描述性文本
    """
    trends = {
        "significant_improvement": "显著改善",
        "slight_improvement": "略有改善",
        "stable": "基本稳定",
        "slight_deterioration": "略有恶化",
        "significant_deterioration": "显著恶化",
        "insufficient_data": "数据不足"
    }
    return trends.get(trend, "未知")


def load_results(results_file: str) -> Dict[str, Any]:
    """
    加载评估结果文件
    
    Args:
        results_file: 结果文件路径
        
    Returns:
        评估结果字典
    """
    with open(results_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_result_files(results_dir: str = "results") -> List[str]:
    """
    列出所有评估结果文件
    
    Args:
        results_dir: 结果目录
        
    Returns:
        结果文件路径列表
    """
    if not os.path.exists(results_dir):
        return []
        
    files = [
        os.path.join(results_dir, f)
        for f in os.listdir(results_dir)
        if f.startswith("evaluation_") and f.endswith(".json")
    ]
    
    # 按修改时间排序，最新的在前
    return sorted(files, key=lambda x: os.path.getmtime(x), reverse=True)


def print_conversation(conversation_history: List[Dict[str, str]]) -> None:
    """
    打印对话历史
    
    Args:
        conversation_history: 对话历史列表
    """
    for i, msg in enumerate(conversation_history):
        role = "虚拟人物" if msg["role"] == "assistant" else "待测模型"
        print(f"\n[{i//2 + 1}] {role}:")
        print(msg["content"])


def print_cognitive_model(cognitive_model: Dict[str, Any], title: str = "认知模型") -> None:
    """
    打印认知模型
    
    Args:
        cognitive_model: 认知模型字典
        title: 标题
    """
    print(f"\n===== {title} =====")
    
    # 打印初级评估
    primary = cognitive_model.get("primary_appraisal", {})
    print("\n初级评估 (Primary Appraisal):")
    print(f"情境相关性: {primary.get('relevance', '未指定')}")
    print(f"情境性质: {primary.get('nature', '未指定')}")
    
    # 打印次级评估
    secondary = cognitive_model.get("secondary_appraisal", {})
    print("\n次级评估 (Secondary Appraisal):")
    print(f"责任归因: {secondary.get('attribution', '未指定')}")
    print(f"应对能力: {secondary.get('coping_ability', '未指定')}")
    print(f"应对策略: {secondary.get('coping_strategy', '未指定')}")
    
    # 打印情绪
    emotions = cognitive_model.get("emotions", [])
    print("\n情绪 (Emotions):")
    print(", ".join(emotions) if emotions else "未指定")
