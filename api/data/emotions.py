"""
定义情绪类型及其描述，用于跟踪虚拟人物在对话过程中的情绪变化
"""

emotions = [
    {
        "id": "anger",
        "name": "愤怒",
        "description": "感到恼怒、暴躁或被冒犯",
        "intensity_levels": {
            "1": "轻微恼怒",
            "2": "明显不满",
            "3": "相当生气",
            "4": "非常愤怒",
            "5": "极度暴怒"
        }
    },
    {
        "id": "sadness",
        "name": "悲伤",
        "description": "感到难过、沮丧或失落",
        "intensity_levels": {
            "1": "略感失落",
            "2": "明显沮丧",
            "3": "相当难过",
            "4": "非常悲伤",
            "5": "极度绝望"
        }
    },
    {
        "id": "fear",
        "name": "恐惧",
        "description": "感到害怕、焦虑或担忧",
        "intensity_levels": {
            "1": "轻微担忧",
            "2": "明显不安",
            "3": "相当焦虑",
            "4": "非常恐惧",
            "5": "极度惊恐"
        }
    },
    {
        "id": "disgust",
        "name": "厌恶",
        "description": "感到反感、嫌弃或恶心",
        "intensity_levels": {
            "1": "轻微不适",
            "2": "明显反感",
            "3": "相当厌恶",
            "4": "强烈排斥",
            "5": "极度恶心"
        }
    },
    {
        "id": "happiness",
        "name": "快乐",
        "description": "感到愉悦、满足或喜悦",
        "intensity_levels": {
            "1": "略感满意",
            "2": "明显愉快",
            "3": "相当开心",
            "4": "非常喜悦",
            "5": "极度欣喜"
        }
    },
    {
        "id": "surprise",
        "name": "惊讶",
        "description": "感到意外、震惊或吃惊",
        "intensity_levels": {
            "1": "略感意外",
            "2": "明显吃惊",
            "3": "相当震惊",
            "4": "非常惊讶",
            "5": "极度震撼"
        }
    },
    {
        "id": "trust",
        "name": "信任",
        "description": "感到安全、依赖或信任",
        "intensity_levels": {
            "1": "略有信心",
            "2": "明显信任",
            "3": "相当依赖",
            "4": "非常信赖",
            "5": "完全托付"
        }
    },
    {
        "id": "anticipation",
        "name": "期待",
        "description": "感到盼望、憧憬或希望",
        "intensity_levels": {
            "1": "略有兴趣",
            "2": "明显期待",
            "3": "相当盼望",
            "4": "非常憧憬",
            "5": "极度渴望"
        }
    }
]

# 情绪状态评分系统
emotion_scoring = {
    "threshold": {
        "improvement": 7,  # 情绪从负面变为正面的阈值（调整为7）
        "worsening": -3,   # 情绪从正面变为负面的阈值
        "critical": -10    # 情绪达到极度负面的阈值，可能触发对话终止（调整为-10）
    },
    "baseline": 0,         # 初始情绪基准值
    "max_positive": 10,    # 最高正面情绪值
    "max_negative": -10,   # 最低负面情绪值
    "max_change_per_turn": 3  # 每轮情绪变化的最大幅度
} 