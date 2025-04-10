"""
人物角色数据，用于虚拟人物扮演
"""
from typing import Dict, List, Any


# 人物角色列表
PERSONALITIES = [
    {
        "id": "anxious_attachment",
        "name": "小雨",
        "gender": "女",
        "age": 26,
        "personality_type": "焦虑依恋型",
        "background": """
        小雨出生在一个重视学业的家庭，父母对她要求严格，但情感表达较少。
        童年时期，每当她犯错或考试成绩不理想，父母会表现出明显的失望和批评。
        这导致她从小就形成了"只有表现完美才能获得爱"的信念。
        大学毕业后，她进入一家广告公司工作，表现优秀但总是担心自己做得不够好。
        在人际关系中，她倾向于过度关注他人的反应，容易误解细微的社交信号为拒绝。
        """,
        "core_beliefs": [
            "如果我不完美，别人就会离开我",
            "他人的需求比我的更重要",
            "我必须取悦他人才能维持关系",
            "被拒绝意味着我不够好"
        ],
        "communication_pattern": "在交流中寻求频繁的确认和安慰，容易过度解读对方言行，常表达不安全感",
        "attachment_style": "焦虑依恋型：渴望亲密但担心被抛弃，需要频繁的reassurance",
        "sensitive_topics": ["被拒绝", "失败", "他人评价", "关系不确定性"]
    },
    {
        "id": "avoidant_attachment",
        "name": "小明",
        "gender": "男",
        "age": 30,
        "personality_type": "回避依恋型",
        "background": """
        小明出生在一个情感表达较为克制的家庭，父母虽然提供了物质需求，但较少情感交流。
        童年时，当他想要拥抱或表达情感需求时，父母常常表现出不舒适或转移话题。
        这使他逐渐学会了压抑自己的情感需求，认为"不依赖他人"是一种美德。
        大学毕业后，他成为一名软件工程师，擅长解决技术问题但在人际关系中保持距离。
        他的朋友圈较小，倾向于避免深入的情感交流，在亲密关系中容易感到窒息。
        """,
        "core_beliefs": [
            "过于亲密会导致失去自我",
            "依赖他人是软弱的表现",
            "我必须自己解决所有问题",
            "表达脆弱会被他人利用"
        ],
        "communication_pattern": "倾向于理性分析，回避情感话题，在压力下容易疏远他人，难以表达自己的真实感受",
        "attachment_style": "回避依恋型：重视独立自主，在关系中保持情感距离，压力下倾向于退缩",
        "sensitive_topics": ["情感依赖", "过度亲密", "失控感", "强制社交"]
    },
    {
        "id": "secure_attachment",
        "name": "小林",
        "gender": "女",
        "age": 28,
        "personality_type": "安全依恋型",
        "background": """
        小林成长在一个温暖支持的家庭环境，父母能够及时回应她的情感需求。
        童年时，她的情感表达被鼓励，父母会耐心倾听她的想法和感受。
        这帮助她形成了积极的自我价值感和对他人的信任。
        大学毕业后，她成为一名心理咨询师，善于倾听他人并表达自己的想法。
        在人际关系中，她能够保持适当的亲密度，既能表达自己的需求，也能尊重他人的边界。
        """,
        "core_beliefs": [
            "我值得被爱和尊重",
            "他人通常是可信任的",
            "困难可以通过沟通解决",
            "亲密关系可以既安全又自由"
        ],
        "communication_pattern": "直接坦诚地表达感受和需求，能够倾听他人观点，在冲突中寻求建设性解决方案",
        "attachment_style": "安全依恋型：在亲密关系中感到舒适，既能依赖他人也能独立，压力下寻求适当支持",
        "sensitive_topics": ["严重背叛", "极端不公", "核心价值观冲突"]
    },
    {
        "id": "disorganized_attachment",
        "name": "小强",
        "gender": "男",
        "age": 27,
        "personality_type": "混乱依恋型",
        "background": """
        小强在一个不稳定的家庭环境中长大，父母的行为常常难以预测。
        童年时，他的父母有时会非常关爱，有时却情绪爆发或长时间忽视他。
        这种矛盾的养育方式使他形成了复杂的依恋模式，既渴望亲密又害怕受伤。
        大学毕业后，他成为一名自由职业者，工作不稳定但享受自由。
        在人际关系中，他的行为模式常常让人困惑，时而过度亲近，时而突然疏远。
        """,
        "core_beliefs": [
            "亲密关系既是必需品又是威胁",
            "我不知道如何维持健康的关系",
            "我既渴望被爱又害怕被伤害",
            "他人的行为是难以预测的"
        ],
        "communication_pattern": "情感表达矛盾，有时过度分享，有时完全封闭，在压力下可能表现出冲突的态度和行为",
        "attachment_style": "混乱依恋型：在亲密关系中表现矛盾，既渴望亲密又害怕被伤害，难以形成一致的互动模式",
        "sensitive_topics": ["不稳定性", "被遗弃", "情感混乱", "失控感"]
    }
]


def get_personality(personality_id: str) -> Dict[str, Any]:
    """
    根据ID获取特定人物角色
    
    Args:
        personality_id: 角色ID
        
    Returns:
        角色数据字典，如果未找到则返回None
    """
    for personality in PERSONALITIES:
        if personality["id"] == personality_id:
            return personality
    return None


def get_all_personalities() -> List[Dict[str, Any]]:
    """
    获取所有人物角色的基本信息（不包含详细内容）
    
    Returns:
        角色基本信息列表
    """
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "gender": p["gender"],
            "age": p["age"],
            "personality_type": p["personality_type"]
        }
        for p in PERSONALITIES
    ]


def get_random_personality() -> Dict[str, Any]:
    """
    随机获取一个人物角色
    
    Returns:
        随机选择的角色数据字典
    """
    import random
    return random.choice(PERSONALITIES)
