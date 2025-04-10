"""
专家评估类，用于对对话和认知模型进行专业评估
"""
from typing import Dict, List, Any, Optional
import json
import asyncio

from models.expert import ExpertModel
from cognitive_model.primary_appraisal import PrimaryAppraisal
from cognitive_model.secondary_appraisal import SecondaryAppraisal
from cognitive_model.emotions import Emotions


class ExpertEvaluator:
    """
    使用专家模型进行对话和认知模型评估的类
    """
    
    def __init__(self, expert_model: ExpertModel):
        """
        初始化专家评估器
        
        Args:
            expert_model: 专家模型实例
        """
        self.expert_model = expert_model
    
    async def evaluate_conversation_quality(self, 
                                      conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        评估对话质量
        
        Args:
            conversation_history: 对话历史
            
        Returns:
            对话质量评估结果
        """
        # 准备评估消息
        # 提取对话文本
        conversation_text = "\n\n".join([
            f"{'虚拟人物' if msg['role'] == 'assistant' else '用户'}: {msg['content']}"
            for msg in conversation_history
        ])
        
        prompt = f"""
        请作为专业的对话评估专家，评估以下对话的质量:
        
        {conversation_text}
        
        请评估以下几个方面(0-10分):
        1. 对话自然度 - 对话是否流畅、自然
        2. 角色一致性 - 对话中的角色是否保持一致的个性和风格
        3. 逻辑连贯性 - 对话是否连贯，有合理的逻辑进展
        4. 情感表达 - 情感表达是否自然、适当
        5. 整体对话质量 - 综合以上因素的整体质量
        
        请以JSON格式提供评分和简短评语。
        """
        
        # 调用专家模型评估
        messages = [
            {"role": "system", "content": "你是一位专业的对话质量评估专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.expert_model.generate_response("", messages=messages, temperature=0.2)
        
        # 解析结果
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
            # 解析失败，返回错误信息
            return {
                "error": f"解析评估结果失败: {str(e)}",
                "raw_response": response,
                "scores": {
                    "naturalness": 0,
                    "character_consistency": 0,
                    "logical_coherence": 0,
                    "emotional_expression": 0,
                    "overall_quality": 0
                }
            }
    
    async def evaluate_cognitive_models(self,
                                  cognitive_model_truth: Dict[str, Any],
                                  cognitive_model_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估认知模型的准确度
        
        Args:
            cognitive_model_truth: 真实认知模型
            cognitive_model_result: 分析得到的认知模型
            
        Returns:
            评估结果
        """
        # 对比两个认知模型
        # 初级评估对比
        primary_truth = PrimaryAppraisal.from_dict(cognitive_model_truth.get("primary_appraisal", {}))
        primary_result = PrimaryAppraisal.from_dict(cognitive_model_result.get("primary_appraisal", {}))
        primary_scores = primary_truth.compare(primary_result)
        
        # 次级评估对比
        secondary_truth = SecondaryAppraisal.from_dict(cognitive_model_truth.get("secondary_appraisal", {}))
        secondary_result = SecondaryAppraisal.from_dict(cognitive_model_result.get("secondary_appraisal", {}))
        secondary_scores = secondary_truth.compare(secondary_result)
        
        # 情绪对比
        emotions_truth = Emotions.from_list(cognitive_model_truth.get("emotions", []))
        emotions_result = Emotions.from_list(cognitive_model_result.get("emotions", []))
        emotion_scores = emotions_truth.compare(emotions_result)
        
        # 构建结果
        results = {
            "primary_appraisal": {
                "scores": primary_scores,
                "truth": primary_truth.to_dict(),
                "result": primary_result.to_dict()
            },
            "secondary_appraisal": {
                "scores": secondary_scores,
                "truth": secondary_truth.to_dict(),
                "result": secondary_result.to_dict()
            },
            "emotions": {
                "scores": emotion_scores,
                "truth": emotions_truth.to_list(),
                "result": emotions_result.to_list()
            },
            "overall_score": (
                primary_scores.get("overall", 0) + 
                secondary_scores.get("overall", 0) + 
                emotion_scores.get("overall", 0)
            ) / 3.0
        }
        
        return results
    
    async def record_mood_changes(self, 
                            mood_history: List[float]) -> Dict[str, Any]:
        """
        记录和分析情绪变化
        
        Args:
            mood_history: 情绪历史记录
            
        Returns:
            情绪变化分析结果
        """
        if not mood_history or len(mood_history) < 2:
            return {
                "trend": "insufficient_data",
                "change": 0.0,
                "start_mood": mood_history[0] if mood_history else 0.0,
                "end_mood": mood_history[-1] if mood_history else 0.0
            }
            
        # 计算变化趋势
        start_mood = mood_history[0]
        end_mood = mood_history[-1]
        total_change = end_mood - start_mood
        
        # 确定整体趋势
        if total_change > 0.2:
            trend = "significant_improvement"
        elif total_change > 0.05:
            trend = "slight_improvement"
        elif total_change < -0.2:
            trend = "significant_deterioration"
        elif total_change < -0.05:
            trend = "slight_deterioration"
        else:
            trend = "stable"
            
        # 计算波动性
        changes = [abs(mood_history[i] - mood_history[i-1]) for i in range(1, len(mood_history))]
        volatility = sum(changes) / len(changes) if changes else 0.0
        
        return {
            "trend": trend,
            "change": total_change,
            "volatility": volatility,
            "start_mood": start_mood,
            "end_mood": end_mood,
            "mood_history": mood_history
        }
    
    async def comprehensive_evaluation(self,
                                 conversation_history: List[Dict[str, str]],
                                 cognitive_model_truth: Dict[str, Any],
                                 cognitive_model_result: Dict[str, Any],
                                 mood_history: List[float]) -> Dict[str, Any]:
        """
        综合评估，整合所有评估结果
        
        Args:
            conversation_history: 对话历史
            cognitive_model_truth: 真实认知模型
            cognitive_model_result: 分析得到的认知模型
            mood_history: 情绪历史记录
            
        Returns:
            综合评估结果
        """
        # 并行执行所有评估
        conversation_quality_task = asyncio.create_task(
            self.evaluate_conversation_quality(conversation_history)
        )
        
        cognitive_models_task = asyncio.create_task(
            self.evaluate_cognitive_models(cognitive_model_truth, cognitive_model_result)
        )
        
        mood_analysis_task = asyncio.create_task(
            self.record_mood_changes(mood_history)
        )
        
        # 等待所有任务完成
        conversation_quality = await conversation_quality_task
        cognitive_models = await cognitive_models_task
        mood_analysis = await mood_analysis_task
        
        # 整合所有结果
        return {
            "conversation_quality": conversation_quality,
            "cognitive_models": cognitive_models,
            "mood_analysis": mood_analysis,
            "timestamp": "", # 实际使用时可添加时间戳
            "session_id": "" # 实际使用时可添加会话ID
        }
