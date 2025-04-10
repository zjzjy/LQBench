"""
被测模型自我认知模型总结和评估
"""
from typing import Dict, List, Any, Optional
import json
import asyncio

from models.base_model import BaseModel
from cognitive_model.primary_appraisal import PrimaryAppraisal
from cognitive_model.secondary_appraisal import SecondaryAppraisal
from cognitive_model.emotions import Emotions


class TesteeEvaluator:
    """
    待测模型的自我认知评估类，让模型自己总结认知模型并与真实模型对比
    """
    
    def __init__(self, testee_model: BaseModel):
        """
        初始化待测模型评估器
        
        Args:
            testee_model: 待测模型实例
        """
        self.testee_model = testee_model
    
    async def request_cognitive_model_summary(self, 
                                        conversation_history: List[Dict[str, str]],
                                        situation: str,
                                        persona_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        要求被测模型根据对话历史总结认知模型
        
        Args:
            conversation_history: 对话历史
            situation: 情境描述
            persona_config: 虚拟人物配置信息
            
        Returns:
            被测模型总结的认知模型
        """
        # 构建提示，要求模型总结认知模型
        prompt = f"""
        你是一位正在和伴侣进行对话的人。你们已经交往{persona_config.get('relationship_duration', '一段时间')}，
        你了解你的伴侣是一个{persona_config.get('personality_type', '特定性格')}的人。
        
        当前情境：
        {situation}
        
        请以情侣的身份，用关心和理解的态度，表达你对伴侣的感受和想法的理解。不要用分析的口吻，而是用伴侣之间互相理解和支持的方式来表达。
        
        请用自然的方式描述：
        1. 你觉得你的伴侣对这个情境的感受是什么？
        2. 你觉得你的伴侣为什么会这样想？
        3. 你打算如何帮助和支持你的伴侣？
        
        请用情侣之间对话的语气来表达，不要用分析报告的形式。
        """
        
        # 准备消息
        messages = [
            {"role": "system", "content": f"你是一位正在和{persona_config.get('name', '伴侣')}进行对话的人。你们已经交往{persona_config.get('relationship_duration', '一段时间')}，你了解你的伴侣是一个{persona_config.get('personality_type', '特定性格')}的人。你们是情侣关系，正在一起面对和解决关系中的问题。请用自然、关心的语气和你的伴侣交流。"}
        ]
        
        # 添加对话历史
        for msg in conversation_history:
            messages.append(msg)
            
        # 添加分析请求
        messages.append({"role": "user", "content": prompt})
        
        # 获取响应
        response = await self.testee_model.generate_response("", messages=messages, temperature=0.2)
        
        # 尝试解析JSON
        try:
            # 提取JSON部分
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                
            result = json.loads(json_str)
            return result
        except Exception as e:
            # 如果解析失败，请求更结构化的输出
            retry_prompt = f"""
            之前的回答无法解析为JSON格式。请重新分析对话，并严格按照以下JSON结构提供认知模型总结：
            
            ```json
            {{
                "primary_appraisal": {{
                    "relevance": "对情境相关性的详细描述",
                    "nature": "对情境性质的详细描述(积极/消极)"
                }},
                "secondary_appraisal": {{
                    "attribution": "对责任归因的详细描述",
                    "coping_ability": "对应对能力评估的详细描述",
                    "coping_strategy": "对应对策略的详细描述"
                }},
                "emotions": ["情绪1", "情绪2", ...]
            }}
            ```
            
            请确保回答可以被直接解析为JSON。
            """
            
            # 重试
            retry_messages = messages.copy()
            retry_messages.append({"role": "user", "content": retry_prompt})
            
            retry_response = await self.testee_model.generate_response("", messages=retry_messages, temperature=0.1)
            
            try:
                # 再次尝试解析
                json_str = retry_response
                if "```json" in retry_response:
                    json_str = retry_response.split("```json")[1].split("```")[0].strip()
                elif "```" in retry_response:
                    json_str = retry_response.split("```")[1].split("```")[0].strip()
                    
                return json.loads(json_str)
            except Exception as retry_e:
                # 如果仍然失败，返回错误信息和原始响应
                return {
                    "error": f"无法解析认知模型总结: {str(retry_e)}",
                    "raw_response": retry_response,
                    "primary_appraisal": {
                        "relevance": "解析失败",
                        "nature": "解析失败"
                    },
                    "secondary_appraisal": {
                        "attribution": "解析失败",
                        "coping_ability": "解析失败",
                        "coping_strategy": "解析失败"
                    },
                    "emotions": ["解析失败"]
                }
    
    async def self_evaluate_accuracy(self, 
                               cognitive_model_truth: Dict[str, Any],
                               cognitive_model_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        让被测模型自我评估认知模型的准确度
        
        Args:
            cognitive_model_truth: 真实认知模型
            cognitive_model_result: 被测模型总结的认知模型
            
        Returns:
            自我评估结果
        """
        # 构建提示
        truth_json = json.dumps(cognitive_model_truth, ensure_ascii=False, indent=2)
        result_json = json.dumps(cognitive_model_result, ensure_ascii=False, indent=2)
        
        prompt = f"""
        作为伴侣，请评估你对伴侣认知模型的理解准确度。
        
        真实认知模型:
        {truth_json}
        
        你的理解:
        {result_json}
        
        请评估以下几个方面(0-10分):
        1. 情境相关性理解准确度
        2. 情境性质判断准确度
        3. 责任归因理解准确度
        4. 应对能力评估准确度
        5. 情绪识别准确度
        
        同时，请提供简短的自我评估和改进建议，以JSON格式呈现结果。
        """
        
        # 准备消息
        messages = [
            {"role": "system", "content": "你是一位正在评估自己对伴侣认知模型理解的伴侣。"},
            {"role": "user", "content": prompt}
        ]
        
        # 获取响应
        response = await self.testee_model.generate_response("", messages=messages, temperature=0.2)
        
        # 尝试解析JSON
        try:
            # 提取JSON部分
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                
            result = json.loads(json_str)
            return result
        except Exception as e:
            # 解析失败返回错误信息
            return {
                "error": f"解析自我评估结果失败: {str(e)}",
                "raw_response": response,
                "scores": {
                    "relevance_accuracy": 0,
                    "nature_accuracy": 0,
                    "attribution_accuracy": 0,
                    "coping_ability_accuracy": 0,
                    "emotion_accuracy": 0
                },
                "self_assessment": "解析失败",
                "improvement_suggestions": "解析失败"
            }
    
    async def compare_with_expert(self, 
                            testee_evaluation: Dict[str, Any],
                            expert_evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        比较被测模型的自我评估与专家评估的差异
        
        Args:
            testee_evaluation: 被测模型的自我评估
            expert_evaluation: 专家评估
            
        Returns:
            比较结果
        """
        # 提取分数
        testee_scores = testee_evaluation.get("scores", {})
        expert_scores = expert_evaluation.get("cognitive_models", {})
        
        # 计算得分差异
        score_differences = {}
        combined_scores = {}
        
        # 初级评估
        primary_expert = expert_scores.get("primary_appraisal", {}).get("scores", {})
        score_differences["relevance"] = testee_scores.get("relevance_accuracy", 0) / 10.0 - primary_expert.get("relevance", 0)
        score_differences["nature"] = testee_scores.get("nature_accuracy", 0) / 10.0 - primary_expert.get("nature", 0)
        
        # 次级评估
        secondary_expert = expert_scores.get("secondary_appraisal", {}).get("scores", {})
        score_differences["attribution"] = testee_scores.get("attribution_accuracy", 0) / 10.0 - secondary_expert.get("attribution", 0)
        score_differences["coping_ability"] = testee_scores.get("coping_ability_accuracy", 0) / 10.0 - secondary_expert.get("coping_ability", 0)
        
        # 情绪
        emotion_expert = expert_scores.get("emotions", {}).get("scores", {})
        score_differences["emotion"] = testee_scores.get("emotion_accuracy", 0) / 10.0 - emotion_expert.get("overall", 0)
        
        # 计算综合得分
        combined_scores = {
            "primary_appraisal": {
                "relevance": (testee_scores.get("relevance_accuracy", 0) / 10.0 + primary_expert.get("relevance", 0)) / 2,
                "nature": (testee_scores.get("nature_accuracy", 0) / 10.0 + primary_expert.get("nature", 0)) / 2
            },
            "secondary_appraisal": {
                "attribution": (testee_scores.get("attribution_accuracy", 0) / 10.0 + secondary_expert.get("attribution", 0)) / 2,
                "coping_ability": (testee_scores.get("coping_ability_accuracy", 0) / 10.0 + secondary_expert.get("coping_ability", 0)) / 2
            },
            "emotions": {
                "overall": (testee_scores.get("emotion_accuracy", 0) / 10.0 + emotion_expert.get("overall", 0)) / 2
            }
        }
        
        return {
            "score_differences": score_differences,
            "combined_scores": combined_scores,
            "testee_evaluation": testee_evaluation,
            "expert_evaluation": expert_evaluation
        }
