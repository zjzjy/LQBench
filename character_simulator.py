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
    emotion_assessment_template
)

class CharacterSimulator:
    """模拟虚拟人物的情侣对话"""
    
    def __init__(
        self, 
        character_config: Optional[Dict[str, Any]] = None,
        scenario_id: Optional[str] = None,
        character_api: str = "deepseek",
        partner_api: str = "openrouter",
        max_turns: int = 10,
        log_dir: str = "logs"
    ):
        """
        初始化虚拟人物模拟器
        
        参数:
            character_config (Dict[str, Any], optional): 虚拟人物配置
            scenario_id (str, optional): 冲突场景ID
            character_api (str): 虚拟人物使用的API类型
            partner_api (str): 对话伴侣使用的API类型
            max_turns (int): 最大对话轮次
            log_dir (str): 日志目录
        """
        # 初始化API客户端
        self.character_client = LLMClient(api_type=character_api)
        self.partner_client = LLMClient(api_type=partner_api)
        
        # 设置模拟参数
        self.max_turns = max_turns
        self.log_dir = log_dir
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 初始化角色和场景
        self.character = character_config or random.choice(sample_characters)
        self.scenario = self._get_scenario(scenario_id)
        
        # 初始化对话状态
        self.dialogue_history = []
        self.emotion_history = []
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
        模拟一轮对话
        
        返回:
            Dict[str, Any]: 包含对话内容和情绪信息的结果
        """
        self.turn_count += 1
        
        # 决定谁先说话
        if self.turn_count == 1:
            # 第一轮，随机决定谁先开始
            character_first = random.choice([True, False])
        else:
            # 后续轮次，轮流发言
            character_first = (len(self.dialogue_history) % 2 == 0)
        
        # 准备消息记录
        if self.turn_count == 1:
            # 第一轮，使用初始提示词
            character_messages = [{"role": "system", "content": self.character_prompt}]
            partner_messages = [{"role": "system", "content": self.partner_prompt}]
        else:
            # 后续轮次，包含历史对话
            character_messages = [{"role": "system", "content": self.character_prompt}]
            partner_messages = [{"role": "system", "content": self.partner_prompt}]
            
            # 添加历史对话
            for msg in self.dialogue_history:
                if msg["speaker"] == "character":
                    character_messages.append({"role": "assistant", "content": msg["content"]})
                    partner_messages.append({"role": "user", "content": msg["content"]})
                else:
                    character_messages.append({"role": "user", "content": msg["content"]})
                    partner_messages.append({"role": "assistant", "content": msg["content"]})
        
        # 模拟对话
        if character_first:
            # 如果是第一轮，添加开场白提示
            if self.turn_count == 1:
                character_messages.append({"role": "user", "content": "请开始对话，表达你对这个情境的初始反应。"})
            
            # 虚拟人物先说
            character_response, _ = self.character_client.create_chat_completion(
                messages=character_messages,
                temperature=0.8
            )
            
            # 解析情绪
            emotion_info = self._parse_emotion(character_response)
            self._update_emotion_score(emotion_info)
            
            # 记录对话
            self.dialogue_history.append({
                "turn": self.turn_count,
                "speaker": "character",
                "content": character_response,
                "emotion_info": emotion_info
            })
            
            # 如果对话应该结束，不再继续
            if self.should_end_dialogue():
                return {
                    "turn": self.turn_count,
                    "character_response": emotion_info["response"],
                    "inner_thoughts": emotion_info["inner_thoughts"],
                    "emotion_score": self.current_emotion_score,
                    "partner_response": None,
                    "dialogue_ended": True,
                    "end_reason": "情绪状态改变或达到最大轮次"
                }
            
            # 添加虚拟人物的回复到伴侣的消息列表
            partner_messages.append({"role": "user", "content": emotion_info["response"]})
            
            # 伴侣回复
            partner_response, _ = self.partner_client.create_chat_completion(
                messages=partner_messages,
                temperature=0.7
            )
            
            # 记录对话
            self.dialogue_history.append({
                "turn": self.turn_count,
                "speaker": "partner",
                "content": partner_response
            })
            
            return {
                "turn": self.turn_count,
                "character_response": emotion_info["response"],
                "inner_thoughts": emotion_info["inner_thoughts"],
                "emotion_score": self.current_emotion_score,
                "partner_response": partner_response,
                "dialogue_ended": False
            }
            
        else:
            # 如果是第一轮，添加开场白提示
            if self.turn_count == 1:
                partner_messages.append({"role": "user", "content": "请开始对话，表达你对这个情境的初始反应。"})
            
            # 伴侣先说
            partner_response, _ = self.partner_client.create_chat_completion(
                messages=partner_messages,
                temperature=0.7
            )
            
            # 记录对话
            self.dialogue_history.append({
                "turn": self.turn_count,
                "speaker": "partner",
                "content": partner_response
            })
            
            # 添加伴侣的回复到虚拟人物的消息列表
            character_messages.append({"role": "user", "content": partner_response})
            
            # 虚拟人物回复
            character_response, _ = self.character_client.create_chat_completion(
                messages=character_messages,
                temperature=0.8
            )
            
            # 解析情绪
            emotion_info = self._parse_emotion(character_response)
            self._update_emotion_score(emotion_info)
            
            # 记录对话
            self.dialogue_history.append({
                "turn": self.turn_count,
                "speaker": "character",
                "content": character_response,
                "emotion_info": emotion_info
            })
            
            return {
                "turn": self.turn_count,
                "character_response": emotion_info["response"],
                "inner_thoughts": emotion_info["inner_thoughts"],
                "emotion_score": self.current_emotion_score,
                "partner_response": partner_response,
                "dialogue_ended": self.should_end_dialogue(),
                "end_reason": "情绪状态改变或达到最大轮次" if self.should_end_dialogue() else None
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
            
            # 打印当前轮次信息
            print(f"\n--- 轮次 {self.turn_count} ---")
            if "partner_response" in turn_result and turn_result["partner_response"] is not None:
                if self.dialogue_history[-2]["speaker"] == "partner":
                    print(f"伴侣: {turn_result['partner_response']}")
                    print(f"{self.character['name']}: {turn_result['character_response']}")
                else:
                    print(f"{self.character['name']}: {turn_result['character_response']}")
                    print(f"伴侣: {turn_result['partner_response']}")
            else:
                print(f"{self.character['name']}: {turn_result['character_response']}")
            
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
            "final_emotion_score": self.current_emotion_score,
            "turns_completed": self.turn_count
        }
    
    def _save_dialogue_log(self):
        """保存对话记录到文件"""
        log_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "character": self.character,
            "scenario": self.scenario,
            "dialogue": self.dialogue_history,
            "emotion_history": self.emotion_history,
            "final_emotion_score": self.current_emotion_score,
            "turns_completed": self.turn_count
        }
        
        log_file = os.path.join(
            self.log_dir, 
            f"{self.character['id']}_{self.scenario['situation']['id']}_{int(time.time())}.json"
        )
        
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f"对话记录已保存到: {log_file}")

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