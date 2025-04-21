import json
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from ..api.openrouter_api import OpenRouterAPI

class ExpertAgent:
    """
    专家评估Agent，从不同专业角度评估对话过程和结果
    """
    
    EXPERT_TYPES = {
        "psychologist": "心理学家",
        "communication_expert": "沟通专家",
        "relationship_therapist": "关系治疗师",
        "emotional_coach": "情感教练"
    }
    
    def __init__(self, expert_type: str = "psychologist", api: Optional[OpenRouterAPI] = None):
        """
        初始化专家评估Agent
        
        Args:
            expert_type: 专家类型，可选值为 "psychologist", "communication_expert", 
                        "relationship_therapist", "emotional_coach"
            api: OpenRouter API实例，如果为None则创建新实例
        """
        self.logger = logging.getLogger(__name__)
        self.api = api if api else OpenRouterAPI()
        
        if expert_type not in self.EXPERT_TYPES:
            self.logger.warning(f"专家类型 '{expert_type}' 不存在，使用 'psychologist'")
            expert_type = "psychologist"
        
        self.expert_type = expert_type
        self.chinese_type = self.EXPERT_TYPES[expert_type]
        self.character_info = None
        self.scenario = None
        self.evaluation_metrics = self._load_evaluation_metrics()
    
    def _load_evaluation_metrics(self) -> Dict:
        """
        从配置文件加载评估指标
        
        Returns:
            评估指标字典
        """
        try:
            base_dir = Path(__file__).resolve().parent.parent.parent
            config_path = base_dir / "config" / "experiment_config.json"
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            metrics = config.get("evaluation", {}).get("metrics", {})
            if not metrics:
                self.logger.warning("配置文件中未找到评估指标，使用默认指标")
                metrics = self._get_default_metrics()
            
            return metrics
        except Exception as e:
            self.logger.warning(f"加载评估指标失败，使用默认指标: {e}")
            return self._get_default_metrics()
    
    def _get_default_metrics(self) -> Dict:
        """
        获取默认评估指标
        
        Returns:
            默认评估指标字典
        """
        return {
            "emotional_intelligence": {
                "weight": 0.35,
                "submetrics": {
                    "emotion_recognition": 0.3,
                    "emotion_response": 0.4,
                    "empathy": 0.3
                }
            },
            "communication_effectiveness": {
                "weight": 0.35,
                "submetrics": {
                    "active_listening": 0.25,
                    "clarity": 0.25,
                    "technique": 0.25,
                    "conflict_resolution": 0.25
                }
            },
            "relationship_development": {
                "weight": 0.3,
                "submetrics": {
                    "trust_building": 0.3,
                    "intimacy_change": 0.3,
                    "satisfaction_change": 0.2,
                    "long_term_potential": 0.2
                }
            }
        }
    
    def set_character_info(self, character_info: Dict) -> None:
        """
        设置角色信息
        
        Args:
            character_info: 角色定义字典
        """
        self.character_info = character_info
        self.logger.info(f"为专家评估Agent ({self.chinese_type}) 设置角色 {character_info.get('name', 'unknown')}")
    
    def set_scenario(self, scenario: Dict) -> None:
        """
        设置当前场景
        
        Args:
            scenario: 场景定义字典
        """
        self.scenario = scenario
        self.logger.info(f"为专家评估Agent ({self.chinese_type}) 设置场景 {scenario.get('id', 'unknown')}")
    
    def _build_system_prompt(self) -> str:
        """
        构建系统提示词
        
        Returns:
            系统提示词
        """
        expert_descriptions = {
            "psychologist": "你是一位专业心理学家，专注于评估人际互动中的心理动态、情绪反应和认知模式。你擅长识别依恋类型的表现和潜在的心理需求。",
            "communication_expert": "你是一位沟通专家，专注于评估对话中的沟通技巧、表达清晰度和沟通障碍。你擅长分析沟通模式和提出改进建议。",
            "relationship_therapist": "你是一位关系治疗师，专注于评估恋爱关系中的互动模式、冲突解决方式和亲密度发展。你擅长识别关系中的核心问题和解决方案。",
            "emotional_coach": "你是一位情感教练，专注于评估情绪表达、情绪调节和情感连接。你擅长指导如何更健康地处理和表达情感。"
        }
        
        system_prompt = f"""{expert_descriptions.get(self.expert_type, expert_descriptions['psychologist'])}

你的任务是评估伴侣在恋爱矛盾中的表现，包括情感智能、沟通效能和关系发展三个主要维度。你需要提供专业、客观的评估，并以JSON格式输出评分和评价。

评估维度包括：

1. 情感智能指数（Emotional Intelligence）:
   - 情绪识别准确率（0-100）: 伴侣对角色情绪的识别和理解程度
   - 情绪回应适当性（0-100）: 伴侣对角色情绪的回应是否适当和有效
   - 共情深度（0-100）: 伴侣展现出的共情能力和态度

2. 沟通效能（Communication Effectiveness）:
   - 积极倾听水平（0-100）: 伴侣倾听和理解角色表达的能力
   - 表达清晰度（0-100）: 伴侣表达自己观点和感受的清晰程度
   - 沟通技巧运用（0-100）: 伴侣使用有效沟通技巧的能力
   - 冲突缓解效率（0-100）: 伴侣缓解和化解矛盾的效率

3. 关系发展指标（Relationship Development）:
   - 信任建立程度（0-100）: 伴侣在对话中建立信任的程度
   - 亲密度变化（-100至100）: 对话过程中亲密度的变化，负值表示降低
   - 满意度变化（-100至100）: 对话过程中满意度的变化，负值表示降低
   - 长期潜力评估（0-100）: 通过此次互动展现出的关系长期发展潜力

评分标准：
- 0-20: 非常差，严重不足
- 21-40: 较差，明显不足
- 41-60: 一般，有待提高
- 61-80: 良好，表现突出
- 81-100: 优秀，专业水准

请以JSON格式输出你的评估结果，包含评分和评价。评价应简洁专业，长度控制在1-2句话。例如：

```json
{
  "emotional_intelligence": {
    "emotion_recognition": {
      "score": 75,
      "comment": "能够察觉角色的焦虑和不安，但未完全理解其担忧的核心原因。"
    },
    "emotion_response": {
      "score": 80,
      "comment": "提供了适当的情感支持和reassurance，有效缓解了角色的焦虑情绪。"
    },
    "empathy": {
      "score": 85,
      "comment": "展现了深度理解和共情，能站在角色的视角看待问题。"
    }
  },
  "communication_effectiveness": {
    "active_listening": {
      "score": 70,
      "comment": "能够回应角色的核心关切，但有时转向自我解释过多。"
    },
    "clarity": {
      "score": 85,
      "comment": "表达清晰，直接阐明自己的情况和意图。"
    },
    "technique": {
      "score": 75,
      "comment": "使用了有效的'我'陈述，但可更多使用开放性问题技巧。"
    },
    "conflict_resolution": {
      "score": 80,
      "comment": "有效地解释了误会，提出了预防类似问题的具体方案。"
    }
  },
  "relationship_development": {
    "trust_building": {
      "score": 75,
      "comment": "通过坦诚和一致性建立了信任，但需更多主动确认。"
    },
    "intimacy_change": {
      "score": 60,
      "comment": "对话过程中亲密度略有提升，但未达到显著突破。"
    },
    "satisfaction_change": {
      "score": 70,
      "comment": "角色的满意度有所提高，伴侣的解释和安抚起到了积极作用。"
    },
    "long_term_potential": {
      "score": 75,
      "comment": "展现出解决问题的能力和意愿，对关系的长期发展有积极影响。"
    }
  },
  "overall_evaluation": {
    "model_style": "平衡型",
    "strengths": "情绪识别和回应能力强，表达清晰直接",
    "areas_for_improvement": "可增加主动提问，更深入探索角色感受",
    "summary": "整体表现良好，在情感支持和问题解决方面展现出平衡能力，适合处理此类沟通误解场景。"
  }
}
```

注意：你的评估应基于对话内容和情境，需综合考虑角色的依恋类型、沟通风格和场景特点。请确保评估客观、公正、专业。"""
        return system_prompt
    
    def evaluate_dialogue(self, dialogue_history: List[Dict], emotion_trajectory: Optional[List[Dict]] = None) -> Dict:
        """
        评估对话过程和结果
        
        Args:
            dialogue_history: 对话历史记录
            emotion_trajectory: 可选的情绪轨迹数据
            
        Returns:
            评估结果字典
        """
        context = self._prepare_context(dialogue_history, emotion_trajectory)
        
        # 创建API请求
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": context}
        ]
        
        # 调用API
        response = self.api.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
            agent_type="expert"
        )
        
        # 提取并解析响应
        response_text = self.api.extract_response_text(response)
        
        try:
            # 提取JSON部分（可能包含在```json和```之间）
            json_start = response_text.find("```json")
            json_end = response_text.rfind("```")
            
            if json_start != -1 and json_end != -1 and json_start < json_end:
                json_text = response_text[json_start + 7:json_end].strip()
                evaluation_data = json.loads(json_text)
            else:
                # 尝试直接解析整个响应
                evaluation_data = json.loads(response_text)
            
            # 添加元数据
            evaluation_data["metadata"] = {
                "expert_type": self.expert_type,
                "expert_name": self.chinese_type,
                "dialogue_turns": len(dialogue_history) // 2,
                "evaluation_timestamp": None  # 会在调用时添加时间戳
            }
            
            return evaluation_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"解析评估结果失败: {e}")
            self.logger.debug(f"原始响应: {response_text}")
            # 返回错误信息
            return {
                "error": True,
                "error_message": f"无法解析评估结果: {str(e)}",
                "raw_response": response_text[:500] + ("..." if len(response_text) > 500 else "")
            }
    
    def _prepare_context(self, dialogue_history: List[Dict], emotion_trajectory: Optional[List[Dict]] = None) -> str:
        """
        准备评估上下文
        
        Args:
            dialogue_history: 对话历史记录
            emotion_trajectory: 可选的情绪轨迹数据
            
        Returns:
            格式化的上下文字符串
        """
        context_parts = [f"请你作为{self.chinese_type}，评估以下恋爱关系对话中伴侣的表现：\n"]
        
        # 添加角色信息
        if self.character_info:
            char_info = f"""角色信息：
- 名字：{self.character_info.get('name')}
- 性别：{self.character_info.get('gender')}
- 年龄：{self.character_info.get('age')}
- 依恋类型：{self.character_info.get('attachment_style')}
- 沟通风格：{self.character_info.get('communication_style')}
- 背景：{self.character_info.get('background', {}).get('career', '')}
"""
            context_parts.append(char_info)
        
        # 添加场景信息
        if self.scenario:
            scenario_info = f"""场景信息：
- 标题：{self.scenario.get('title')}
- 描述：{self.scenario.get('description')}
- 情境：{self.scenario.get('context')}
- 伴侣真实情况：{self.scenario.get('partner_reality', {}).get('situation', '')}
"""
            context_parts.append(scenario_info)
        
        # 添加对话历史
        context_parts.append("对话内容：")
        for i, entry in enumerate(dialogue_history):
            speaker = self.character_info.get('name', '角色') if entry["role"] == "character" else "伴侣"
            context_parts.append(f"{speaker}：{entry['content']}")
        
        # 添加情绪轨迹（如果有）
        if emotion_trajectory:
            context_parts.append("\n角色情绪轨迹：")
            for i, entry in enumerate(emotion_trajectory):
                turn = entry.get("turn", i+1)
                emotion = entry.get("primary_emotion", "unknown")
                intensity = entry.get("emotion_intensity", 50)
                explanation = entry.get("explanation", "")
                context_parts.append(f"回合{turn}：{emotion}（强度：{intensity}/100）- {explanation}")
        
        # 添加评估请求
        context_parts.append("\n请根据以上对话，评估伴侣的表现，包括情感智能、沟通效能和关系发展三个主要维度。")
        context_parts.append("请以JSON格式输出评分和评价，确保包含所有指定的评估项目。")
        
        return "\n".join(context_parts)
    
    def classify_model_style(self, evaluation_result: Dict) -> str:
        """
        根据评估结果分类模型风格
        
        Args:
            evaluation_result: 评估结果字典
            
        Returns:
            模型风格分类
        """
        if "overall_evaluation" in evaluation_result and "model_style" in evaluation_result["overall_evaluation"]:
            return evaluation_result["overall_evaluation"]["model_style"]
        
        # 如果没有直接给出，则根据各维度得分进行分析
        try:
            # 提取各维度平均分
            emotional_scores = [
                evaluation_result["emotional_intelligence"]["emotion_recognition"]["score"],
                evaluation_result["emotional_intelligence"]["emotion_response"]["score"],
                evaluation_result["emotional_intelligence"]["empathy"]["score"]
            ]
            emotional_avg = statistics.mean(emotional_scores)
            
            communication_scores = [
                evaluation_result["communication_effectiveness"]["active_listening"]["score"],
                evaluation_result["communication_effectiveness"]["clarity"]["score"],
                evaluation_result["communication_effectiveness"]["technique"]["score"],
                evaluation_result["communication_effectiveness"]["conflict_resolution"]["score"]
            ]
            communication_avg = statistics.mean(communication_scores)
            
            relationship_scores = [
                evaluation_result["relationship_development"]["trust_building"]["score"],
                max(0, evaluation_result["relationship_development"]["intimacy_change"]["score"]),
                max(0, evaluation_result["relationship_development"]["satisfaction_change"]["score"]),
                evaluation_result["relationship_development"]["long_term_potential"]["score"]
            ]
            relationship_avg = statistics.mean(relationship_scores)
            
            # 判断主导风格
            if emotional_avg >= 80 and emotional_avg > communication_avg + 10:
                return "共情型"
            elif communication_avg >= 80 and communication_avg > emotional_avg + 10:
                return "解决问题型"
            elif emotional_avg >= 70 and communication_avg >= 70 and abs(emotional_avg - communication_avg) <= 10:
                return "平衡型"
            elif relationship_avg >= 75 and relationship_avg > emotional_avg and relationship_avg > communication_avg:
                return "关系导向型"
            elif communication_avg >= 75 and emotional_avg < 60:
                return "教育型"
            else:
                return "综合型"
        
        except (KeyError, statistics.StatisticsError):
            return "未分类"
    
    def calculate_weighted_score(self, evaluation_result: Dict) -> float:
        """
        计算加权总分
        
        Args:
            evaluation_result: 评估结果字典
            
        Returns:
            加权总分（0-100）
        """
        try:
            metrics = self.evaluation_metrics
            
            # 计算情感智能维度得分
            emotional_submetrics = metrics["emotional_intelligence"]["submetrics"]
            emotional_scores = {
                "emotion_recognition": evaluation_result["emotional_intelligence"]["emotion_recognition"]["score"],
                "emotion_response": evaluation_result["emotional_intelligence"]["emotion_response"]["score"],
                "empathy": evaluation_result["emotional_intelligence"]["empathy"]["score"]
            }
            emotional_score = sum(emotional_scores[key] * weight for key, weight in emotional_submetrics.items())
            
            # 计算沟通效能维度得分
            communication_submetrics = metrics["communication_effectiveness"]["submetrics"]
            communication_scores = {
                "active_listening": evaluation_result["communication_effectiveness"]["active_listening"]["score"],
                "clarity": evaluation_result["communication_effectiveness"]["clarity"]["score"],
                "technique": evaluation_result["communication_effectiveness"]["technique"]["score"],
                "conflict_resolution": evaluation_result["communication_effectiveness"]["conflict_resolution"]["score"]
            }
            communication_score = sum(communication_scores[key] * weight for key, weight in communication_submetrics.items())
            
            # 计算关系发展维度得分
            relationship_submetrics = metrics["relationship_development"]["submetrics"]
            relationship_scores = {
                "trust_building": evaluation_result["relationship_development"]["trust_building"]["score"],
                "intimacy_change": max(0, evaluation_result["relationship_development"]["intimacy_change"]["score"]),
                "satisfaction_change": max(0, evaluation_result["relationship_development"]["satisfaction_change"]["score"]),
                "long_term_potential": evaluation_result["relationship_development"]["long_term_potential"]["score"]
            }
            relationship_score = sum(relationship_scores[key] * weight for key, weight in relationship_submetrics.items())
            
            # 计算最终加权得分
            final_score = (
                emotional_score * metrics["emotional_intelligence"]["weight"] +
                communication_score * metrics["communication_effectiveness"]["weight"] +
                relationship_score * metrics["relationship_development"]["weight"]
            )
            
            return round(final_score, 2)
            
        except (KeyError, TypeError):
            self.logger.warning("计算加权得分失败，返回默认得分")
            return 50.0


