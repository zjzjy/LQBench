"""
虚拟人物模拟器，用于模拟情侣对话场景中的角色行为
"""

import os
import json
import time
import random
import re  # 添加缺失的re模块导入
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import sys

# 删除绝对导入路径，只保留相对导入
from api.llm import LLMClient
from api.data.personality_types import personality_types
from api.data.relationship_beliefs import relationship_beliefs
from api.data.communication_types import communication_types
from api.data.attachment_styles import attachment_styles
from api.data.emotions import emotions, emotion_scoring
from api.data.conflict_scenarios import conflict_scenarios, get_scenario_by_id, get_situation_by_id
from api.data.character_profiles import character_profiles, get_character_by_scenario
from api.data.prompt_templates import (
    character_prompt_template, 
    partner_prompt_template, 
    dialogue_analysis_template,
    emotion_prediction_template,
    expert_emotion_analysis_template,
    dialogue_appraisal_template
)

class CharacterSimulator:
    """模拟虚拟人物的情侣对话"""
    
    def __init__(
        self, 
        character_config: Optional[Dict[str, Any]] = None,
        scenario_id: Optional[str] = None,
        situation_id: Optional[str] = None,
        character_api: str = "deepseek",
        partner_api: str = "openrouter",
        expert_apis: List[str] = ["deepseek"],  # 修改为列表，支持多个API
        character_model: Optional[str] = None,
        partner_model: Optional[str] = None,
        expert_model: Optional[str] = None,
        max_turns: int = 10,
        log_dir: str = "logs",
        use_emotion_prediction: bool = True,
        use_expert_analysis: bool = True,
        num_experts: int = 3
    ):
        """
        初始化虚拟人物模拟器
        
        参数:
            character_config (Dict[str, Any], optional): 虚拟人物配置
            scenario_id (str, optional): 冲突场景ID
            situation_id (str, optional): 具体情境ID
            character_api (str): 虚拟人物使用的API类型
            partner_api (str): 对话伴侣使用的API类型
            expert_apis (List[str]): 专家分析使用的API类型列表
            character_model (str, optional): 虚拟人物使用的模型名称
            partner_model (str, optional): 对话伴侣使用的模型名称
            expert_model (str, optional): 专家分析使用的模型名称
            max_turns (int): 最大对话轮次
            log_dir (str): 日志目录
            use_emotion_prediction (bool): 是否启用待测模型的情感预测
            use_expert_analysis (bool): 是否启用专家的情感分析
            num_experts (int): 专家数量
        """
        # 初始化API客户端
        self.character_client = LLMClient(api_type=character_api, model_name=character_model)
        self.partner_client = LLMClient(api_type=partner_api, model_name=partner_model)
        self.expert_apis = expert_apis  # 存储专家API列表
        self.expert_model = expert_model  # 存储专家模型名称
        
        # 设置模拟参数
        self.max_turns = max_turns
        self.log_dir = log_dir
        self.use_emotion_prediction = use_emotion_prediction
        self.use_expert_analysis = use_expert_analysis
        self.num_experts = num_experts
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 初始化角色和场景
        if character_config and scenario_id:
            self.character = character_config
            scenario = get_scenario_by_id(scenario_id)
            if not scenario:
                raise ValueError(f"未找到场景: {scenario_id}")
            
            if situation_id:
                situation = get_situation_by_id(scenario_id, situation_id)
                if not situation:
                    raise ValueError(f"未找到情境: {situation_id}")
            else:
                situation = random.choice(scenario["situations"])
            
            self.scenario = {
                "scenario": scenario,
                "situation": situation
            }
        else:
            # 如果未提供配置，随机选择一个场景和对应的角色
            scenario = random.choice(conflict_scenarios)
            situation = random.choice(scenario["situations"])
            self.character = get_character_by_scenario(scenario["id"], situation["id"])
            if not self.character:
                raise ValueError(f"未找到场景 {scenario['id']} 情境 {situation['id']} 对应的角色配置")
            
            self.scenario = {
                "scenario": scenario,
                "situation": situation
            }
        
        # 初始化对话状态
        self.dialogue_history = []
        self.emotion_history = []
        self.emotion_prediction_history = []  # 存储待测模型的情感预测
        self.expert_analysis_history = []  # 存储专家的情感分析
        
        # 设置初始情绪值，确保在合理范围内
        # 根据情境的严重程度设置初始情绪值
        # 避免设置过高或过低的初始值，以防一开始就触发对话结束
        initial_emotion = self._calculate_initial_emotion()
        self.current_emotion_score = max(
            min(initial_emotion, 
                emotion_scoring["threshold"]["improvement"] - 1),  # 不超过改善阈值
                emotion_scoring["threshold"]["critical"] + 1  # 不低于临界阈值
        )
        
        self.turn_count = 0
        
        # 初始化提示词
        self._prepare_prompts()
    
    def _calculate_initial_emotion(self) -> int:
        """
        根据场景和角色特征计算初始情绪值
        
        返回:
            int: 初始情绪值，范围在临界阈值和改善阈值之间
        """
        # 获取情绪临界阈值
        critical_threshold = emotion_scoring["threshold"]["critical"]  # 现在是-10
        improvement_threshold = emotion_scoring["threshold"]["improvement"]  # 现在是7
        
        # 安全起见，设置初始情绪值范围
        min_emotion = critical_threshold + 3  # 确保至少比临界阈值高3，避免过早结束
        max_emotion = improvement_threshold - 1  # 不超过改善阈值
        
        # 根据场景和角色特征适当调整基础情绪值
        # 通常角色开始时会处于中性偏负面情绪状态
        base_emotion = random.randint(min_emotion, min(min_emotion + 5, -1))
        
        # 考虑角色的性格特征进行微调
        personality_type = self.character.get("personality_type", "")
        is_neurotic = "neuroticism_high" in personality_type
        is_optimistic = "openness_high" in personality_type
        
        # 微调但不要突破安全边界
        if is_neurotic:
            base_emotion = max(base_emotion - 2, min_emotion)
        if is_optimistic:
            base_emotion = min(base_emotion + 2, max_emotion)
        
        print(f"初始情绪值: {base_emotion} (允许范围: {min_emotion} 到 {max_emotion})")
        return base_emotion
    
    def _get_scenario(self, scenario_id: Optional[str] = None) -> Dict[str, Any]:
        """获取冲突场景"""
        if scenario_id:
            # 查找指定ID的场景
            for scenario in conflict_scenarios:
                if scenario["id"] == scenario_id:
                    # 随机选择一个具体情境
                    situation = random.choice(scenario["situations"])
                    return {
                        "scenario": scenario,
                        "situation": situation
                    }
            # 如果未找到指定ID，使用随机场景
            print(f"未找到ID为 {scenario_id} 的场景，将使用随机场景")
            
        # 随机选择场景和情境
        scenario = random.choice(conflict_scenarios)
        situation = random.choice(scenario["situations"])
        return {
            "scenario": scenario,
            "situation": situation
        }
    
    def _get_data_by_id(self, data_list: List[Dict[str, Any]], item_id: str) -> Optional[Dict[str, Any]]:
        """从数据列表中查找指定ID的项目，支持多个ID（以逗号分隔）"""
        if not item_id:
            return None
        
        # 如果是多个ID，只取第一个
        first_id = item_id.split(',')[0].strip()
        
        for item in data_list:
            if item["id"] == first_id:
                return item
        return None
    
    def _prepare_prompts(self):
        """准备角色和伴侣的提示词"""
        try:
            # 查找性格类型
            personality = self._get_data_by_id(personality_types, self.character.get("personality_type"))
            relationship_belief = self._get_data_by_id(relationship_beliefs, self.character.get("relationship_belief"))
            communication_type = self._get_data_by_id(communication_types, self.character.get("communication_type"))
            attachment_style = self._get_data_by_id(attachment_styles, self.character.get("attachment_style"))
            
            # 准备冲突描述
            conflict_description = (
                f"{self.scenario['scenario']['name']} - {self.scenario['situation']['name']}: "
                f"{self.scenario['situation']['description']}。例如：{self.scenario['situation']['example']}"
            )
            
            # 打印关键字段以便于调试
            print(f"Name: {self.character.get('name', '未知')}")
            print(f"Age: {self.character.get('age', 25)}")
            print(f"Gender: {self.character.get('gender', '未知')}")
            print(f"Background: {self.character.get('background', '无背景信息')}")
            print(f"Trigger topics: {', '.join(self.character.get('trigger_topics', []))}")
            print(f"Coping mechanisms: {', '.join(self.character.get('coping_mechanisms', []))}")
            
            # 格式化角色提示词 - 直接指定所有必需参数
            self.character_prompt = character_prompt_template.format(
                name=self.character.get("name", "未知"),
                age=self.character.get("age", 25),
                gender=self.character.get("gender", "未知"),
                background=self.character.get("background", "无背景信息"),
                personality_description=personality["description"] if personality else "普通性格",
                relationship_belief_description=relationship_belief["description"] if relationship_belief else "无特定关系信念",
                communication_style_description=communication_type["interaction_style"] if communication_type else "一般沟通方式",
                attachment_style_description=attachment_style["description"] if attachment_style else "无特定依恋类型",
                trigger_topics=", ".join(self.character.get("trigger_topics", [])),
                coping_mechanisms=", ".join(self.character.get("coping_mechanisms", [])),
                conflict_description=conflict_description
            )
            
            # 准备伴侣提示词
            partner_gender = "男" if self.character.get("gender") == "女" else "女"
            self.partner_prompt = partner_prompt_template.format(
                character_name=self.character.get("name", "未知"),
                conflict_description=conflict_description
            )
            
            # 保存初始提示词
            self._log_prompts()
            
        except Exception as e:
            print(f"准备提示词时出错: {str(e)}")
            # 打印更多详细错误信息
            import traceback
            traceback.print_exc()
            raise
    
    def _log_prompts(self):
        """记录提示词到日志文件"""
        prompts_log = {
            "character": {
                "config": self.character,
                "prompt": self.character_prompt
            },
            "scenario": self.scenario,
            "partner_prompt": self.partner_prompt
        }
        
        log_file = os.path.join(
            self.log_dir, 
            f"{self.character['id']}_{self.scenario['situation']['id']}_{int(time.time())}_prompts.json"
        )
        
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(prompts_log, f, ensure_ascii=False, indent=2)
    
    def _parse_emotion(self, response: str) -> Dict[str, Any]:
        """
        初始化虚拟人物默认情绪信息，由于角色不再自行评估情绪，
        这个方法返回一个空的情绪信息对象，实际情绪由专家分析提供
        
        参数:
            response (str): 虚拟人物的回复
            
        返回:
            Dict[str, Any]: 初始情绪信息
        """
        # 默认情绪评估结果
        emotion_result = {
            "emotions": [],  # 情绪类型列表
            "score": self.current_emotion_score,  # 使用当前情绪评分
        }
        
        return emotion_result
    
    def _update_emotion_score(self, emotion_info: Dict[str, Any]):
        """更新情绪评分"""
        # 保存上一轮情绪评分
        previous_score = self.current_emotion_score
        
        # 使用虚拟人物自我评估的分数
        if "score" in emotion_info and emotion_info["score"] != 0:
            new_score = emotion_info["score"]
        # 如果没有评分，根据情绪类型和强度估算
        elif "primary_emotion" in emotion_info and "intensity" in emotion_info:
            # 积极情绪
            if emotion_info["primary_emotion"] in ["快乐", "信任", "期待"]:
                adjustment = emotion_info["intensity"]
            # 消极情绪
            elif emotion_info["primary_emotion"] in ["愤怒", "悲伤", "恐惧", "厌恶"]:
                adjustment = -emotion_info["intensity"]
            # 中性情绪
            else:
                adjustment = 0
                
            new_score = self.current_emotion_score + adjustment
        else:
            # 如果没有足够信息计算新的情绪分数，保持不变
            new_score = self.current_emotion_score
        
        # 限制情绪变化幅度
        max_change = emotion_scoring.get("max_change_per_turn", 3)
        if new_score > previous_score:
            # 正向变化：限制最大增长
            change = min(new_score - previous_score, max_change)
            new_score = previous_score + change
        else:
            # 负向变化：限制最大下降
            change = min(previous_score - new_score, max_change)
            new_score = previous_score - change
        
        # 确保分数在合法范围内
        self.current_emotion_score = max(
            min(new_score, emotion_scoring["max_positive"]), 
            emotion_scoring["max_negative"]
        )
        
        # 记录情绪历史
        self.emotion_history.append({
            "turn": self.turn_count,
            "emotion_info": emotion_info,
            "score": self.current_emotion_score,
            "previous_score": previous_score,
            "change": self.current_emotion_score - previous_score
        })
    
    def _predict_emotion(self) -> Dict[str, Any]:
        """
        使用待测模型预测虚拟人物的下一轮情绪状态
        
        返回:
            Dict[str, Any]: 预测的情绪信息
        """
        if not self.use_emotion_prediction or not self.dialogue_history:
            return {}
        
        # 准备对话历史
        dialogue_text = "\n".join([
            f"轮次 {i+1}:\n" +
            f"{turn['character_name']}: {turn['character_message']}\n" +
            f"你: {turn['partner_message']}\n"
            for i, turn in enumerate(self.dialogue_history)
        ])
        
        # 获取人物性格描述
        personality = self._get_data_by_id(personality_types, self.character.get("personality_type"))
        personality_description = personality["description"] if personality else "普通性格"
        
        # 准备冲突描述
        conflict_description = (
            f"{self.scenario['scenario']['name']} - {self.scenario['situation']['name']}: "
            f"{self.scenario['situation']['description']}"
        )
        
        # 格式化预测提示词
        prediction_prompt = emotion_prediction_template.format(
            character_name=self.character.get("name", "未知"),
            dialogue_history=dialogue_text,
            personality_description=personality_description,
            conflict_description=conflict_description
        )
        
        # 调用待测模型进行预测
        try:
            prediction_response, _ = self.partner_client.call(
                prompt=prediction_prompt,
                temperature=0.5
            )
            
            # 尝试从响应中提取JSON
            try:
                # 尝试提取JSON格式的预测结果
                json_match = re.search(r'\{[^{]*"predicted_emotion"[^}]*\}', prediction_response, re.DOTALL)
                if json_match:
                    prediction_json = json.loads(json_match.group(0))
                else:
                    # 如果没有找到标准JSON，尝试基于关键词提取
                    prediction_json = {
                        "predicted_emotion": self._extract_value(prediction_response, r'(predicted_emotion|情绪)["\s:：]+([^",]+)', 2, "未知"),
                        "intensity": self._extract_int(prediction_response, r'(intensity|强度)["\s:：]+(\d+)', 2, 0),
                        "emotion_score": self._extract_int(prediction_response, r'(emotion_score|情绪分数|情绪评分)["\s:：]+([-]?\d+)', 2, 0),
                        "explanation": self._extract_value(prediction_response, r'(explanation|解释)["\s:：]+([^"]+)', 2, "")
                    }
                
                # 添加预测时间和轮次信息
                prediction_json["turn"] = self.turn_count
                prediction_json["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
                
                # 保存预测历史
                self.emotion_prediction_history.append(prediction_json)
                
                return prediction_json
            except Exception as e:
                print(f"解析情绪预测JSON失败: {str(e)}")
                print(f"原始响应: {prediction_response}")
                
                # 返回空预测结果
                empty_prediction = {
                    "turn": self.turn_count,
                    "predicted_emotion": "未知",
                    "intensity": 0,
                    "emotion_score": 0,
                    "explanation": f"解析失败: {str(e)}",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.emotion_prediction_history.append(empty_prediction)
                return empty_prediction
        except Exception as e:
            print(f"情绪预测API调用失败: {str(e)}")
            
            # 返回空预测结果
            empty_prediction = {
                "turn": self.turn_count,
                "predicted_emotion": "未知",
                "intensity": 0,
                "emotion_score": 0,
                "explanation": f"API调用失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.emotion_prediction_history.append(empty_prediction)
            return empty_prediction
    
    def _analyze_with_experts(self) -> List[Dict[str, Any]]:
        """
        使用多个专家模型分析虚拟人物的当前情绪状态
        
        返回:
            List[Dict[str, Any]]: 专家分析结果列表
        """
        if not self.use_expert_analysis or not self.dialogue_history:
            return []
        
        # 准备对话历史
        dialogue_text = "\n".join([
            f"轮次 {i+1}:\n" +
            f"{turn['character_name']}: {turn['character_message']}\n" +
            f"测试对象: {turn['partner_message']}\n"
            for i, turn in enumerate(self.dialogue_history)
        ])
        
        # 获取人物特质描述
        personality = self._get_data_by_id(personality_types, self.character.get("personality_type"))
        relationship_belief = self._get_data_by_id(relationship_beliefs, self.character.get("relationship_belief"))
        communication_type = self._get_data_by_id(communication_types, self.character.get("communication_type"))
        attachment_style = self._get_data_by_id(attachment_styles, self.character.get("attachment_style"))
        
        personality_description = personality["description"] if personality else "普通性格"
        relationship_belief_description = relationship_belief["description"] if relationship_belief else "无特定关系信念"
        communication_style_description = communication_type["interaction_style"] if communication_type else "一般沟通方式"
        attachment_style_description = attachment_style["description"] if attachment_style else "无特定依恋类型"
        
        # 准备冲突描述
        conflict_description = (
            f"{self.scenario['scenario']['name']} - {self.scenario['situation']['name']}: "
            f"{self.scenario['situation']['description']}"
        )
        
        # 格式化专家分析提示词
        expert_prompt = expert_emotion_analysis_template.format(
            character_name=self.character.get("name", "未知"),
            personality_description=personality_description,
            relationship_belief_description=relationship_belief_description,
            communication_style_description=communication_style_description,
            attachment_style_description=attachment_style_description,
            conflict_description=conflict_description,
            dialogue_history=dialogue_text,
            turn_number=self.turn_count
        )
        
        expert_analyses = []
        
        # 调用专家模型进行分析
        for i in range(self.num_experts):
            try:
                # 选择对应的专家API
                expert_api = self.expert_apis[i % len(self.expert_apis)]  # 循环使用API列表
                expert_client = LLMClient(api_type=expert_api, model_name=self.expert_model)
                
                expert_response, _ = expert_client.call(
                    prompt=expert_prompt,
                    temperature=0.2 + (i * 0.1)  # 每个专家使用略微不同的温度
                )
                
                # 尝试从响应中提取JSON
                try:
                    # 尝试提取JSON格式的分析结果
                    json_match = re.search(r'\{[^{]*"primary_emotion"[^}]*\}', expert_response, re.DOTALL)
                    if json_match:
                        expert_json = json.loads(json_match.group(0))
                    else:
                        # 如果没有找到标准JSON，尝试基于关键词提取
                        expert_json = {
                            "primary_emotion": self._extract_value(expert_response, r'(primary_emotion|主要情绪)["\s:：]+([^",]+)', 2, "未知"),
                            "intensity": self._extract_int(expert_response, r'(intensity|强度)["\s:：]+(\d+)', 2, 0),
                            "emotion_score": self._extract_int(expert_response, r'(emotion_score|情绪分数|情绪评分)["\s:：]+([-]?\d+)', 2, 0)
                        }
                    
                    # 添加专家ID、分析时间和轮次信息
                    expert_json["expert_id"] = f"expert_{i+1}"
                    expert_json["turn"] = self.turn_count
                    expert_json["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    expert_analyses.append(expert_json)
                except Exception as e:
                    print(f"解析专家分析JSON失败: {str(e)}")
                    print(f"原始响应: {expert_response}")
                    
                    # 添加失败的分析结果
                    expert_analyses.append({
                        "expert_id": f"expert_{i+1}",
                        "turn": self.turn_count,
                        "primary_emotion": "未知",
                        "intensity": 0,
                        "emotion_score": 0,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
            except Exception as e:
                print(f"专家分析API调用失败: {str(e)}")
                
                # 添加失败的分析结果
                expert_analyses.append({
                    "expert_id": f"expert_{i+1}",
                    "turn": self.turn_count,
                    "primary_emotion": "未知",
                    "intensity": 0,
                    "emotion_score": 0, 
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # 保存专家分析历史
        self.expert_analysis_history.append({
            "turn": self.turn_count,
            "analyses": expert_analyses
        })
        
        return expert_analyses
    
    def _extract_value(self, text: str, pattern: str, group: int, default: str = "") -> str:
        """从文本中提取特定模式的值"""
        match = re.search(pattern, text, re.DOTALL)
        return match.group(group).strip() if match else default
    
    def _extract_int(self, text: str, pattern: str, group: int, default: int = 0) -> int:
        """从文本中提取整数值"""
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return int(match.group(group).strip())
            except ValueError:
                return default
        return default
    
    def _extract_list(self, text: str, pattern: str, group: int) -> List[str]:
        """从文本中提取列表值"""
        match = re.search(pattern, text, re.DOTALL)
        if match:
            items_str = match.group(group).strip()
            # 处理不同格式的列表表示
            items = []
            # 尝试找到所有被引号包围的项
            quoted_items = re.findall(r'"([^"]*)"', items_str)
            if quoted_items:
                items = quoted_items
            else:
                # 尝试按逗号分割
                items = [item.strip() for item in items_str.split(",") if item.strip()]
            return items
        return []
    
    def should_end_dialogue(self) -> bool:
        """
        判断对话是否应该结束
        
        返回:
            bool: True表示应该结束，False表示可以继续
        """
        # 达到最大轮次
        if self.turn_count >= self.max_turns:
            return True
        
        # 情绪明显好转
        if (len(self.emotion_history) >= 3 and
            self.current_emotion_score >= emotion_scoring["threshold"]["improvement"]):
            return True
        
        # 情绪达到极度负面
        if self.current_emotion_score <= emotion_scoring["threshold"]["critical"]:
            return True
            
        # 情绪长期持续恶化（连续3轮以上下降且总下降超过6分）
        if len(self.emotion_history) >= 3:
            consecutive_worsening = 0
            total_change = 0
            
            for i in range(len(self.emotion_history) - 1, max(len(self.emotion_history) - 4, -1), -1):
                if i > 0 and self.emotion_history[i]["score"] < self.emotion_history[i-1]["score"]:
                    consecutive_worsening += 1
                    total_change += self.emotion_history[i-1]["score"] - self.emotion_history[i]["score"]
                else:
                    break
            
            if consecutive_worsening >= 3 and total_change >= 6:
                return True
        
        return False
    
    def _check_and_fix_character_response(self, response: str, character_messages: List[Dict[str, str]]) -> str:
        """
        检查虚拟人物回复是否符合格式要求，如果不符合则尝试修复
        
        参数:
            response: 原始回复内容
            character_messages: 对话历史消息列表
            
        返回:
            str: 修复后的回复内容
        """
        # 初步检查是否包含常见问题
        has_issues = (
            len(response.strip()) == 0 or 
            "I " in response or 
            "am " in response or 
            response.count(" ") > response.count("，") * 2 or
            "(" in response or ")" in response or  # 检查是否包含圆括号（可能表示动作）
            "*" in response or  # 检查是否包含星号（可能表示动作）
            "[" in response or "]" in response or  # 检查是否包含方括号（可能表示动作）
            "<" in response or ">" in response or  # 检查是否包含尖括号（可能表示标签）
            "【" in response or "】" in response or  # 检查是否包含中文方括号（可能表示内心独白）
            ":" in response or "：" in response or  # 检查是否包含冒号（可能表示动作描述）
            re.search(r'（.*?）', response) is not None  # 检查是否包含中文圆括号（可能表示动作）
        )
        
        if not has_issues:
            return response
            
        print("警告: 虚拟人物回复不符合要求，可能使用了英文或包含动作描述，尝试重新生成...")
        
        # 使用DeepSeek检查回复是否符合标准
        checker_prompt = f"""
请检查以下对话回复是否符合标准，这一点非常重要，必须严格判断：

回复内容：{response}

检查标准：
1. 必须是纯中文，没有任何英文
2. 不包含任何动作描述，如"(微笑)"、"*叹气*"、"【内心独白】"、"（突然眼睛一亮）"等
3. 符合真实人类对话风格，不包含人工标记
4. 不包含冒号、括号等可能表示动作或内心活动的符号
5. 检查英文括号() 和中文括号（）内是否包含动作描述

如果发现任何一条不符合，请直接回答"不符合"，否则回答"符合"。
"""
        
        try:
            # 创建临时的DeepSeek客户端进行检查
            checker_client = LLMClient(api_type="deepseek")
            check_result, _ = checker_client.call(prompt=checker_prompt, temperature=0.1)
            
            # 如果检查结果显示不符合标准，进行修复
            if "不符合" in check_result:
                # 找到系统提示词
                system_prompt = next((msg["content"] for msg in character_messages if msg["role"] == "system"), "")
                if system_prompt:
                    # 第一次尝试就使用系统提示词进行修复
                    retry_prompt_with_system = f"""
你的回复不符合要求。请仔细阅读以下系统提示，并严格按照要求回复：

{system_prompt}

请记住：
1. 必须使用纯中文回复
2. 不要包含任何动作描述或表情，不要使用任何形式的括号
3. 不要使用任何特殊符号如括号、星号等
4. 回复要简短自然，像真实的聊天对话
5. 不要包含内心独白或元叙述
6. 不要包含类似"(微笑)"、"（叹气）"、"【内心独白】"这样的内容

错误示例：
"（突然眼睛一亮）那...那我们现在去看电影好不好？"（错误：包含动作描述）
"哼，上次卸载了第二天又偷偷装回来（生气）"（错误：包含表情描述）

正确示例：
"那...那我们现在去看电影好不好？"
"哼，上次卸载了第二天又偷偷装回来"

请重新回复：
"""
                    character_messages.append({"role": "user", "content": retry_prompt_with_system})
                    fixed_response, _ = self.character_client.create_chat_completion(
                        messages=character_messages,
                        temperature=0.4
                    )
                    
                    # 再次检查修复后的回复
                    second_check_prompt = f"""
请检查以下对话回复是否符合标准，这一点非常重要，必须严格判断：

回复内容：{fixed_response}

检查标准：
1. 必须是纯中文，没有任何英文
2. 不包含任何动作描述，如"(微笑)"、"*叹气*"、"【内心独白】"、"（突然眼睛一亮）"等
3. 符合真实人类对话风格，不包含人工标记
4. 不包含冒号、括号等可能表示动作或内心活动的符号
5. 检查英文括号() 和中文括号（）内是否包含动作描述

如果发现任何一条不符合，请直接回答"不符合"，否则回答"符合"。
"""
                    second_check_result, _ = checker_client.call(prompt=second_check_prompt, temperature=0.1)
                    
                    # 如果第一次修复后仍不符合标准，进行第二次尝试（加强措辞）
                    if "不符合" in second_check_result:
                        retry_prompt_strong = f"""
你的回复仍然不符合要求。我需要你非常严格地遵守以下规则：

1. 只输出纯中文文本，没有任何其他内容
2. 绝对不要包含任何动作描述、表情符号或特殊标记
3. 不要使用任何英文单词
4. 不要使用任何括号、星号、方括号等特殊符号
5. 不要包含冒号
6. 不要包含任何内心独白
7. 回复必须像真实人类在手机上发的消息一样简短自然

例如，不要写"（突然眼睛一亮）那...那我们现在去看电影好不好？"，
而应该只写"那...那我们现在去看电影好不好？"

请重新回复（只需回复消息内容，不要添加任何额外内容）：
"""
                        character_messages.append({"role": "user", "content": retry_prompt_strong})
                        fixed_response, _ = self.character_client.create_chat_completion(
                            messages=character_messages,
                            temperature=0.3
                        )
                    
                    return fixed_response
                else:
                    # 如果没有找到系统提示词，使用简单提示
                    retry_prompt = "你的回复不符合要求。请记住：1. 必须使用中文回复；2. 不要使用英文；3. 不要包含任何动作描述或内心独白；4. 不要使用括号、星号、方括号等符号；5. 回复要像真实人类对话一样简短自然。请重新回复："
                    character_messages.append({"role": "user", "content": retry_prompt})
                    fixed_response, _ = self.character_client.create_chat_completion(
                        messages=character_messages,
                        temperature=0.4
                    )
                    return fixed_response
            
        except Exception as e:
            print(f"检查回复格式时出错: {str(e)}")
        
        # 如果检查过程出错或检查通过，返回原始回复
        return response
    
    def _check_and_fix_partner_response(self, response: str, partner_messages: List[Dict[str, str]]) -> str:
        """
        检查伴侣回复是否符合格式要求，如果不符合则尝试修复
        
        参数:
            response: 原始回复内容
            partner_messages: 对话历史消息列表
            
        返回:
            str: 修复后的回复内容
        """
        # 初步检查是否包含常见问题
        has_issues = (
            len(response.strip()) == 0 or 
            "I " in response or 
            "am " in response or 
            response.count(" ") > response.count("，") * 2 or
            "(" in response or ")" in response or  # 检查是否包含圆括号（可能表示动作）
            "*" in response or  # 检查是否包含星号（可能表示动作）
            "[" in response or "]" in response or  # 检查是否包含方括号（可能表示动作）
            "<" in response or ">" in response or  # 检查是否包含尖括号（可能表示标签）
            "【" in response or "】" in response or  # 检查是否包含中文方括号（可能表示内心独白）
            ":" in response or "：" in response or  # 检查是否包含冒号（可能表示动作描述）
            re.search(r'（.*?）', response) is not None  # 检查是否包含中文圆括号（可能表示动作）
        )
        
        if not has_issues:
            return response
            
        print("警告: 伴侣回复不符合要求，可能使用了英文或包含动作描述，尝试重新生成...")
        
        # 使用DeepSeek检查回复是否符合标准
        checker_prompt = f"""
请检查以下对话回复是否符合标准，这一点非常重要，必须严格判断：

回复内容：{response}

检查标准：
1. 必须是纯中文，没有任何英文
2. 不包含任何动作描述，如"(微笑)"、"*叹气*"、"【内心独白】"、"（突然眼睛一亮）"等
3. 符合真实人类对话风格，不包含人工标记
4. 不包含冒号、括号等可能表示动作或内心活动的符号
5. 检查英文括号() 和中文括号（）内是否包含动作描述

如果发现任何一条不符合，请直接回答"不符合"，否则回答"符合"。
"""
        
        try:
            # 创建临时的DeepSeek客户端进行检查
            checker_client = LLMClient(api_type="deepseek")
            check_result, _ = checker_client.call(prompt=checker_prompt, temperature=0.1)
            
            # 如果检查结果显示不符合标准，进行修复
            if "不符合" in check_result:
                # 找到系统提示词
                system_prompt = next((msg["content"] for msg in partner_messages if msg["role"] == "system"), "")
                if system_prompt:
                    # 第一次尝试就使用系统提示词进行修复
                    retry_prompt_with_system = f"""
你的回复不符合要求。请仔细阅读以下系统提示，并严格按照要求回复：

{system_prompt}

请记住：
1. 必须使用纯中文回复
2. 不要包含任何动作描述或表情，不要使用任何形式的括号
3. 不要使用任何特殊符号如括号、星号等
4. 回复要简短自然，像真实的聊天对话
5. 不要包含内心独白或元叙述
6. 不要包含类似"(微笑)"、"（叹气）"、"【内心独白】"这样的内容

错误示例：
"（委屈巴巴地拉着你的手）那...那我把游戏卸载好不好？"（错误：包含动作描述）
"宝贝我错了嘛（放下手机凑过来）这次真的不打了"（错误：包含动作描述）

请重新回复：
"""
                    partner_messages.append({"role": "user", "content": retry_prompt_with_system})
                    fixed_response, _ = self.partner_client.create_chat_completion(
                        messages=partner_messages,
                        temperature=0.4
                    )
                    
                    # 再次检查修复后的回复
                    second_check_prompt = f"""
请检查以下对话回复是否符合标准，这一点非常重要，必须严格判断：

回复内容：{fixed_response}

检查标准：
1. 必须是纯中文，没有任何英文
2. 不包含任何动作描述，如"(微笑)"、"*叹气*"、"【内心独白】"、"（突然眼睛一亮）"等
3. 符合真实人类对话风格，不包含人工标记
4. 不包含冒号、括号等可能表示动作或内心活动的符号
5. 检查英文括号() 和中文括号（）内是否包含动作描述

如果发现任何一条不符合，请直接回答"不符合"，否则回答"符合"。
"""
                    second_check_result, _ = checker_client.call(prompt=second_check_prompt, temperature=0.1)
                    
                    # 如果第一次修复后仍不符合标准，进行第二次尝试（加强措辞）
                    if "不符合" in second_check_result:
                        retry_prompt_strong = f"""
你的回复仍然不符合要求。我需要你非常严格地遵守以下规则：

1. 只输出纯中文文本，没有任何其他内容
2. 绝对不要包含任何动作描述、表情符号或特殊标记
3. 不要使用任何英文单词
4. 不要使用任何括号、星号、方括号等特殊符号
5. 不要包含冒号
6. 不要包含任何内心独白
7. 回复必须像真实人类在手机上发的消息一样简短自然

例如，不要写"（委屈巴巴地拉着你的手）那...那我把游戏卸载好不好？"，
而应该只写"那...那我把游戏卸载好不好？"

请重新回复（只需回复消息内容，不要添加任何额外内容）：
"""
                        partner_messages.append({"role": "user", "content": retry_prompt_strong})
                        fixed_response, _ = self.partner_client.create_chat_completion(
                            messages=partner_messages,
                            temperature=0.3
                        )
                    
                    return fixed_response
                else:
                    # 如果没有找到系统提示词，使用简单提示
                    retry_prompt = "你的回复不符合要求。请记住：1. 必须使用中文回复；2. 不要使用英文；3. 不要包含任何动作描述或内心独白；4. 不要使用括号、星号、方括号等符号；5. 回复要像真实人类对话一样简短自然。请重新回复："
                    partner_messages.append({"role": "user", "content": retry_prompt})
                    fixed_response, _ = self.partner_client.create_chat_completion(
                        messages=partner_messages,
                        temperature=0.4
                    )
                    return fixed_response
            
        except Exception as e:
            print(f"检查回复格式时出错: {str(e)}")
        
        # 如果检查过程出错或检查通过，返回原始回复
        return response
    
    def simulate_turn(self) -> Dict[str, Any]:
        """
        模拟单轮对话
        
        返回:
            Dict[str, Any]: 对话轮次结果
        """
        self.turn_count += 1
        print(f"\n=== 轮次 {self.turn_count} ===")
        
        # 构建对话历史消息列表（用于发送给虚拟人物）
        character_messages = []
        if self.turn_count == 1:
            # 第一轮，使用系统提示词
            character_messages.append({"role": "system", "content": self.character_prompt})
            # 添加一个用户消息来初始化对话
            character_messages.append({"role": "user", "content": "你好，最近怎么样？（请记住你是在一个情侣对话场景中，必须使用中文回复，并表现出相应的情绪和性格特点）"})
        else:
            # 后续轮次，添加对话历史
            # 首先添加系统提示词强化角色扮演要求
            character_messages.append({"role": "system", "content": "你正在扮演一个情侣对话中的角色，必须始终使用中文回复，不允许使用任何英文。请根据你的人物设定和当前对话情境自然回应。禁止输出与角色扮演无关的内容。"})
            for turn in self.dialogue_history:
                character_messages.append({"role": "user", "content": turn["partner_message"]})
                character_messages.append({"role": "assistant", "content": turn["character_message"]})
        
        # 构建伴侣的对话历史消息列表
        partner_messages = []
        if self.turn_count == 1:
            # 第一轮，使用系统提示词
            partner_messages.append({"role": "system", "content": self.partner_prompt})
            # 添加一个初始化消息
            partner_messages.append({"role": "user", "content": "请根据上面的指示，扮演角色的男/女朋友。你必须使用中文回复，表达你对当前冲突的观点或感受。"})
        else:
            # 后续轮次，添加对话历史
            # 首先添加系统提示词强化角色扮演要求
            partner_messages.append({"role": "system", "content": "你正在扮演情侣对话中的一方，必须始终使用中文回复，不允许使用任何英文。请根据当前对话情境自然回应，不要留空不回复。"})
            for turn in self.dialogue_history:
                partner_messages.append({"role": "user", "content": turn["character_message"]})
                partner_messages.append({"role": "assistant", "content": turn["partner_message"]})
        
        # 虚拟人物先发言（第一轮）或回复伴侣（后续轮次）
        if self.turn_count == 1:
            # 第一轮，虚拟人物先发言
            print(f"虚拟人物 {self.character['name']} 第一轮发言...")
            character_response, _ = self.character_client.create_chat_completion(
                messages=character_messages,
                temperature=0.6  # 降低温度以获得更确定性的回复
            )
        else:
            # 后续轮次，虚拟人物回复伴侣的上一轮发言
            last_partner_message = self.dialogue_history[-1]["partner_message"]
            print(f"虚拟人物 {self.character['name']} 回复...")
            character_messages.append({"role": "user", "content": last_partner_message})
            
            character_response, _ = self.character_client.create_chat_completion(
                messages=character_messages,
                temperature=0.6  # 降低温度以获得更确定性的回复
            )
        
        # 使用新方法检查并修复虚拟人物回复
        character_response = self._check_and_fix_character_response(character_response, character_messages)
        
        # 初始化默认情绪信息
        emotion_info = self._parse_emotion(character_response)
        
        # 保存完整响应用于日志和专家分析
        full_character_response = character_response
        
        # 打印虚拟人物回复
        print(f"{self.character['name']}: {full_character_response}")
        
        # 如果启用了专家分析，使用专家分析的情绪评估
        if self.use_expert_analysis:
            # 记录本轮对话（用于专家分析）
            temp_turn = {
                "turn": self.turn_count,
                "character_name": self.character.get("name", "未知"),
                "character_message": full_character_response,
                "partner_message": self.dialogue_history[-1]["partner_message"] if self.dialogue_history else "",
                "dialogue_ended": False
            }
            self.dialogue_history.append(temp_turn)
            
            # 获取专家分析结果
            expert_analyses = self._analyze_with_experts()
            if expert_analyses:
                # 保存当前情绪分数用于计算变化
                previous_score = self.current_emotion_score
                
                # 使用专家分析的平均情绪分数
                total_score = sum(analysis.get("emotion_score", 0) for analysis in expert_analyses)
                avg_score = total_score / len(expert_analyses) if expert_analyses else 0
                new_score = int(avg_score)
                
                # 限制情绪变化幅度
                max_change = emotion_scoring.get("max_change_per_turn", 3)
                if new_score > previous_score:
                    # 正向变化：限制最大增长
                    change = min(new_score - previous_score, max_change)
                    new_score = previous_score + change
                else:
                    # 负向变化：限制最大下降
                    change = min(previous_score - new_score, max_change)
                    new_score = previous_score - change
                    
                # 确保分数在合法范围内
                self.current_emotion_score = max(
                    min(new_score, emotion_scoring["max_positive"]), 
                    emotion_scoring["max_negative"]
                )
                
                # 收集所有专家分析的情绪类型
                emotions = []
                for analysis in expert_analyses:
                    primary_emotion = analysis.get("primary_emotion")
                    if primary_emotion and primary_emotion != "未知":
                        emotions.append(primary_emotion)
                
                # 更新情绪信息
                emotion_info = {
                    "emotions": emotions,
                    "score": self.current_emotion_score,
                    "previous_score": previous_score,
                    "change": self.current_emotion_score - previous_score,
                    "expert_analyses": expert_analyses
                }
                
                # 记录情绪历史
                self.emotion_history.append({
                    "turn": self.turn_count,
                    "emotion_info": emotion_info,
                    "score": self.current_emotion_score,
                    "previous_score": previous_score,
                    "change": self.current_emotion_score - previous_score
                })
                
                print(f"专家分析情绪: {emotions}, 平均评分: {self.current_emotion_score} (变化: {self.current_emotion_score - previous_score})")
            
            # 移除临时添加的对话轮次
            self.dialogue_history.pop()
        
        # 检查是否应该结束对话
        end_reason = None
        if self.turn_count >= self.max_turns:
            end_reason = "达到最大对话轮次"
        elif len(self.emotion_history) >= 3 and self.current_emotion_score >= emotion_scoring["threshold"]["improvement"]:
            end_reason = "情绪明显好转"
        elif self.current_emotion_score <= emotion_scoring["threshold"]["critical"]:
            end_reason = "情绪达到极度负面"
        # 检查长期持续恶化
        elif len(self.emotion_history) >= 3:
            consecutive_worsening = 0
            total_change = 0
            
            for i in range(len(self.emotion_history) - 1, max(len(self.emotion_history) - 4, -1), -1):
                if i > 0 and self.emotion_history[i]["score"] < self.emotion_history[i-1]["score"]:
                    consecutive_worsening += 1
                    total_change += self.emotion_history[i-1]["score"] - self.emotion_history[i]["score"]
                else:
                    break
            
            if consecutive_worsening >= 3 and total_change >= 6:
                end_reason = "情绪持续恶化"
        
        if end_reason:
            #print(f"\n对话结束: {end_reason}")
            turn_result = {
                "turn": self.turn_count,
                "character_name": self.character.get("name", "未知"),
                "character_message": full_character_response,
                "emotion_info": emotion_info,
                "partner_message": None,
                "dialogue_ended": True,
                "end_reason": end_reason
            }
            
            # 添加到对话历史
            self.dialogue_history.append(turn_result)
            
            return turn_result
        
        # 伴侣回复虚拟人物
        print(f"伴侣回复...")
        partner_messages.append({"role": "user", "content": character_response})
        
        partner_response, _ = self.partner_client.create_chat_completion(
            messages=partner_messages,
            temperature=0.6  # 降低温度以获得更确定性的回复
        )
        
        # 使用新方法检查并修复伴侣回复
        partner_response = self._check_and_fix_partner_response(partner_response, partner_messages)
        
        print(f"伴侣: {partner_response}")
        
        # 记录本轮对话
        turn_result = {
            "turn": self.turn_count,
            "character_name": self.character.get("name", "未知"),
            "character_message": full_character_response,
            "emotion_info": emotion_info,
            "partner_message": partner_response,
            "dialogue_ended": False
        }
        
        # 添加到对话历史
        self.dialogue_history.append(turn_result)
        
        return turn_result
    
    def _format_dialogue_history_for_appraisal(self) -> str:
        """格式化对话历史用于appraisal评估"""
        if not self.dialogue_history:
            return ""
            
        dialogue_text = ""
        character_name = self.character.get("name", "未知")
        
        for turn in self.dialogue_history:
            dialogue_text += f"{character_name}: {turn.get('character_message', '')}\n"
            dialogue_text += f"伴侣: {turn.get('partner_message', '')}\n\n"
        
        return dialogue_text

    def _analyze_dialogue_appraisal(self) -> Dict[str, Any]:
        """
        在对话结束后，让partner模型评估整个对话，生成appraisal字段
        
        返回:
            Dict[str, Any]: 包含primary_appraisal和secondary_appraisal的评估结果
        """
        from api.data.prompt_templates import dialogue_appraisal_template
        import time
        import sys
        
        # 设置为False关闭调试输出
        debug_mode = False
        
        def debug_print(msg):
            """打印调试信息到stderr"""
            if debug_mode:
                print(f"DEBUG: {msg}", file=sys.stderr)
                sys.stderr.flush()
            
        debug_print("========== 开始appraisal评估 ==========")
        
        # 如果没有对话历史，无法评估
        if not self.dialogue_history:
            debug_print("警告: 无法评估appraisal，对话历史为空")
            return self._create_default_appraisal("对话历史为空")

        # 构建完整对话历史文本
        dialogue_text = ""
        for turn in self.dialogue_history:
            character_name = self.character.get("name", "未知")
            dialogue_text += f"{character_name}: {turn['character_message']}\n"
            dialogue_text += f"伴侣: {turn['partner_message']}\n\n"
        
        debug_print(f"对话历史构建完成，共 {len(self.dialogue_history)} 轮对话")
        
        # 准备appraisal评估提示
        try:
            debug_print("开始构建appraisal提示词...")
            
            # 获取所需的各个字段
            character_name = self.character.get("name", "未知")
            age = self.character.get("age", "未知")
            gender = self.character.get("gender", "未知")
            background = self.character.get("background", "未知")
            
            # 处理性格描述
            personality_description = self.character.get("personality_description", "")
            if not personality_description and "personality_type" in self.character:
                personality_description = f"性格类型: {self.character.get('personality_type', '未知')}"
            
            # 获取冲突描述
            conflict_description = self.scenario['situation']['description']
            
            # 逐步构建提示词
            appraisal_prompt = dialogue_appraisal_template.format(
                character_name=character_name,
                age=age,
                gender=gender,
                background=background,
                personality_description=personality_description,
                conflict_description=conflict_description,
                full_dialogue_history=dialogue_text
            )
            
            debug_print("提示词构建完成")
            
        except Exception as format_error:
            debug_print(f"构建提示词时出错: {str(format_error)}")
            return self._create_default_appraisal(f"提示词构建错误: {str(format_error)}")
        
        try:
            debug_print("开始调用deepseek API...")
            start_time = time.time()
            
            # 使用LLMClient直接调用API，添加系统提示
            from api.llm import LLMClient
            client = LLMClient()
            response_text = None
            try:
                response_text, appraisal_result = client.call(
                    prompt=appraisal_prompt,
                    model="deepseek-chat",
                    temperature=0.1,
                    max_tokens=500,
                    system_prompt="你是一个JSON处理引擎。只输出有效的JSON格式，不要添加任何其他文本或标记。不要使用markdown代码块。直接输出以{开头，以}结尾的有效JSON。"
                )
                
                debug_print(f"API调用完成，耗时: {time.time() - start_time:.2f}秒")
                debug_print(f"原始响应类型: {type(response_text)}")
                debug_print(f"响应长度: {len(response_text) if response_text else 0}")
                debug_print(f"响应内容: >>>{response_text}<<<")
                
                if not response_text:
                    debug_print("警告: API返回空响应")
                    return self._create_default_appraisal("API返回空响应")
                    
                # 尝试解析JSON
                result = self._clean_and_parse_json(response_text, debug_print)
                return result
                
            except Exception as api_error:
                debug_print(f"API调用或解析出错: {str(api_error)}")
                if response_text:
                    debug_print(f"API返回的响应: >>>{response_text}<<<")
                return self._create_default_appraisal(f"API错误: {str(api_error)}")
                
        except Exception as outer_error:
            debug_print(f"外层异常: {str(outer_error)}")
            import traceback
            traceback.print_exc(file=sys.stderr)
            return self._create_default_appraisal(f"外层错误: {str(outer_error)}")
        finally:
            debug_print("========== 结束appraisal评估 ==========")
            
    def _create_default_appraisal(self, reason: str) -> Dict[str, Any]:
        """创建默认的appraisal结果"""
        return {
            "primary_appraisal": {
                "relevance": "未能解析评估",
                "nature": "未能解析评估"
            },
            "secondary_appraisal": {
                "attribution": "未能解析评估",
                "coping_ability": "未能解析评估",
                "coping_strategy": "未能解析评估"
            }
        }

    def run_simulation(self) -> Dict[str, Any]:
        """
        运行完整的对话模拟
        
        返回:
            Dict[str, Any]: 包含完整对话历史和情绪变化的结果
        """
        print(f"开始模拟: {self.character['name']} - {self.scenario['situation']['name']}")
        
        while not self.should_end_dialogue():
            turn_result = self.simulate_turn()
            
            if turn_result.get("dialogue_ended", False):
                print(f"\n对话结束: {turn_result.get('end_reason', '未知原因')}")
                break
        
        # 对话结束后，生成appraisal评估
        try:
            dialogue_appraisal = self._analyze_dialogue_appraisal()
            print("已生成对话appraisal评估")
        except Exception as e:
            print(f"生成appraisal评估时出错: {str(e)}")
            dialogue_appraisal = self._create_default_appraisal(f"异常: {str(e)}")
        
        # 保存对话记录
        self._save_dialogue_log(dialogue_appraisal)
        
        return {
            "character": self.character,
            "scenario": self.scenario,
            "dialogue_history": self.dialogue_history,
            "emotion_history": self.emotion_history,
            "emotion_prediction_history": self.emotion_prediction_history,
            "expert_analysis_history": self.expert_analysis_history,
            "dialogue_appraisal": dialogue_appraisal,
            "final_emotion_score": self.current_emotion_score,
            "turns_completed": self.turn_count
        }
    
    def _save_dialogue_log(self, dialogue_appraisal=None):
        """
        保存对话日志到文件
        
        参数:
            dialogue_appraisal (Dict[str, Any], optional): 对话appraisal评估结果
        """
        # 准备日志数据
        log_data = {
            "character": self.character,
            "scenario": self.scenario,
            "dialogue_history": self.dialogue_history,
            "emotion_history": self.emotion_history,
            "emotion_prediction_history": self.emotion_prediction_history,
            "expert_analysis_history": self.expert_analysis_history,
            "final_emotion_score": self.current_emotion_score,
            "turns_completed": self.turn_count,
            "max_turns": self.max_turns,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 添加appraisal评估结果（如果有）
        if dialogue_appraisal:
            log_data["dialogue_appraisal"] = dialogue_appraisal
        
        # 生成日志文件名
        log_file = os.path.join(
            self.log_dir, 
            f"{self.character['id']}_{self.scenario['situation']['id']}_{int(time.time())}.json"
        )
        
        # 保存日志
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
            
        print(f"对话日志已保存到: {log_file}")
        
        return log_file

    def _clean_and_parse_json(self, text, debug_print):
        """清理API返回的文本，尝试解析JSON，支持多种可能的格式问题"""
        if not text:
            debug_print("警告: 收到空的文本")
            return self._create_default_appraisal("API返回空响应")

        debug_print(f"原始JSON文本: {text}")
        
        # 1. 清理空白字符和非JSON内容
        cleaned = text.strip()

        # 如果文本不是以{开始或不是以}结束，尝试找到有效的JSON部分
        if not cleaned.startswith('{'):
            debug_print(f"文本不是以'{{''开始: {cleaned[:20]}...")
            # 找到第一个{的位置
            start_pos = cleaned.find('{')
            if start_pos >= 0:
                cleaned = cleaned[start_pos:]
                debug_print(f"截取后的文本: {cleaned[:20]}...")

        if not cleaned.endswith('}'):
            debug_print(f"文本不是以'}}'结束: ...{cleaned[-20:]}")
            # 找到最后一个}的位置
            end_pos = cleaned.rfind('}')
            if end_pos >= 0:
                cleaned = cleaned[:end_pos+1]
                debug_print(f"截取后的文本: ...{cleaned[-20:]}")
                
        # 特殊处理: 检查并修复引号问题
        cleaned = self._fix_quotes(cleaned, debug_print)
        
        # 特殊处理: 删除文本开头的换行符和空格
        cleaned = cleaned.lstrip()
        
        # 2. 尝试直接解析
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            debug_print(f"直接解析JSON失败，错误: {str(e)}")
            return self._create_default_appraisal("JSON解析失败")
        
    def _fix_quotes(self, text, debug_print):
        """修复JSON中可能存在的引号问题"""
        debug_print("尝试修复可能的引号问题")
        
        # 检查是否有未转义的引号问题
        result = text
        
        # 注意：以下部分逻辑可能导致引入无效的控制字符
        # 因此注释掉不必要的替换操作
        """
        # 1. 处理值中的未转义引号 (例如 {"key": "value "with" quotes"})
        pattern = r':[\\s]*"([^"]*)"([^"]*)"([^"]*)"'
        matches = re.finditer(pattern, result)
        for match in matches:
            full = match.group(0)
            fixed = full.replace('"' + match.group(2) + '"', '\\"' + match.group(2) + '\\"')
            result = result.replace(full, fixed)
            debug_print(f"修复了引号问题: {full} -> {fixed}")
        """
            
        # 2. 处理多余的开头引号
        if result.startswith('"') and not result.startswith('{"'):
            result = result[1:]
            debug_print("移除了开头多余的引号")
            
        # 3. 处理多余的结尾引号
        if result.endswith('"') and not result.endswith('"}'):
            result = result[:-1]
            debug_print("移除了结尾多余的引号")
            
        return result

# 如果直接运行此文件，执行示例模拟
if __name__ == "__main__":
    # 创建模拟器实例
    simulator = CharacterSimulator(
        character_config=sample_characters[0],  # 使用第一个示例角色
        max_turns=8,  # 最多8轮对话
        log_dir="logs"  # 日志保存目录
    )
    
    # 运行模拟
    result = simulator.run_simulation()
    
    # 打印摘要
    print("\n=== 对话摘要 ===")
    print(f"角色: {result['character']['name']}")
    print(f"场景: {result['scenario']['situation']['name']}")
    print(f"完成轮次: {result['turns_completed']}")
    print(f"最终情绪评分: {result['final_emotion_score']}")
    
    # 显示情绪变化趋势
    print("\n情绪变化趋势:")
    for emotion in result['emotion_history']:
        print(f"轮次 {emotion['turn']}: {emotion['score']} - {emotion['emotion_info'].get('primary_emotion', '未知')}") 