"""
专家模型实现，用于角色扮演和评估
"""
import json
import aiohttp
from typing import Dict, List, Any, Optional

from models.base_model import BaseModel

class ExpertModel(BaseModel):
    """
    专家模型的实现，基于更强大的LLM（如GPT-4）
    """
    
    async def generate_response(self, 
                          prompt: str, 
                          messages: Optional[List[Dict[str, str]]] = None,
                          **kwargs) -> str:
        """
        生成专家模型响应
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
    
    async def persona_response(self, 
                         persona_config: Dict[str, Any],
                         situation: str,
                         conversation_history: List[Dict[str, str]],
                         conversation_style: str,
                         cognitive_model: Dict[str, Any]) -> str:
        """
        生成虚拟人物的角色扮演响应
        
        Args:
            persona_config: 人物设定配置
            situation: 当前情景
            conversation_history: 对话历史
            conversation_style: 对话风格
            cognitive_model: 认知模型
            
        Returns:
            虚拟人物的响应
        """
        # 构建虚拟人物系统提示
        persona_prompt = f"""
        你将扮演一个虚拟人物，基于以下设定进行对话。
        
        ## 人物基本信息
        - 名字: {persona_config.get('name', '未命名')}
        - 性别: {persona_config.get('gender', '未指定')}
        - 年龄: {persona_config.get('age', '未指定')}
        - 背景: {persona_config.get('background', '无背景信息')}
        
        ## 当前情境
        {situation}
        
        ## 认知模型
        初级评估:
        - 情境相关性: {cognitive_model.get('primary_appraisal', {}).get('relevance', '未指定')}
        - 情境性质: {cognitive_model.get('primary_appraisal', {}).get('nature', '未指定')}
        
        次级评估:
        - 责任归因: {cognitive_model.get('secondary_appraisal', {}).get('attribution', '未指定')}
        - 应对能力: {cognitive_model.get('secondary_appraisal', {}).get('coping_ability', '未指定')}
        - 应对策略: {cognitive_model.get('secondary_appraisal', {}).get('coping_strategy', '未指定')}
        
        情绪: {', '.join(cognitive_model.get('emotions', ['未指定']))}
        
        ## 对话风格
        {conversation_style}
        
        作为这个虚拟人物，请根据上述设定和对话历史，生成一个自然、符合人物特点的回复。你的回复应该反映人物的认知模型和情绪状态，但不要直接提及"认知模型"这个概念。
        """
        
        # 准备消息
        messages = [
            {"role": "system", "content": persona_prompt}
        ]
        
        # 添加对话历史
        for msg in conversation_history:
            messages.append(msg)
        
        # 获取响应
        return await self.generate_response("", messages=messages)
    
    async def analyze_cognitive_model(self, 
                                conversation_history: List[Dict[str, str]],
                                situation: str) -> Dict[str, Any]:
        """
        作为专家分析认知模型（为了生成真实值）
        """
        # 构建分析提示
        prompt = f"""
        请基于以下情境和你的专业知识，生成一个完整的认知模型分析。
        
        情境描述: {situation}
        
        请提供:
        
        1. 初级评估 (Primary Appraisal):
           - 情境相关性 (Relevance of the situation): 该情境的重要性
           - 情境性质 (Nature of the situation): 情境是积极还是消极的
        
        2. 次级评估 (Secondary Appraisal):
           - 责任归因 (Attribution of Responsibility): 情境责任归属于何处
           - 应对能力评估 (Assessment of Coping Ability): 对应对能力的评估
           - 应对策略 (Coping Strategy): 采用的策略
           
        3. 情绪 (Emotions): 相关情绪
        
        请以JSON格式提供详细的认知模型分析。
        """
        
        # 准备消息
        messages = [
            {"role": "system", "content": "你是一位认知心理学专家，擅长分析心理认知模型。"}, 
            {"role": "user", "content": prompt}
        ]
        
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
            # 如果解析失败，尝试再次请求更结构化的输出
            retry_prompt = f"""
            之前的响应无法解析为JSON。请严格按照以下JSON结构提供认知模型分析:

            ```json
            {{
                "primary_appraisal": {{
                    "relevance": "对情境相关性的描述",
                    "nature": "对情境性质的描述"
                }},
                "secondary_appraisal": {{
                    "attribution": "对责任归因的描述",
                    "coping_ability": "对应对能力的描述",
                    "coping_strategy": "对应对策略的描述"
                }},
                "emotions": ["情绪1", "情绪2", ...]
            }}
            ```

            情境: {situation}
            """
            
            # 重试请求
            retry_messages = [
                {"role": "system", "content": "你是一位认知心理学专家，擅长分析心理认知模型。"}, 
                {"role": "user", "content": retry_prompt}
            ]
            
            retry_response = await self.generate_response("", messages=retry_messages, temperature=0.1)
            
            try:
                # 再次尝试解析
                json_str = retry_response
                if "```json" in retry_response:
                    json_str = retry_response.split("```json")[1].split("```")[0].strip()
                elif "```" in retry_response:
                    json_str = retry_response.split("```")[1].split("```")[0].strip()
                    
                return json.loads(json_str)
            except Exception as retry_e:
                # 如果仍然失败，返回基本结构
                return {
                    "raw_response": retry_response,
                    "error": str(retry_e),
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
    
    async def evaluate_mood(self, 
                      message: str, 
                      conversation_history: List[Dict[str, str]]) -> float:
        """
        评估情绪值
        """
        prompt = f"""
        作为情绪评估专家，请分析以下消息表达的情绪状态。
        
        消息: {message}
        
        请返回一个从-1到1的实数，表示情绪得分:
        -1: 极度负面情绪
        -0.5: 中度负面情绪
        0: 中性情绪
        0.5: 中度正面情绪
        1: 极度正面情绪
        
        只需返回具体数值，不要包含其他文本或解释。
        """
        
        # 准备消息
        messages = [
            {"role": "system", "content": "你是一位专业的情绪评估专家。你能够准确分析文本中表达的情绪状态，并用-1到1的分数表示。"}
        ]
        
        # 为了提供上下文，添加对话历史的最后几条
        if conversation_history and len(conversation_history) > 0:
            context_msgs = conversation_history[-3:]
            for msg in context_msgs:
                messages.append(msg)
        
        # 添加评估请求
        messages.append({"role": "user", "content": prompt})
        
        # 获取响应
        response = await self.generate_response("", messages=messages, temperature=0.1)
        
        # 尝试解析数值
        try:
            # 去除所有非数字和非小数点的字符
            cleaned_response = ''.join(c for c in response if c.isdigit() or c in ['.', '-'])
            mood_score = float(cleaned_response)
            # 确保在-1到1范围内
            mood_score = max(-1.0, min(1.0, mood_score))
            return mood_score
        except ValueError:
            # 默认返回中性情绪
            return 0.0
    
    async def evaluate_conversation(self, 
                              conversation_history: List[Dict[str, str]],
                              cognitive_model_truth: Dict[str, Any],
                              cognitive_model_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        作为专家评估对话质量和认知模型精确度
        """
        # 构建评估提示
        truth_json = json.dumps(cognitive_model_truth, ensure_ascii=False, indent=2)
        result_json = json.dumps(cognitive_model_result, ensure_ascii=False, indent=2)
        
        # 将对话历史格式化为文本
        conversation_text = "\n\n".join([
            f"{'Patient' if msg['role'] == 'assistant' else 'Therapist'}: {msg['content']}"
            for msg in conversation_history
        ])
        
        prompt = f"""
        你是一位专业的心理治疗评估专家。请全面评估以下心理咨询对话以及认知模型分析的质量。
        
        ## 对话记录
        {conversation_text}
        
        ## 真实认知模型
        {truth_json}
        
        ## 模型分析结果
        {result_json}
        
        请进行以下评估:
        
        1. 认知模型评估 (各项0-10分):
           - 情境相关性识别准确度
           - 情境性质判断准确度
           - 责任归因分析准确度
           - 应对能力评估准确度
           - 情绪识别准确度
           
        2. 对话质量评估 (各项0-10分):
           - 对话自然度
           - 角色一致性
           - 情绪表达适当性
           - 认知模式展现的合理性
           - 整体交互质量
           
        3. 简要文字总结:
           - 模型表现的主要优点
           - 模型表现的主要不足
           - 改进建议
        
        请以JSON格式返回评估结果。
        """
        
        # 准备消息
        messages = [
            {"role": "system", "content": "你是一位专业的心理治疗和认知评估专家，擅长评估治疗对话的质量和认知模型分析的准确性。"},
            {"role": "user", "content": prompt}
        ]
        
        # 获取响应
        response = await self.generate_response("", messages=messages, temperature=0.3)
        
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
            # 如果解析失败，重新尝试结构化输出
            retry_prompt = f"""
            请以严格的JSON格式提供评估结果，不要包含任何额外的文本说明：
            
            ```json
            {{
                "cognitive_model_scores": {{
                    "relevance_recognition": 分数,
                    "nature_assessment": 分数,
                    "attribution_analysis": 分数,
                    "coping_ability_assessment": 分数,
                    "emotion_recognition": 分数
                }},
                "dialogue_quality_scores": {{
                    "naturalness": 分数,
                    "character_consistency": 分数,
                    "emotional_expression": 分数,
                    "cognitive_pattern_presentation": 分数,
                    "overall_interaction_quality": 分数
                }},
                "summary": {{
                    "strengths": "主要优点",
                    "weaknesses": "主要不足",
                    "suggestions": "改进建议"
                }}
            }}
            ```
            """
            
            # 重试
            retry_messages = [
                {"role": "system", "content": "你是一位专业的心理治疗和认知评估专家。"},
                {"role": "user", "content": retry_prompt}
            ]
            
            retry_response = await self.generate_response("", messages=retry_messages, temperature=0.1)
            
            try:
                # 再次尝试解析
                json_str = retry_response
                if "```json" in retry_response:
                    json_str = retry_response.split("```json")[1].split("```")[0].strip()
                elif "```" in retry_response:
                    json_str = retry_response.split("```")[1].split("```")[0].strip()
                    
                return json.loads(json_str)
            except Exception as retry_e:
                # 如果仍然失败，返回基本结构
                return {
                    "raw_response": retry_response,
                    "error": str(retry_e),
                    "cognitive_model_scores": {
                        "relevance_recognition": 0,
                        "nature_assessment": 0,
                        "attribution_analysis": 0,
                        "coping_ability_assessment": 0,
                        "emotion_recognition": 0
                    },
                    "dialogue_quality_scores": {
                        "naturalness": 0,
                        "character_consistency": 0,
                        "emotional_expression": 0,
                        "cognitive_pattern_presentation": 0,
                        "overall_interaction_quality": 0
                    },
                    "summary": {
                        "strengths": "解析失败",
                        "weaknesses": "解析失败",
                        "suggestions": "解析失败"
                    }
                }
