"""
配置文件，用于存储LLM接口参数和评估设置
"""

# LLM API配置
MODEL_CONFIGS = {
    "deepseek": {
        "api_key": "sk-1bc0ea02705c4237a63340c3e821709b",
        "api_base": "https://api.deepseek.com/v1",
        "model_name": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 1000
    },
    "expert": {
        "api_key": "sk-1bc0ea02705c4237a63340c3e821709b",
        "api_base": "https://api.deepseek.com/v1",
        "model_name": "deepseek-chat",
        "temperature": 0.2,
        "max_tokens": 2000
    }
}

# 会话控制参数
CONVERSATION_CONFIG = {
    "max_turns": 5,  # 最大对话轮次
    "mood_threshold": 0.8,  # 情绪改善阈值，超过此值则结束对话
    "min_turns": 5,  # 最小对话轮次
}

# 情绪评估参数
EMOTION_CONFIG = {
    "record_interval": 1,  # 每隔多少轮记录一次情绪
    "emotion_scale": {
        "very_negative": -1.0,
        "negative": -0.5,
        "neutral": 0.0,
        "positive": 0.5,
        "very_positive": 1.0
    }
}

# 认知模型评估参数
COGNITIVE_MODEL_CONFIG = {
    "compare_metrics": ["relevance", "nature", "coping_ability", "attribution"],
    "score_weights": {
        "relevance": 0.25,
        "nature": 0.25,
        "coping_ability": 0.25,
        "attribution": 0.25
    }
}

# 对话风格设置
CONVERSATION_STYLES = [
    "plain",
    "upset",
    "verbose",
    "reserved",
    "tangent",
    "pleasing"
]

# 输出和日志配置
OUTPUT_CONFIG = {
    "log_dir": "logs",
    "results_dir": "results",
    "debug": True,
    "save_conversations": True
}