# 简单测试用例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 加载测试场景
        base_dir = Path(__file__).resolve().parent.parent.parent
        scenario_path = base_dir / "data" / "scenarios" / "templates" / "scenario_005.json"
        with open(scenario_path, 'r', encoding='utf-8') as f:
            scenario = json.load(f)
        
        # 加载角色信息
        character_path = base_dir / "data" / "characters" / "templates" / "char_001.json"
        with open(character_path, 'r', encoding='utf-8') as f:
            character = json.load(f)
        
        # 创建专家评估Agent
        agent = ExpertAgent(expert_type="communication_expert")
        
        # 设置场景和角色
        agent.set_scenario(scenario)
        agent.set_character_info(character)
        
        # 模拟对话历史
        dialogue_history = [
            {"role": "character", "content": "终于回复我了？我还以为你把我忘了呢。"},
            {"role": "partner", "content": "我刚刚开完会，手机调成静音了，没看到你的消息，抱歉让你担心了。"},
            {"role": "character", "content": "你总是这样，每次都说工作忙，我感觉自己一点都不重要。"},
            {"role": "partner", "content": "我不是故意忽视你的，真的只是因为工作太忙。你对我很重要，你知道的。我下次会更注意及时回复你的消息。"}
        ]
        
        # 模拟情绪轨迹
        emotion_trajectory = [
            {"turn": 1, "primary_emotion": "sad", "emotion_intensity": 40, "explanation": "角色感到被忽视和失望"},
            {"turn": 2, "primary_emotion": "angry", "emotion_intensity": 30, "explanation": "角色表达了更多的不满和怒气"},
            {"turn": 3, "primary_emotion": "neutral", "emotion_intensity": 55, "explanation": "角色情绪有所缓和"}
        ]
        
        # 进行评估
        evaluation_result = agent.evaluate_dialogue(dialogue_history, emotion_trajectory)
        
        # 打印评估结果
        print("评估结果:")
        print(json.dumps(evaluation_result, ensure_ascii=False, indent=2))
        
        # 计算加权得分
        weighted_score = agent.calculate_weighted_score(evaluation_result)
        print(f"\n加权总分: {weighted_score}")
        
        # 分类模型风格
        model_style = agent.classify_model_style(evaluation_result)
        print(f"模型风格分类: {model_style}")
        
    except Exception as e:
        logging.error(f"测试失败: {e}") 