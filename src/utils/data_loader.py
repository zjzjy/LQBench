import json
import os
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple

logger = logging.getLogger(__name__)

class DataLoader:
    """
    数据加载器，用于加载和处理各种数据文件
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化数据加载器
        
        Args:
            base_dir: 数据目录的基础路径，默认为None，使用默认目录
        """
        self.logger = logging.getLogger(__name__)
        
        if base_dir is None:
            # 获取当前文件所在目录，拼接默认数据目录
            self.base_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.base_dir = Path(base_dir)
        
        # 设置各种数据目录
        self.character_dir = self.base_dir / "data" / "characters"
        self.scenario_dir = self.base_dir / "data" / "scenarios"
        self.scenario_templates_dir = self.scenario_dir / "templates"
        self.config_dir = self.base_dir / "config"
        self.results_dir = self.base_dir / "results"
        self.dialogues_dir = self.base_dir / "data" / "dialogues"
        
        # 确保所有目录存在
        for dir_path in [self.character_dir, self.scenario_dir, self.scenario_templates_dir, 
                        self.config_dir, self.results_dir, self.dialogues_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 缓存加载的数据
        self._characters_cache = {}
        self._scenarios_cache = {}
        self._character_pool = None
        self._scenario_pool = None
        self._dialogues_cache = {}
    
    def load_json_file(self, file_path: Union[str, Path]) -> Dict:
        """
        加载JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            加载的JSON数据
            
        Raises:
            FileNotFoundError: 文件不存在
            json.JSONDecodeError: JSON解析错误
        """
        file_path = Path(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            self.logger.error(f"文件不存在: {file_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}, 文件: {file_path}")
            raise
    
    def save_json_file(self, data: Dict, file_path: Union[str, Path], indent: int = 2) -> bool:
        """
        保存数据到JSON文件
        
        Args:
            data: 要保存的数据
            file_path: 目标文件路径
            indent: JSON缩进
            
        Returns:
            保存是否成功
        """
        file_path = Path(file_path)
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            return True
        except Exception as e:
            self.logger.error(f"保存JSON文件失败: {e}, 文件: {file_path}")
            return False
    
    def load_character(self, character_id: str) -> Dict:
        """
        加载角色数据
        
        Args:
            character_id: 角色ID（例如 "char_001"）
            
        Returns:
            角色数据
            
        Raises:
            FileNotFoundError: 角色文件不存在
        """
        # 检查ID格式，补充前缀如果需要
        if not character_id.startswith("char_"):
            # 如果ID是纯数字格式（如"001"），添加前缀
            if character_id.isdigit() or character_id.isdecimal():
                character_id = f"char_{character_id.zfill(3)}"
        
        # 首先尝试在templates目录下查找
        character_path = self.character_dir / "templates" / f"{character_id}.json"
        if not character_path.exists():
            # 如果不存在，尝试在角色目录中直接查找
            character_path = self.character_dir / f"{character_id}.json"
            if not character_path.exists():
                self.logger.error(f"角色文件不存在: {character_id}")
                raise FileNotFoundError(f"找不到角色文件: {character_id}")
        
        self.logger.info(f"加载角色文件: {character_path}")
        return self.load_json_file(character_path)
    
    def load_all_characters(self) -> Dict[str, Dict]:
        """
        加载所有角色数据
        
        Returns:
            角色ID到角色数据的映射字典
        """
        characters = {}
        
        # 检查templates目录
        templates_dir = self.character_dir / "templates"
        if templates_dir.exists():
            for file_path in templates_dir.glob("*.json"):
                try:
                    character = self.load_json_file(file_path)
                    char_id = character.get("id") or file_path.stem
                    characters[char_id] = character
                except Exception as e:
                    self.logger.warning(f"加载角色文件失败: {e}, 文件: {file_path}")
        
        # 也检查主角色目录
        for file_path in self.character_dir.glob("*.json"):
            # 跳过character_pool.json
            if file_path.name == "character_pool.json":
                continue
                
            try:
                character = self.load_json_file(file_path)
                char_id = character.get("id") or file_path.stem
                characters[char_id] = character
            except Exception as e:
                self.logger.warning(f"加载角色文件失败: {e}, 文件: {file_path}")
        
        return characters
    
    def load_scenario(self, scenario_id: str) -> Dict:
        """
        加载场景数据
        
        Args:
            scenario_id: 场景ID（例如 "scenario_005"）
            
        Returns:
            场景数据
            
        Raises:
            FileNotFoundError: 场景文件不存在
        """
        # 检查ID格式，补充前缀如果需要
        if not scenario_id.startswith("scenario_"):
            # 如果ID是纯数字格式（如"005"），添加前缀
            if scenario_id.isdigit() or scenario_id.isdecimal():
                scenario_id = f"scenario_{scenario_id.zfill(3)}"
        
        # 首先尝试在templates目录下查找
        scenario_path = self.scenario_templates_dir / f"{scenario_id}.json"
        if not scenario_path.exists():
            # 如果不存在，尝试在场景目录中直接查找
            scenario_path = self.scenario_dir / f"{scenario_id}.json"
            if not scenario_path.exists():
                self.logger.error(f"场景文件不存在: {scenario_id}")
                raise FileNotFoundError(f"找不到场景文件: {scenario_id}")
        
        self.logger.info(f"加载场景文件: {scenario_path}")
        return self.load_json_file(scenario_path)
    
    def load_all_scenarios(self) -> Dict[str, Dict]:
        """
        加载所有场景数据
        
        Returns:
            场景ID到场景数据的映射字典
        """
        scenarios = {}
        
        # 检查templates目录
        if self.scenario_templates_dir.exists():
            for file_path in self.scenario_templates_dir.glob("*.json"):
                try:
                    scenario = self.load_json_file(file_path)
                    scenario_id = scenario.get("id") or file_path.stem
                    scenarios[scenario_id] = scenario
                except Exception as e:
                    self.logger.warning(f"加载场景文件失败: {e}, 文件: {file_path}")
        
        # 也检查主场景目录下的文件
        for file_path in self.scenario_dir.glob("*.json"):
            # 跳过scenario_pool.json
            if file_path.name == "scenario_pool.json":
                continue
                
            try:
                scenario = self.load_json_file(file_path)
                scenario_id = scenario.get("id") or file_path.stem
                scenarios[scenario_id] = scenario
            except Exception as e:
                self.logger.warning(f"加载场景文件失败: {e}, 文件: {file_path}")
        
        return scenarios
    
    def load_scenario_pool(self) -> Dict:
        """
        加载场景池数据
        
        Returns:
            场景池数据
        """
        pool_path = self.scenario_dir / "scenario_pool.json"
        if not pool_path.exists():
            self.logger.warning(f"场景池文件不存在: {pool_path}")
            return {"version": "1.0", "scenarios": [], "stats": {"total": 0}}
        
        return self.load_json_file(pool_path)
    
    def load_config(self, config_name: str) -> Dict:
        """
        加载配置文件
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置数据
        """
        config_path = self.config_dir / f"{config_name}.json"
        if not config_path.exists():
            self.logger.warning(f"配置文件不存在: {config_path}")
            return {}
        
        return self.load_json_file(config_path)
    
    def save_result(self, result_data: Dict, result_type: str, timestamp: str, id_prefix: str = "") -> str:
        """
        保存结果数据
        
        Args:
            result_data: 结果数据
            result_type: 结果类型（如"dialogue", "evaluation"等）
            timestamp: 时间戳
            id_prefix: ID前缀
            
        Returns:
            结果文件路径
        """
        # 创建结果子目录
        result_subdir = self.results_dir / result_type
        result_subdir.mkdir(parents=True, exist_ok=True)
        
        # 生成结果ID
        result_id = f"{id_prefix}_{timestamp}" if id_prefix else timestamp
        
        # 结果文件路径
        result_path = result_subdir / f"{result_id}.json"
        
        # 保存结果
        self.save_json_file(result_data, result_path)
        
        return str(result_path)
    
    def get_random_character(self) -> Dict:
        """
        随机获取一个角色
        
        Returns:
            随机角色数据
        """
        characters = self.load_all_characters()
        if not characters:
            raise ValueError("未找到任何角色数据")
        
        return random.choice(list(characters.values()))
    
    def get_random_scenario(self) -> Dict:
        """
        随机获取一个场景
        
        Returns:
            随机场景数据
        """
        scenarios = self.load_all_scenarios()
        if not scenarios:
            raise ValueError("未找到任何场景数据")
        
        return random.choice(list(scenarios.values()))
    
    def match_character_scenario(self, character_id: Optional[str] = None, scenario_id: Optional[str] = None) -> Tuple[Dict, Dict]:
        """
        匹配角色和场景
        
        Args:
            character_id: 指定角色ID，如不指定则随机选择
            scenario_id: 指定场景ID，如不指定则随机选择
            
        Returns:
            (角色数据, 场景数据)
        """
        if character_id:
            character = self.load_character(character_id)
        else:
            character = self.get_random_character()
        
        # 获取所有可用的场景
        available_scenarios = list(self.load_all_scenarios().keys())
        if not available_scenarios:
            raise ValueError("未找到任何可用的场景")
            
        if scenario_id:
            # 尝试加载指定场景
            try:
                scenario = self.load_scenario(scenario_id)
                return character, scenario
            except FileNotFoundError:
                self.logger.warning(f"指定的场景不存在: {scenario_id}，将使用可用场景")
                scenario_id = None  # 重置为None，使用随机逻辑
        
        # 如果没有指定场景或指定场景不存在
        if not scenario_id:
            # 如果角色有指定的冲突场景，则从中选择一个可用的
            if "conflict_scenarios" in character and character["conflict_scenarios"]:
                # 过滤出实际存在的场景
                available_conflict_scenarios = []
                for s_id in character["conflict_scenarios"]:
                    try:
                        self.load_scenario(s_id)  # 测试场景是否存在
                        available_conflict_scenarios.append(s_id)
                    except FileNotFoundError:
                        continue
                
                if available_conflict_scenarios:
                    # 从可用的冲突场景中随机选择
                    scenario_id = random.choice(available_conflict_scenarios)
                    scenario = self.load_scenario(scenario_id)
                    return character, scenario
                else:
                    self.logger.warning(f"角色 {character.get('id')} 的所有指定场景都不存在，将随机选择场景")
            
            # 如果没有可用的指定场景，则从所有可用场景中随机选择
            scenario_id = random.choice(available_scenarios)
            scenario = self.load_scenario(scenario_id)
        
        return character, scenario
    
    def load_dialogue_history(self, dialogue_id: str) -> Dict:
        """
        加载对话历史记录
        
        Args:
            dialogue_id: 对话ID
            
        Returns:
            对话历史记录数据
            
        Raises:
            FileNotFoundError: 对话文件不存在
        """
        # 支持包含和不包含扩展名的文件名
        if not dialogue_id.endswith('.json'):
            dialogue_id = f"{dialogue_id}.json"
            
        dialogue_path = self.dialogues_dir / dialogue_id
        
        if not dialogue_path.exists():
            self.logger.error(f"对话历史记录文件不存在: {dialogue_path}")
            raise FileNotFoundError(f"找不到对话历史记录文件: {dialogue_id}")
        
        self.logger.info(f"加载对话历史记录: {dialogue_path}")
        dialogue_data = self.load_json_file(dialogue_path)
        
        # 缓存加载的对话数据
        self._dialogues_cache[dialogue_id] = dialogue_data
        
        return dialogue_data
    
    def save_dialogue_history(self, dialogue_data: Dict, dialogue_id: Optional[str] = None) -> str:
        """
        保存对话历史记录
        
        Args:
            dialogue_data: 对话历史记录数据
            dialogue_id: 对话ID，如果为None则使用对话数据中的ID或生成新ID
            
        Returns:
            对话文件路径
        """
        # 如果没有提供对话ID，尝试从数据中获取
        if dialogue_id is None:
            dialogue_id = dialogue_data.get("id")
            
        # 如果数据中也没有ID，生成一个基于时间戳的ID
        if dialogue_id is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dialogue_id = f"dialogue_{timestamp}"
            
        # 确保有.json扩展名
        if not dialogue_id.endswith('.json'):
            dialogue_id = f"{dialogue_id}.json"
        
        # 设置对话ID到数据中
        dialogue_data["id"] = dialogue_id.replace('.json', '')
        
        # 对话文件路径
        dialogue_path = self.dialogues_dir / dialogue_id
        
        # 保存对话数据
        success = self.save_json_file(dialogue_data, dialogue_path)
        
        if success:
            self.logger.info(f"对话历史记录已保存: {dialogue_path}")
            # 更新缓存
            self._dialogues_cache[dialogue_id] = dialogue_data
            return str(dialogue_path)
        else:
            self.logger.error(f"保存对话历史记录失败: {dialogue_path}")
            return ""
    
    def list_dialogue_files(self) -> List[str]:
        """
        列出所有对话历史记录文件
        
        Returns:
            对话文件ID列表
        """
        dialogue_files = []
        
        for file_path in self.dialogues_dir.glob("*.json"):
            # 提取不带扩展名的文件名作为对话ID
            dialogue_id = file_path.stem
            dialogue_files.append(dialogue_id)
            
        return dialogue_files


# 简单测试用例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建数据加载器
    loader = DataLoader()
    
    # 测试对话历史记录功能
    try:
        # 创建示例对话数据
        dialogue_data = {
            "id": "test_dialogue",
            "character_id": "char_001",
            "scenario_id": "scenario_005",
            "timestamp": "20240501120000",
            "history": [
                {
                    "role": "user",
                    "content": "你好，我们可以聊聊吗？",
                    "timestamp": "20240501120005"
                },
                {
                    "role": "character",
                    "content": "当然可以，请问有什么可以帮助你的？",
                    "timestamp": "20240501120010"
                }
            ],
            "metadata": {
                "emotion_state": {"joy": 0.7, "anger": 0.1, "sadness": 0.1, "fear": 0.1}
            }
        }
        
        # 保存对话数据
        dialogue_path = loader.save_dialogue_history(dialogue_data)
        print(f"对话历史记录已保存: {dialogue_path}")
        
        # 列出所有对话文件
        dialogue_files = loader.list_dialogue_files()
        print(f"对话文件列表: {dialogue_files}")
        
        # 加载刚保存的对话数据
        loaded_dialogue = loader.load_dialogue_history("test_dialogue")
        print(f"加载的对话ID: {loaded_dialogue['id']}")
        print(f"对话历史记录消息数: {len(loaded_dialogue['history'])}")
        
    except Exception as e:
        print(f"对话历史记录操作失败: {e}") 