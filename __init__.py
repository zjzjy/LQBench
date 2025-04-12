"""
LQBench - 用于情侣对话模拟的基准测试框架
"""

__version__ = "0.1.0"

# 导出主要的类和函数，以便更便捷地导入
from LQBench.character_simulator import CharacterSimulator
from LQBench.benchmark_runner import BenchmarkRunner

# 方便导入的子模块
from LQBench.api.data import (
    personality_types,
    relationship_beliefs,
    communication_types,
    attachment_styles,
    emotions,
    conflict_scenarios,
    character_profiles,
    prompt_templates
)

# 导出LLM客户端
from LQBench.api.llm import LLMClient 