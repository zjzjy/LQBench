"""
虚拟人物模拟器，用于模拟情侣对话并评估情绪变化
"""

import os
import json
import time
import random
import re  # 添加缺失的re模块导入
from typing import Dict, List, Any, Optional, Tuple, Union

from LQBench.api.llm import LLMClient
from LQBench.api.data.personality_types import personality_types
from LQBench.api.data.relationship_beliefs import relationship_beliefs
from LQBench.api.data.communication_types import communication_types
from LQBench.api.data.attachment_styles import attachment_styles
from LQBench.api.data.emotions import emotions, emotion_scoring
from LQBench.api.data.conflict_scenarios import conflict_scenarios
from LQBench.api.data.character_profiles import character_template, sample_characters, create_character_profile
from LQBench.api.data.prompt_templates import (
    character_prompt_template, 
    partner_prompt_template, 
    dialogue_analysis_template,
    emotion_assessment_template,
    emotion_prediction_template,
    expert_emotion_analysis_template
)

class CharacterSimulator:
    """模拟虚拟人物的情侣对话"""
    
    def __init__(
        self, 
        character_config: Optional[Dict[str, Any]] = None,
        scenario_id: Optional[str] = None,
        character_api: str = "deepseek",
        partner_api: str = "openrouter",
        expert_apis: List[str] = ["deepseek"],  # 修改为列表，支持多个API
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
            character_api (str): 虚拟人物使用的API类型
            partner_api (str): 对话伴侣使用的API类型
            expert_apis (List[str]): 专家分析使用的API类型列表
            max_turns (int): 最大对话轮次
            log_dir (str): 日志目录
            use_emotion_prediction (bool): 是否启用待测模型的情感预测
            use_expert_analysis (bool): 是否启用专家的情感分析
            num_experts (int): 专家数量
        """
        # 初始化API客户端
        self.character_client = LLMClient(api_type=character_api)
        self.partner_client = LLMClient(api_type=partner_api)
        self.expert_apis = expert_apis  # 存储专家API列表
        
        # 设置模拟参数
        self.max_turns = max_turns
        self.log_dir = log_dir
        self.use_emotion_prediction = use_emotion_prediction
        self.use_expert_analysis = use_expert_analysis
        self.num_experts = num_experts
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 初始化角色和场景
        self.character = character_config or random.choice(sample_characters)
        self.scenario = self._get_scenario(scenario_id)
        
        # 初始化对话状态
        self.dialogue_history = []
        self.emotion_history = []
        self.emotion_prediction_history = []  # 存储待测模型的情感预测
        self.expert_analysis_history = []  # 存储专家的情感分析
        self.current_emotion_score = emotion_scoring["baseline"]
        self.turn_count = 0
        
        # 初始化提示词
        self._prepare_prompts()
    
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
        """从数据列表中查找指定ID的项目"""
        for item in data_list:
            if item["id"] == item_id:
                return item
        return None
    
    def _prepare_prompts(self):
        """准备角色和伴侣的提示词"""
        # 查找性格类型
        personality = self._get_data_by_id(personality_types, self.character["personality_type"])
        relationship_belief = self._get_data_by_id(relationship_beliefs, self.character["relationship_belief"])
        communication_type = self._get_data_by_id(communication_types, self.character["communication_type"])
        attachment_style = self._get_data_by_id(attachment_styles, self.character["attachment_style"])
        
        # 准备冲突描述
        conflict_description = (
            f"{self.scenario['scenario']['name']} - {self.scenario['situation']['name']}: "
            f"{self.scenario['situation']['description']}。例如：{self.scenario['situation']['example']}"
        )
        
        # 格式化角色提示词
        self.character_prompt = character_prompt_template.format(
            name=self.character["name"],
            age=self.character["age"],
            gender=self.character["gender"],
            background=self.character["background"],
            personality_description=personality["description"] if personality else "普通性格",
            relationship_belief_description=relationship_belief["description"] if relationship_belief else "无特定关系信念",
            communication_style_description=communication_type["interaction_style"] if communication_type else "一般沟通方式",
            attachment_style_description=attachment_style["description"] if attachment_style else "无特定依恋类型",
            trigger_topics=", ".join(self.character["trigger_topics"]),
            coping_mechanisms=", ".join(self.character["coping_mechanisms"]),
            conflict_description=conflict_description
        )
        
        # 准备伴侣提示词
        partner_gender = "男" if self.character["gender"] == "女" else "女"
        self.partner_prompt = partner_prompt_template.format(
            character_name=self.character["name"],
            conflict_description=conflict_description
        )
        
        # 保存初始提示词
        self._log_prompts()
    
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
        解析虚拟人物回复中的情绪评估
        
        参数:
            response (str): 虚拟人物的回复
            
        返回:
            Dict[str, Any]: 解析后的情绪信息，包含情绪类型、强度和评分
        """
        # 提取内心独白部分
        inner_thoughts = ""
        if "【内心】" in response:
            parts = response.split("【内心】")
            if len(parts) >= 3:
                inner_thoughts = parts[1].strip()
            response = response.replace(f"【内心】{inner_thoughts}【内心】", "").strip()
        
        # 默认情绪评估结果
        emotion_result = {
            "response": response,  # 去除内心独白后的回复
            "inner_thoughts": inner_thoughts,  # 内心独白
            "primary_emotion": "未知",  # 主要情绪
            "intensity": 0,  # 情绪强度
            "score": 0,  # 情绪评分
            "explanation": ""  # 解释
        }
        
        # 尝试从内心独白中提取情绪信息
        if inner_thoughts:
            # 提取情绪评分
            score_match = re.search(r"情绪[评值分]+[：:]\s*([-+]?\d+)", inner_thoughts)
            if score_match:
                try:
                    emotion_result["score"] = int(score_match.group(1))
                except ValueError:
                    pass
            
            # 提取主要情绪和强度
            for emotion in emotions:
                if emotion["name"] in inner_thoughts:
                    emotion_result["primary_emotion"] = emotion["name"]
                    # 尝试提取强度
                    intensity_match = re.search(r"强度[：:]\s*(\d+)", inner_thoughts)
                    if intensity_match:
                        try:
                            emotion_result["intensity"] = int(intensity_match.group(1))
                        except ValueError:
                            pass
                    break
            
            # 提取解释
            explanation_match = re.search(r"原因[:：](.*?)(?:\n|$)", inner_thoughts, re.DOTALL)
            if explanation_match:
                emotion_result["explanation"] = explanation_match.group(1).strip()
        
        return emotion_result
    
    def _update_emotion_score(self, emotion_info: Dict[str, Any]):
        """更新情绪评分"""
        # 使用虚拟人物自我评估的分数
        if "score" in emotion_info and emotion_info["score"] != 0:
            self.current_emotion_score = max(
                min(emotion_info["score"], emotion_scoring["max_positive"]), 
                emotion_scoring["max_negative"]
            )
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
                
            self.current_emotion_score = max(
                min(self.current_emotion_score + adjustment, emotion_scoring["max_positive"]), 
                emotion_scoring["max_negative"]
            )
        
        # 记录情绪历史
        self.emotion_history.append({
            "turn": self.turn_count,
            "emotion_info": emotion_info,
            "score": self.current_emotion_score
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
        personality = self._get_data_by_id(personality_types, self.character["personality_type"])
        personality_description = personality["description"] if personality else "普通性格"
        
        # 准备冲突描述
        conflict_description = (
            f"{self.scenario['scenario']['name']} - {self.scenario['situation']['name']}: "
            f"{self.scenario['situation']['description']}"
        )
        
        # 格式化预测提示词
        prediction_prompt = emotion_prediction_template.format(
            character_name=self.character["name"],
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
        personality = self._get_data_by_id(personality_types, self.character["personality_type"])
        relationship_belief = self._get_data_by_id(relationship_beliefs, self.character["relationship_belief"])
        communication_type = self._get_data_by_id(communication_types, self.character["communication_type"])
        attachment_style = self._get_data_by_id(attachment_styles, self.character["attachment_style"])
        
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
            character_name=self.character["name"],
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
                expert_client = LLMClient(api_type=expert_api)
                
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
                            "emotion_score": self._extract_int(expert_response, r'(emotion_score|情绪分数|情绪评分)["\s:：]+([-]?\d+)', 2, 0),
                            "key_triggers": self._extract_list(expert_response, r'(key_triggers|触发点)["\s:：]+\[(.*?)\]', 2),
                            "analysis": self._extract_value(expert_response, r'(analysis|分析)["\s:：]+([^"]+)', 2, "")
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
                        "key_triggers": [],
                        "analysis": f"解析失败: {str(e)}",
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
                    "key_triggers": [],
                    "analysis": f"API调用失败: {str(e)}",
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
        
        return False
    
    def simulate_turn(self) -> Dict[str, Any]:
        """
        模拟单轮对话
        
        返回:
            Dict[str, Any]: 对话轮次结果
        """
        self.turn_count += 1
        print(f"\n=== 轮次 {self.turn_count} ===")
        
        if self.turn_count > 1:
            # 在虚拟人物回复前，让待测模型预测情绪（除了第一轮）
            emotion_prediction = self._predict_emotion()
            print(f"情绪预测: {emotion_prediction}")
        
        # 构建对话历史消息列表（用于发送给虚拟人物）
        character_messages = []
        if self.turn_count == 1:
            # 第一轮，使用系统提示词
            character_messages.append({"role": "system", "content": self.character_prompt})
        else:
            # 后续轮次，添加对话历史
            for turn in self.dialogue_history:
                character_messages.append({"role": "user", "content": turn["partner_message"]})
                character_messages.append({"role": "assistant", "content": turn["character_message"]})
        
        # 构建伴侣的对话历史消息列表
        partner_messages = []
        if self.turn_count == 1:
            # 第一轮，使用系统提示词
            partner_messages.append({"role": "system", "content": self.partner_prompt})
        else:
            # 后续轮次，添加对话历史
            for turn in self.dialogue_history:
                partner_messages.append({"role": "user", "content": turn["character_message"]})
                partner_messages.append({"role": "assistant", "content": turn["partner_message"]})
        
        # 虚拟人物先发言（第一轮）或回复伴侣（后续轮次）
        if self.turn_count == 1:
            # 第一轮，虚拟人物先发言
            print(f"虚拟人物 {self.character['name']} 第一轮发言...")
            character_response, _ = self.character_client.create_chat_completion(
                messages=character_messages,
                temperature=0.8
            )
        else:
            # 后续轮次，虚拟人物回复伴侣的上一轮发言
            last_partner_message = self.dialogue_history[-1]["partner_message"]
            print(f"虚拟人物 {self.character['name']} 回复...")
            character_messages.append({"role": "user", "content": last_partner_message})
            
            character_response, _ = self.character_client.create_chat_completion(
                messages=character_messages,
                temperature=0.8
            )
        
        # 解析虚拟人物的回复，提取情绪信息
        emotion_info = self._parse_emotion(character_response)
        character_message = emotion_info["response"]  # 去除内心独白后的回复
        
        # 更新情绪评分
        self._update_emotion_score(emotion_info)
        
        # 打印虚拟人物回复
        print(f"{self.character['name']}: {character_message}")
        if emotion_info["inner_thoughts"]:
            print(f"内心独白: {emotion_info['inner_thoughts']}")
        print(f"情绪: {emotion_info['primary_emotion']} (强度: {emotion_info['intensity']}, 评分: {emotion_info['score']})")
        
        # 使用专家模型分析当前情绪
        expert_analyses = self._analyze_with_experts()
        if expert_analyses:
            print("\n专家情感分析:")
            for analysis in expert_analyses:
                print(f"专家 {analysis['expert_id']}: {analysis['primary_emotion']} (强度: {analysis['intensity']}, 分数: {analysis['emotion_score']})")
                print(f"分析: {analysis['analysis']}")
        
        # 检查是否应该结束对话
        if self.should_end_dialogue():
            print("\n对话应该结束")
            turn_result = {
                "turn": self.turn_count,
                "character_name": self.character["name"],
                "character_message": character_message,
                "emotion_info": emotion_info,
                "partner_message": None,
                "emotion_prediction": self.emotion_prediction_history[-1] if self.emotion_prediction_history else None,
                "expert_analyses": expert_analyses,
                "dialogue_ended": True
            }
            
            # 添加到对话历史
            self.dialogue_history.append(turn_result)
            
            return turn_result
        
        # 伴侣回复虚拟人物
        print(f"伴侣回复...")
        partner_messages.append({"role": "user", "content": character_message})
        
        partner_response, _ = self.partner_client.create_chat_completion(
            messages=partner_messages,
            temperature=0.8
        )
        
        print(f"伴侣: {partner_response}")
        
        # 记录本轮对话
        turn_result = {
            "turn": self.turn_count,
            "character_name": self.character["name"],
            "character_message": character_message,
            "emotion_info": emotion_info,
            "partner_message": partner_response,
            "emotion_prediction": self.emotion_prediction_history[-1] if self.emotion_prediction_history else None,
            "expert_analyses": expert_analyses,
            "dialogue_ended": False
        }
        
        # 添加到对话历史
        self.dialogue_history.append(turn_result)
        
        return turn_result
    
    def run_simulation(self) -> Dict[str, Any]:
        """
        运行完整的对话模拟
        
        返回:
            Dict[str, Any]: 包含完整对话历史和情绪变化的结果
        """
        print(f"开始模拟: {self.character['name']} - {self.scenario['situation']['name']}")
        
        while not self.should_end_dialogue():
            turn_result = self.simulate_turn()
            
            # 打印当前轮次信息
            print(f"\n--- 轮次 {self.turn_count} ---")
            if "partner_message" in turn_result and turn_result["partner_message"] is not None:
                if self.dialogue_history[-2]["speaker"] == "partner":
                    print(f"伴侣: {turn_result['partner_message']}")
                    print(f"{self.character['name']}: {turn_result['character_message']}")
                else:
                    print(f"{self.character['name']}: {turn_result['character_message']}")
                    print(f"伴侣: {turn_result['partner_message']}")
            else:
                print(f"{self.character['name']}: {turn_result['character_message']}")
            
            print(f"内心独白: {turn_result['inner_thoughts']}")
            print(f"情绪评分: {turn_result['emotion_score']}")
            
            if turn_result.get("dialogue_ended", False):
                print(f"\n对话结束: {turn_result.get('end_reason', '未知原因')}")
                break
        
        # 保存对话记录
        self._save_dialogue_log()
        
        return {
            "character": self.character,
            "scenario": self.scenario,
            "dialogue_history": self.dialogue_history,
            "emotion_history": self.emotion_history,
            "emotion_prediction_history": self.emotion_prediction_history,
            "expert_analysis_history": self.expert_analysis_history,
            "final_emotion_score": self.current_emotion_score,
            "turns_completed": self.turn_count
        }
    
    def _save_dialogue_log(self):
        """保存对话日志到文件"""
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