"""
定义虚拟人物配置及相关函数
"""

import os
import json
from typing import List, Dict, Any, Optional

def load_character_profiles() -> List[Dict[str, Any]]:
    """从配置文件加载角色配置"""
    # 首先尝试从环境变量获取配置文件路径
    config_paths = [
        "config.json",
        "LQBench/config.json",
        os.path.join(os.path.dirname(__file__), "../../config.json"),
        os.path.join(os.path.dirname(__file__), "../../LQBench/config.json")
    ]
    
    config = None
    config_path = None
    for path in config_paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                config_path = path
                break
    
    if not config:
        raise FileNotFoundError("无法找到配置文件")
    
    profiles_file = config.get("CHARACTER_PROFILES_FILE")
    if not profiles_file:
        raise ValueError("配置文件中未指定 CHARACTER_PROFILES_FILE")
    
    # 解析相对路径
    if not os.path.isabs(profiles_file):
        # 获取配置文件所在的目录
        config_dir = os.path.dirname(os.path.abspath(config_path))
        # 如果配置文件在 LQBench 目录下，则使用该目录作为基准
        if os.path.basename(config_dir) == "LQBench":
            profiles_file = os.path.join(config_dir, profiles_file)
        else:
            # 否则使用当前工作目录
            profiles_file = os.path.join(os.getcwd(), profiles_file)
    
    # 加载角色配置文件
    if not os.path.exists(profiles_file):
        raise FileNotFoundError(f"找不到角色配置文件: {profiles_file}")
    
    with open(profiles_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("character_profiles", [])

def get_character_by_scenario(scenario_id: str, situation_id: str) -> Optional[Dict[str, Any]]:
    """根据场景ID和情境ID获取对应的角色配置"""
    # 构造完整的角色ID（场景ID_情境ID）
    character_id = f"{scenario_id}_{situation_id}"
    
    # 在角色配置中查找匹配的ID
    for character in character_profiles:
        if character.get("id") == character_id:
            return character
    return None

def create_character_profile(
    id: str,
    name: str,
    gender: str,
    age: int,
    personality_type: str,
    relationship_belief: str,
    communication_type: str,
    attachment_style: str,
    background: str,
    trigger_topics: List[str],
    coping_mechanisms: List[str],
    scenario_id: Optional[str] = None,
    situation_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建角色配置"""
    return {
        "id": id,
        "name": name,
        "gender": gender,
        "age": age,
        "personality_type": personality_type,
        "relationship_belief": relationship_belief,
        "communication_type": communication_type,
        "attachment_style": attachment_style,
        "background": background,
        "trigger_topics": trigger_topics,
        "coping_mechanisms": coping_mechanisms,
        "scenario_id": scenario_id,
        "situation_id": situation_id
    }

# 加载角色配置数据
try:
    character_profiles = load_character_profiles()
except Exception as e:
    print(f"加载角色配置数据失败: {str(e)}")
    character_profiles = []

# 导出示例角色供测试使用
sample_characters = character_profiles[:3] if character_profiles else []

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