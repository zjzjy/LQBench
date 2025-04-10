"""
LLM模型基类，定义所有模型需要实现的接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BaseModel(ABC):
    """
    所有LLM模型的基类，定义了统一的接口
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模型
        
        Args:
            config: 模型配置参数
        """
        self.config = config
        self.model_name = config.get("model_name", "unknown")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
        self.api_key = config.get("api_key", None)
        self.api_base = config.get("api_base", None)
        
        if not self.api_key:
            raise ValueError(f"API密钥未提供，模型 {self.model_name} 无法初始化")
    
    @abstractmethod
    async def generate_response(self, 
                          prompt: str, 
                          messages: Optional[List[Dict[str, str]]] = None,
                          **kwargs) -> str:
        """
        生成模型响应
        
        Args:
            prompt: 提示文本
            messages: 消息历史，格式为[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            **kwargs: 其他参数
            
        Returns:
            模型生成的响应文本
        """
        pass
    
    @abstractmethod
    async def analyze_cognitive_model(self, 
                                conversation_history: List[Dict[str, str]],
                                situation: str) -> Dict[str, Any]:
        """
        根据对话历史分析认知模型
        
        Args:
            conversation_history: 对话历史
            situation: 情境描述
            
        Returns:
            认知模型分析结果，包含primary appraisal和secondary appraisal
        """
        pass
    
    @abstractmethod
    async def evaluate_mood(self, 
                      message: str, 
                      conversation_history: List[Dict[str, str]]) -> float:
        """
        评估消息的情绪状态
        
        Args:
            message: 待评估的消息
            conversation_history: 对话历史
            
        Returns:
            情绪分数，范围通常为[-1, 1]，-1表示极度负面，1表示极度正面
        """
        pass
    
    @abstractmethod
    async def evaluate_conversation(self, 
                              conversation_history: List[Dict[str, str]],
                              cognitive_model_truth: Dict[str, Any],
                              cognitive_model_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估整个对话的质量
        
        Args:
            conversation_history: 对话历史
            cognitive_model_truth: 真实的认知模型
            cognitive_model_result: 模型生成的认知模型
            
        Returns:
            评估结果，包含各项指标的分数
        """
        pass
