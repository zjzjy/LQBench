import json
import logging
import jsonschema
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path

class DataValidator:
    """
    数据验证工具，用于验证各种输入数据的格式和内容
    """
    
    def __init__(self, schemas_dir: Optional[str] = None):
        """
        初始化数据验证工具
        
        Args:
            schemas_dir: JSON Schema目录，默认为None，使用默认目录
        """
        self.logger = logging.getLogger(__name__)
        
        if schemas_dir is None:
            # 获取当前文件所在目录，拼接默认schema目录
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.schemas_dir = base_dir / "src" / "utils" / "schemas"
        else:
            self.schemas_dir = Path(schemas_dir)
        
        # 确保schema目录存在
        self.schemas_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化默认schema
        self._initialize_default_schemas()
        
        # 加载schema
        self.schemas = {}
        for schema_type in ["character", "scenario", "dialogue", "emotion", "evaluation"]:
            schema_path = self.schemas_dir / f"{schema_type}_schema.json"
            if schema_path.exists():
                try:
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        self.schemas[schema_type] = json.load(f)
                except Exception as e:
                    self.logger.error(f"加载{schema_type} schema失败: {e}")
    
    def _initialize_default_schemas(self) -> None:
        """
        初始化默认JSON Schema
        """
        # 角色Schema
        character_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["id", "name", "gender", "age", "personality", "attachment_style", "communication_style"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "gender": {"type": "string", "enum": ["male", "female", "other"]},
                "age": {"type": "integer", "minimum": 18},
                "personality": {
                    "type": "object",
                    "required": ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"],
                    "properties": {
                        "openness": {"type": "integer", "minimum": 0, "maximum": 100},
                        "conscientiousness": {"type": "integer", "minimum": 0, "maximum": 100},
                        "extraversion": {"type": "integer", "minimum": 0, "maximum": 100},
                        "agreeableness": {"type": "integer", "minimum": 0, "maximum": 100},
                        "neuroticism": {"type": "integer", "minimum": 0, "maximum": 100}
                    }
                },
                "attachment_style": {
                    "type": "string", 
                    "enum": ["secure", "anxious", "avoidant", "fearful"]
                },
                "communication_style": {
                    "type": "string", 
                    "enum": ["passive", "aggressive", "passive-aggressive", "assertive"]
                },
                "background": {
                    "type": "object",
                    "properties": {
                        "childhood": {"type": "string"},
                        "education": {"type": "string"},
                        "career": {"type": "string"},
                        "hobbies": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "values": {"type": "array", "items": {"type": "string"}},
                "speech_patterns": {
                    "type": "object",
                    "properties": {
                        "common_phrases": {"type": "array", "items": {"type": "string"}},
                        "communication_examples": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "conflict_scenarios": {"type": "array", "items": {"type": "string"}}
            }
        }
        
        # 场景Schema
        scenario_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["id", "type", "title", "description", "intensity", "context"],
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "intensity": {"type": "string", "enum": ["low", "medium", "high"]},
                "context": {"type": "string"},
                "background": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string"},
                        "location": {"type": "string"},
                        "relationship_context": {"type": "string"},
                        "recent_events": {"type": "string"}
                    }
                },
                "character_perspective": {
                    "type": "object",
                    "properties": {
                        "interpretation": {"type": "string"},
                        "expectations": {"type": "string"},
                        "fears": {"type": "string"}
                    }
                },
                "partner_reality": {
                    "type": "object",
                    "properties": {
                        "situation": {"type": "string"},
                        "intentions": {"type": "string"},
                        "awareness": {"type": "string"}
                    }
                },
                "cognitive_appraisal": {
                    "type": "object",
                    "properties": {
                        "primary": {"type": "string"},
                        "secondary": {"type": "string"}
                    }
                },
                "expected_reactions": {
                    "type": "object",
                    "properties": {
                        "emotional": {"type": "array", "items": {"type": "string"}},
                        "behavioral": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "initial_dialogue": {"type": "string"}
            }
        }
        
        # 对话条目Schema
        dialogue_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["role", "content"],
            "properties": {
                "role": {"type": "string", "enum": ["character", "partner"]},
                "content": {"type": "string"}
            }
        }
        
        # 情绪数据Schema
        emotion_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["primary_emotion", "emotion_intensity"],
            "properties": {
                "turn": {"type": "integer", "minimum": 1},
                "primary_emotion": {"type": "string"},
                "secondary_emotions": {"type": "array", "items": {"type": "string"}},
                "emotion_intensity": {"type": "integer", "minimum": 0, "maximum": 100},
                "explanation": {"type": "string"},
                "suggested_response_tone": {"type": "string"}
            }
        }
        
        # 评估结果Schema
        evaluation_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["emotional_intelligence", "communication_effectiveness", "relationship_development"],
            "properties": {
                "emotional_intelligence": {
                    "type": "object",
                    "required": ["emotion_recognition", "emotion_response", "empathy"],
                    "properties": {
                        "emotion_recognition": {
                            "type": "object",
                            "required": ["score", "comment"],
                            "properties": {
                                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                "comment": {"type": "string"}
                            }
                        },
                        "emotion_response": {
                            "type": "object",
                            "required": ["score", "comment"],
                            "properties": {
                                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                "comment": {"type": "string"}
                            }
                        },
                        "empathy": {
                            "type": "object",
                            "required": ["score", "comment"],
                            "properties": {
                                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                "comment": {"type": "string"}
                            }
                        }
                    }
                },
                "communication_effectiveness": {
                    "type": "object",
                    "required": ["active_listening", "clarity", "technique", "conflict_resolution"],
                    "properties": {
                        "active_listening": {
                            "type": "object",
                            "required": ["score", "comment"],
                            "properties": {
                                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                "comment": {"type": "string"}
                            }
                        },
                        "clarity": {
                            "type": "object",
                            "required": ["score", "comment"],
                            "properties": {
                                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                "comment": {"type": "string"}
                            }
                        },
                        "technique": {
                            "type": "object",
                            "required": ["score", "comment"],
                            "properties": {
                                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                "comment": {"type": "string"}
                            }
                        },
                        "conflict_resolution": {
                            "type": "object",
                            "required": ["score", "comment"],
                            "properties": {
                                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                "comment": {"type": "string"}
                            }
                        }
                    }
                },
                "relationship_development": {
                    "type": "object",
                    "required": ["trust_building", "intimacy_change", "satisfaction_change", "long_term_potential"],
                    "properties": {
                        "trust_building": {
                            "type": "object",
                            "required": ["score", "comment"],
                            "properties": {
                                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                "comment": {"type": "string"}
                            }
                        },
                        "intimacy_change": {
                            "type": "object",
                            "required": ["score", "comment"],
                            "properties": {
                                "score": {"type": "integer", "minimum": -100, "maximum": 100},
                                "comment": {"type": "string"}
                            }
                        },
                        "satisfaction_change": {
                            "type": "object",
                            "required": ["score", "comment"],
                            "properties": {
                                "score": {"type": "integer", "minimum": -100, "maximum": 100},
                                "comment": {"type": "string"}
                            }
                        },
                        "long_term_potential": {
                            "type": "object",
                            "required": ["score", "comment"],
                            "properties": {
                                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                "comment": {"type": "string"}
                            }
                        }
                    }
                },
                "overall_evaluation": {
                    "type": "object",
                    "properties": {
                        "model_style": {"type": "string"},
                        "strengths": {"type": "string"},
                        "areas_for_improvement": {"type": "string"},
                        "summary": {"type": "string"}
                    }
                }
            }
        }
        
        # 保存默认schema
        schemas = {
            "character": character_schema,
            "scenario": scenario_schema,
            "dialogue": dialogue_schema,
            "emotion": emotion_schema,
            "evaluation": evaluation_schema
        }
        
        for schema_type, schema in schemas.items():
            schema_path = self.schemas_dir / f"{schema_type}_schema.json"
            if not schema_path.exists():
                with open(schema_path, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, ensure_ascii=False, indent=2)
                self.logger.info(f"创建默认{schema_type} schema: {schema_path}")
    
    def validate_data(self, data: Dict, schema_type: str) -> Tuple[bool, str]:
        """
        验证数据是否符合指定的schema
        
        Args:
            data: 待验证的数据字典
            schema_type: schema类型，如"character"、"scenario"等
            
        Returns:
            (验证是否通过, 错误信息)
        """
        if schema_type not in self.schemas:
            return False, f"未找到{schema_type} schema"
        
        schema = self.schemas[schema_type]
        
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True, ""
        except jsonschema.exceptions.ValidationError as e:
            error_message = f"验证失败: {e.message}"
            self.logger.warning(error_message)
            return False, error_message
    
    def validate_character(self, character_data: Dict) -> Tuple[bool, str]:
        """
        验证角色数据
        
        Args:
            character_data: 角色数据字典
            
        Returns:
            (验证是否通过, 错误信息)
        """
        return self.validate_data(character_data, "character")
    
    def validate_scenario(self, scenario_data: Dict) -> Tuple[bool, str]:
        """
        验证场景数据
        
        Args:
            scenario_data: 场景数据字典
            
        Returns:
            (验证是否通过, 错误信息)
        """
        return self.validate_data(scenario_data, "scenario")
    
    def validate_dialogue_entry(self, dialogue_entry: Dict) -> Tuple[bool, str]:
        """
        验证对话条目
        
        Args:
            dialogue_entry: 对话条目字典
            
        Returns:
            (验证是否通过, 错误信息)
        """
        return self.validate_data(dialogue_entry, "dialogue")
    
    def validate_emotion_data(self, emotion_data: Dict) -> Tuple[bool, str]:
        """
        验证情绪数据
        
        Args:
            emotion_data: 情绪数据字典
            
        Returns:
            (验证是否通过, 错误信息)
        """
        return self.validate_data(emotion_data, "emotion")
    
    def validate_evaluation_result(self, evaluation_data: Dict) -> Tuple[bool, str]:
        """
        验证评估结果
        
        Args:
            evaluation_data: 评估结果字典
            
        Returns:
            (验证是否通过, 错误信息)
        """
        return self.validate_data(evaluation_data, "evaluation")
    
    def validate_api_response(self, response: Dict) -> Tuple[bool, str]:
        """
        验证API响应是否符合预期格式
        
        Args:
            response: API响应字典
            
        Returns:
            (验证是否通过, 错误信息)
        """
        # 简单检查是否包含必要的字段
        if "choices" not in response or not isinstance(response["choices"], list) or len(response["choices"]) == 0:
            return False, "API响应缺少有效的choices字段"
        
        if "message" not in response["choices"][0] or "content" not in response["choices"][0]["message"]:
            return False, "API响应缺少message.content字段"
        
        return True, ""
    
    def validate_json_string(self, json_string: str) -> Tuple[bool, Dict, str]:
        """
        验证并解析JSON字符串
        
        Args:
            json_string: JSON字符串
            
        Returns:
            (验证是否通过, 解析后的数据字典, 错误信息)
        """
        try:
            data = json.loads(json_string)
            return True, data, ""
        except json.JSONDecodeError as e:
            error_message = f"JSON解析失败: {str(e)}"
            self.logger.warning(error_message)
            return False, {}, error_message
    
    def extract_json_from_llm_response(self, response_text: str) -> Tuple[bool, Dict, str]:
        """
        从大模型响应中提取JSON
        
        Args:
            response_text: 大模型响应文本
            
        Returns:
            (提取是否成功, 提取的JSON数据, 错误信息)
        """
        # 尝试直接解析
        try:
            data = json.loads(response_text)
            return True, data, ""
        except json.JSONDecodeError:
            # 尝试找到JSON块
            json_start = response_text.find("```json")
            if json_start != -1:
                json_end = response_text.find("```", json_start + 7)
                if json_end != -1:
                    json_text = response_text[json_start + 7:json_end].strip()
                    try:
                        data = json.loads(json_text)
                        return True, data, ""
                    except json.JSONDecodeError as e:
                        return False, {}, f"JSON块解析失败: {str(e)}"
                else:
                    return False, {}, "找到JSON块开始标记，但未找到结束标记"
            else:
                # 尝试使用正则表达式查找可能的JSON部分
                import re
                json_pattern = r'(\{[\s\S]*?\})'
                matches = re.findall(json_pattern, response_text)
                
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, dict) and len(data) > 1:  # 确保这是一个有意义的JSON对象
                            return True, data, ""
                    except:
                        continue
                
                return False, {}, "无法在响应中找到有效的JSON"


# 简单测试用例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建数据验证工具
    validator = DataValidator()
    
    # 测试角色验证
    test_character = {
        "id": "test_char",
        "name": "测试角色",
        "gender": "male",
        "age": 25,
        "personality": {
            "openness": 70,
            "conscientiousness": 60,
            "extraversion": 80,
            "agreeableness": 50,
            "neuroticism": 40
        },
        "attachment_style": "anxious",
        "communication_style": "passive-aggressive"
    }
    
    is_valid, error = validator.validate_character(test_character)
    print(f"角色验证: {'通过' if is_valid else '失败'}, 错误: {error}")
    
    # 测试JSON提取
    test_response = """
    以下是评估结果：
    
    ```json
    {
      "primary_emotion": "anger",
      "secondary_emotions": ["disappointment", "hurt"],
      "emotion_intensity": 75,
      "explanation": "角色对伴侣未回复消息感到愤怒，暗含被忽视的失望"
    }
    ```
    
    希望这个评估对你有帮助。
    """
    
    is_success, data, error = validator.extract_json_from_llm_response(test_response)
    print(f"JSON提取: {'成功' if is_success else '失败'}, 数据: {data}, 错误: {error}") 