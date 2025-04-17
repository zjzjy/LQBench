"""
定义情侣冲突场景及相关描述
"""

import os
import json
from typing import List, Dict, Any, Optional

def load_conflict_scenarios() -> List[Dict[str, Any]]:
    """从配置文件加载冲突场景"""
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
            print(f"找到配置文件: {path}")
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                config_path = path
                break
    
    if not config:
        raise FileNotFoundError("无法找到配置文件")
    
    scenarios_file = config.get("CONFLICT_SCENARIOS_FILE")
    if not scenarios_file:
        raise ValueError("配置文件中未指定 CONFLICT_SCENARIOS_FILE")
    
    # 解析相对路径
    if not os.path.isabs(scenarios_file):
        # 获取配置文件所在的目录
        config_dir = os.path.dirname(os.path.abspath(config_path))
        # 如果配置文件在 LQBench 目录下，则使用该目录作为基准
        if os.path.basename(config_dir) == "LQBench":
            scenarios_file = os.path.join(config_dir, scenarios_file)
        else:
            # 否则使用当前工作目录
            scenarios_file = os.path.join(os.getcwd(), scenarios_file)
    
    print(f"尝试加载场景文件: {scenarios_file}")
    
    # 加载场景文件
    if not os.path.exists(scenarios_file):
        raise FileNotFoundError(f"找不到场景文件: {scenarios_file}")
    
    with open(scenarios_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        scenarios = data.get("conflict_scenarios", [])
        print(f"加载到 {len(scenarios)} 个场景")
        # for scenario in scenarios:
        #     print(f"场景: {scenario['id']}")
        return scenarios

def get_scenario_by_id(scenario_id: str) -> Optional[Dict[str, Any]]:
    """根据ID获取场景"""
    #print(f"查找场景: {scenario_id}")
    #print(f"可用场景: {[s['id'] for s in conflict_scenarios]}")
    for scenario in conflict_scenarios:
        if scenario["id"] == scenario_id:
            return scenario
    return None

def get_situation_by_id(scenario_id: str, situation_id: str) -> Optional[Dict[str, Any]]:
    """根据场景ID和情境ID获取具体情境"""
    scenario = get_scenario_by_id(scenario_id)
    if scenario:
        for situation in scenario["situations"]:
            if situation["id"] == situation_id:
                return situation
    return None

# 加载场景数据
try:
    conflict_scenarios = load_conflict_scenarios()
except Exception as e:
    print(f"加载场景数据失败: {str(e)}")
    conflict_scenarios = [] 