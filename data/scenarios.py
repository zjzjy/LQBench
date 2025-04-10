"""
情境数据，用于虚拟人物扮演的场景
"""
from typing import Dict, List, Any


# 情境列表
SCENARIOS = [
    {
        "id": "relationship_late_return",
        "title": "伴侣晚归",
        "description": "一对情侣交往两年。最近，女孩注意到男友经常晚归，看起来疲惫不堪，不愿多交流。",
        "context": """
        你们交往已有两年，关系一直很稳定。但最近一个月，他开始频繁晚归，经常到晚上11点甚至凌晨才回家。
        当你询问原因时，他只是简单地回答"工作忙"，看起来很疲惫，不想多说话。
        你发现他开始减少和你的约会时间，即使在一起时也心不在焉，经常看手机。
        你试图沟通，但他总是说你"想太多"或"太敏感"，这让你感到更加不安。
        昨晚他又晚归，身上有淡淡的香水味，这是压垮你的最后一根稻草。
        """,
        "suggested_primary_appraisal": {
            "relevance": "关系稳定性受到威胁，情感安全感受到挑战，对伴侣的信任开始动摇",
            "nature": "负面情境，感觉被背叛和欺骗，关系可能面临危机"
        },
        "suggested_secondary_appraisal": {
            "attribution": "将责任归于伴侣的行为变化和可能的不忠",
            "coping_ability": "感到无助和困惑，不确定如何应对这种情况",
            "coping_strategy": "频繁询问、检查手机、要求解释、寻求确认"
        },
        "suggested_emotions": ["焦虑", "怀疑", "不安", "愤怒", "伤心", "恐惧", "无力感"]
    },
    {
        "id": "relationship_communication_breakdown",
        "title": "沟通障碍",
        "description": "一对情侣因为沟通方式不同而频繁发生争吵。",
        "context": """
        你们交往一年半，最近几个月经常因为小事争吵。
        你发现你们对同一件事的看法经常截然不同，而且很难说服对方。
        每次争吵后，他都会选择沉默，拒绝沟通，这让你更加生气。
        你希望他能更主动地表达自己的想法，而不是总是回避问题。
        最近一次争吵后，他已经三天没有主动联系你了。
        """,
        "suggested_primary_appraisal": {
            "relevance": "关系中的沟通模式出现问题，情感连接受到威胁",
            "nature": "负面情境，感到被忽视和误解"
        },
        "suggested_secondary_appraisal": {
            "attribution": "将问题归因于沟通方式的差异和对方的回避态度",
            "coping_ability": "不确定如何改善沟通，但希望解决问题",
            "coping_strategy": "尝试新的沟通方式、寻求专业建议、给彼此空间"
        },
        "suggested_emotions": ["沮丧", "孤独", "困惑", "失望", "焦虑", "希望"]
    },
    {
        "id": "relationship_future_plans",
        "title": "未来规划分歧",
        "description": "一对情侣对未来生活的规划出现严重分歧。",
        "context": """
        你们交往三年，最近开始讨论结婚和未来的生活规划。
        你希望婚后能继续工作，追求自己的事业，但他认为你应该在家照顾家庭。
        关于居住地也有分歧，你想留在大城市，他则希望回到家乡发展。
        最近一次讨论中，他提到如果你们不能达成一致，可能要考虑分手。
        这让你感到震惊和受伤，因为你一直以为你们的关系很稳固。
        """,
        "suggested_primary_appraisal": {
            "relevance": "关系面临重大抉择，价值观和人生目标出现冲突",
            "nature": "负面情境，感到关系可能面临终结"
        },
        "suggested_secondary_appraisal": {
            "attribution": "将分歧归因于不同的生活理念和价值观",
            "coping_ability": "不确定是否应该妥协或坚持自己的选择",
            "coping_strategy": "深入思考自己的需求、寻求建议、尝试寻找折中方案"
        },
        "suggested_emotions": ["焦虑", "困惑", "伤心", "愤怒", "不确定感", "恐惧"]
    },
    {
        "id": "relationship_trust_issues",
        "title": "信任危机",
        "description": "一对情侣因为过去的欺骗行为而面临信任危机。",
        "context": """
        你们交往两年，最近你发现他曾经对你隐瞒了一些重要的事情。
        虽然事情已经过去，但你知道真相后感到被欺骗和背叛。
        他解释说是因为害怕伤害你才选择隐瞒，但你觉得这反而造成了更大的伤害。
        现在你很难完全信任他，总是怀疑他是否还有其他事情瞒着你。
        他承诺会改变，但你不知道是否应该相信他。
        """,
        "suggested_primary_appraisal": {
            "relevance": "关系中的信任基础受到破坏，安全感丧失",
            "nature": "负面情境，感到被欺骗和背叛"
        },
        "suggested_secondary_appraisal": {
            "attribution": "将问题归因于对方的欺骗行为和缺乏坦诚",
            "coping_ability": "不确定是否能够重建信任",
            "coping_strategy": "要求更多透明度、设定界限、观察对方行为"
        },
        "suggested_emotions": ["愤怒", "伤心", "不信任", "困惑", "犹豫", "希望"]
    }
]


def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """
    根据ID获取特定情境
    
    Args:
        scenario_id: 情境ID
        
    Returns:
        情境数据字典，如果未找到则返回None
    """
    for scenario in SCENARIOS:
        if scenario["id"] == scenario_id:
            return scenario
    return None


def get_all_scenarios() -> List[Dict[str, Any]]:
    """
    获取所有情境的基本信息（不包含详细内容）
    
    Returns:
        情境基本信息列表
    """
    return [
        {
            "id": s["id"],
            "title": s["title"],
            "description": s["description"]
        }
        for s in SCENARIOS
    ]


def get_random_scenario() -> Dict[str, Any]:
    """
    随机获取一个情境
    
    Returns:
        随机选择的情境数据字典
    """
    import random
    return random.choice(SCENARIOS)
