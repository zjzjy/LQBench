"""
虚拟人物类，用于模拟不同性格和认知模式的人物
"""
from typing import Dict, List, Any, Optional
import asyncio

from models.expert import ExpertModel
from persona.conversation_styles import get_conversation_style

class Persona:
    """
    虚拟人物类，用于构建和模拟具有特定认知模型的虚拟角色
    """
    
    def __init__(self,
                 expert_model: ExpertModel,
                 persona_config: Dict[str, Any],
                 situation: str,
                 conversation_style_name: str = "plain"):
        """
        初始化虚拟人物
        
        Args:
            expert_model: 专家模型实例，用于生成角色扮演回复
            persona_config: 人物基本配置信息
            situation: 当前面临的情景
            conversation_style_name: 对话风格名称
        """
        self.expert_model = expert_model
        self.persona_config = persona_config
        self.situation = situation
        self.conversation_style = get_conversation_style(conversation_style_name)
        self.conversation_history = []
        self.mood_history = []
        self.cognitive_model_history = []
        
        # 初始认知模型为空，后续会生成
        self.cognitive_model = None
    
    async def initialize_cognitive_model(self) -> Dict[str, Any]:
        """
        初始化认知模型，基于人物设定和情境
        
        Returns:
            生成的认知模型
        """
        self.cognitive_model = await self.expert_model.analyze_cognitive_model([], self.situation)
        self.cognitive_model_history.append(self.cognitive_model)
        return self.cognitive_model
    
    async def respond(self, user_message: str) -> str:
        """
        生成虚拟人物对用户消息的回复
        
        Args:
            user_message: 用户消息
            
        Returns:
            虚拟人物的回复
        """
        # 确保认知模型已初始化
        if self.cognitive_model is None:
            await self.initialize_cognitive_model()
            
        # 将用户消息添加到对话历史
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # 生成响应
        response = await self.expert_model.persona_response(
            persona_config=self.persona_config,
            situation=self.situation,
            conversation_history=self.conversation_history,
            conversation_style=self.conversation_style["prompt"],
            cognitive_model=self.cognitive_model
        )
        
        # 将响应添加到对话历史
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # 评估当前情绪并记录
        mood = await self.expert_model.evaluate_mood(response, self.conversation_history)
        self.mood_history.append(mood)
        
        return response
    
    async def get_current_mood(self) -> float:
        """
        获取当前情绪值
        
        Returns:
            当前情绪值（-1到1）
        """
        if not self.mood_history:
            return 0.0
        return self.mood_history[-1]
    
    async def get_mood_trend(self) -> float:
        """
        获取情绪变化趋势
        
        Returns:
            情绪变化趋势，正值表示改善，负值表示恶化
        """
        if len(self.mood_history) < 2:
            return 0.0
            
        # 计算最近3次或所有记录的平均变化
        window = min(3, len(self.mood_history) - 1)
        changes = [self.mood_history[i] - self.mood_history[i-1] for i in range(len(self.mood_history) - window, len(self.mood_history))]
        return sum(changes) / len(changes)
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        获取对话历史
        
        Returns:
            对话历史列表
        """
        return self.conversation_history
    
    def get_mood_history(self) -> List[float]:
        """
        获取情绪历史
        
        Returns:
            情绪历史列表
        """
        return self.mood_history
    
    def get_cognitive_model_history(self) -> List[Dict[str, Any]]:
        """
        获取认知模型历史
        
        Returns:
            认知模型历史列表
        """
        return self.cognitive_model_history
