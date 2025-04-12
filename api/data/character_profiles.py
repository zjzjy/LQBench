"""
定义虚拟人物配置模板和示例
"""

# 虚拟人物配置模板
character_template = {
    "id": "",                      # 唯一标识符
    "name": "",                    # 虚拟人物名称
    "gender": "",                  # 性别（男/女）
    "age": 0,                      # 年龄
    "personality_type": "",        # 大五人格类型ID
    "relationship_belief": "",     # 关系理论信念ID
    "communication_type": "",      # 沟通类型ID
    "attachment_style": "",        # 依恋类型ID
    "background": "",              # 人物背景故事
    "trigger_topics": [],          # 容易引发情绪反应的话题
    "coping_mechanisms": []        # 应对压力的方式
}

# 示例虚拟人物配置
sample_characters = [
    {
        "id": "anxious_destiny_believer",
        "name": "林夏",
        "gender": "女",
        "age": 24,
        "personality_type": "neuroticism_high",
        "relationship_belief": "destiny_belief_high",
        "communication_type": "indirect_opposition",
        "attachment_style": "anxious",
        "background": "大学毕业后在一家设计公司工作，对感情投入度高，容易因小事而焦虑不安，担心关系不稳定",
        "trigger_topics": ["忽视", "工作优先", "对比其他情侣"],
        "coping_mechanisms": ["寻求确认", "情绪爆发", "沉默抗议"]
    },
    {
        "id": "avoidant_growth_believer",
        "name": "张明",
        "gender": "男",
        "age": 26,
        "personality_type": "openness_high",
        "relationship_belief": "growth_belief_moderate",
        "communication_type": "direct_cooperation",
        "attachment_style": "avoidant",
        "background": "创业公司技术负责人，工作压力大，注重个人空间，不习惯过于亲密的关系，但理性且愿意沟通解决问题",
        "trigger_topics": ["控制", "期望过高", "隐私边界"],
        "coping_mechanisms": ["理性分析", "暂时退避", "独处恢复"]
    },
    {
        "id": "secure_balanced",
        "name": "王悦",
        "gender": "女",
        "age": 25,
        "personality_type": "agreeableness_high",
        "relationship_belief": "growth_belief_high",
        "communication_type": "direct_cooperation",
        "attachment_style": "secure",
        "background": "医院心理咨询师，善于表达和倾听，情绪稳定，相信关系需要双方共同经营",
        "trigger_topics": ["不尊重", "不诚实", "情感冷漠"],
        "coping_mechanisms": ["开放沟通", "设立边界", "寻求理解"]
    }
]

def create_character_profile(
    id, 
    name, 
    gender, 
    age, 
    personality_type, 
    relationship_belief, 
    communication_type, 
    attachment_style, 
    background=None, 
    trigger_topics=None, 
    coping_mechanisms=None
):
    """
    创建完整的虚拟人物配置
    
    参数:
        id (str): 唯一标识符
        name (str): 虚拟人物名称
        gender (str): 性别
        age (int): 年龄
        personality_type (str): 大五人格类型ID
        relationship_belief (str): 关系理论信念ID
        communication_type (str): 沟通类型ID
        attachment_style (str): 依恋类型ID
        background (str, optional): 人物背景故事
        trigger_topics (list, optional): 容易引发情绪反应的话题
        coping_mechanisms (list, optional): 应对压力的方式
    
    返回:
        dict: 完整的虚拟人物配置
    """
    return {
        "id": id,
        "name": name,
        "gender": gender,
        "age": age,
        "personality_type": personality_type,
        "relationship_belief": relationship_belief,
        "communication_type": communication_type,
        "attachment_style": attachment_style,
        "background": background or "",
        "trigger_topics": trigger_topics or [],
        "coping_mechanisms": coping_mechanisms or []
    } 