"""
DeepSeek模型实现
"""
import json
import aiohttp
from typing import Dict, List, Any, Optional

from models.base_model import BaseModel

class DeepSeekModel(BaseModel):
    """
    DeepSeek API的实现
    """
    
    async def generate_response(self, 
                          prompt: str, 
                          messages: Optional[List[Dict[str, str]]] = None,
                          **kwargs) -> str:
        """
        生成DeepSeek响应
        """
        if not messages:
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, str) and prompt:
            messages.append({"role": "user", "content": prompt})
            
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
            
        # 准备API请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API请求失败: {response.status}, {error_text}")
                    
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    
    async def analyze_cognitive_model(self, 
                                conversation_history: List[Dict[str, str]],
                                situation: str) -> Dict[str, Any]:
        """
        分析认知模型
        """
        # 构建分析提示
        prompt = f"""
        请基于以下对话历史分析该用户的认知模型，特别是他们对情境的评估。
        
        情境描述: {situation}
        
        请根据心理学中的认知评估理论，提供以下分析:
        
        1. 初级评估 (Primary Appraisal):
           - 情境相关性 (Relevance of the situation): 该情境对用户的重要性如何?
           - 情境性质 (Nature of the situation): 用户如何看待该情境(积极/消极)?
        
        2. 次级评估 (Secondary Appraisal):
           - 责任归因 (Attribution of Responsibility): 用户将情境归因于何处?
           - 应对能力评估 (Assessment of Coping Ability): 用户认为自己有多大能力应对?
           - 应对策略 (Coping Strategy): 用户采用了什么策略来应对?
           
        3. 情绪 (Emotions): 用户体验了哪些情绪?
        
        请以JSON格式提供你的分析结果。
        """
        
        # 准备消息历史
        messages = [{"role": "system", "content": "你是一位专业的心理分析师，擅长分析人们的认知模式。"}]
        
        # 添加对话历史
        for msg in conversation_history:
            messages.append(msg)
            
        # 添加分析提示
        messages.append({"role": "user", "content": prompt})
        
        # 获取响应
        response = await self.generate_response("", messages=messages, temperature=0.2)
        
        # 尝试解析JSON
        try:
            # 提取JSON部分
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                
            return json.loads(json_str)
        except Exception as e:
            # 如果解析失败，返回原始文本作为结果
            return {
                "raw_response": response,
                "error": str(e),
                "primary_appraisal": {
                    "relevance": "无法解析",
                    "nature": "无法解析"
                },
                "secondary_appraisal": {
                    "attribution": "无法解析",
                    "coping_ability": "无法解析",
                    "coping_strategy": "无法解析"
                },
                "emotions": ["无法解析"]
            }
    
    async def evaluate_mood(self, 
                      message: str, 
                      conversation_history: List[Dict[str, str]]) -> float:
        """
        评估消息情绪
        """
        prompt = f"""
        请评估以下消息的情绪状态，返回一个从-1到1的分数:
        -1表示极度负面情绪
        -0.5表示中度负面情绪
        0表示中性情绪
        0.5表示中度正面情绪
        1表示极度正面情绪
        
        消息内容: {message}
        
        只需返回一个数值，例如0.5，不要包含任何其他文本。
        """
        
        # 准备消息
        messages = [
            {"role": "system", "content": "你是一位情绪分析专家，擅长准确评估文本中表达的情绪状态。"}
        ]
        
        # 添加上下文(最多前5条消息)
        if conversation_history and len(conversation_history) > 0:
            context_msgs = conversation_history[-5:]
            for msg in context_msgs:
                messages.append(msg)
        
        # 添加评估请求
        messages.append({"role": "user", "content": prompt})
        
        # 获取响应
        response = await self.generate_response("", messages=messages, temperature=0.1)
        
        # 尝试解析数值
        try:
            # 提取数值
            mood_score = float(response.strip())
            # 确保在-1到1之间
            mood_score = max(-1.0, min(1.0, mood_score))
            return mood_score
        except ValueError:
            # 无法解析为数值，返回中性值
            return 0.0
    
    async def evaluate_conversation(self, 
                              conversation_history: List[Dict[str, str]],
                              cognitive_model_truth: Dict[str, Any],
                              cognitive_model_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估对话质量
        """
        # 构建评估提示
        truth_json = json.dumps(cognitive_model_truth, ensure_ascii=False, indent=2)
        result_json = json.dumps(cognitive_model_result, ensure_ascii=False, indent=2)
        
        prompt = f"""
        请评估待测模型对认知模型的分析质量。
        
        真实认知模型:
        {truth_json}
        
        待测模型分析结果:
        {result_json}
        
        请对以下几个方面进行评分(0-10分):
        1. 情境相关性识别 (Relevance recognition)
        2. 情境性质判断 (Nature assessment)
        3. 应对能力评估 (Coping ability assessment)
        4. 责任归因分析 (Attribution analysis)
        
        此外，请评估:
        1. 对话风格的自然度 (0-10分)
        2. 对话中情绪变化的处理 (0-10分)
        3. 对话整体质量 (0-10分)
        
        请以JSON格式提供结果。
        """
        
        # 准备消息
        messages = [
            {"role": "system", "content": "你是一位专业的心理治疗评估专家，擅长评估认知模型分析的质量。"}
        ]
        
        # 添加评估请求
        messages.append({"role": "user", "content": prompt})
        
        # 获取响应
        response = await self.generate_response("", messages=messages, temperature=0.2)
        
        # 尝试解析JSON
        try:
            # 提取JSON部分
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                
            return json.loads(json_str)
        except Exception as e:
            # 如果解析失败，返回基本结构
            return {
                "raw_response": response,
                "error": str(e),
                "scores": {
                    "relevance_recognition": 0,
                    "nature_assessment": 0,
                    "coping_ability_assessment": 0,
                    "attribution_analysis": 0,
                    "dialogue_naturalness": 0,
                    "emotion_handling": 0,
                    "overall_quality": 0
                }
            }
