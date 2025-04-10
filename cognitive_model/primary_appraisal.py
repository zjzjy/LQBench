"""
认知模型中的初级评估（Primary Appraisal）实现
"""
from typing import Dict, Any, List, Optional


class PrimaryAppraisal:
    """
    初级评估类，用于表示个体对情境的基本评估
    """
    
    def __init__(self, relevance: str = None, nature: str = None):
        """
        初始化初级评估
        
        Args:
            relevance: 情境相关性，描述情境对个体的重要性
            nature: 情境性质，描述情境是积极的还是消极的
        """
        self.relevance = relevance
        self.nature = nature
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PrimaryAppraisal':
        """
        从字典创建初级评估实例
        
        Args:
            data: 包含初级评估信息的字典
            
        Returns:
            初级评估实例
        """
        relevance = data.get('relevance')
        nature = data.get('nature')
        return cls(relevance=relevance, nature=nature)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将初级评估转换为字典
        
        Returns:
            包含初级评估信息的字典
        """
        return {
            'relevance': self.relevance,
            'nature': self.nature
        }
    
    def compare(self, other: 'PrimaryAppraisal') -> Dict[str, float]:
        """
        比较两个初级评估的相似度
        
        Args:
            other: 另一个初级评估实例
            
        Returns:
            包含相似度分数的字典
        """
        # 简单实现，后续可以用更复杂的语义相似度计算
        scores = {}
        
        # 相关性比较
        if self.relevance and other.relevance:
            if self.relevance.lower() == other.relevance.lower():
                scores['relevance'] = 1.0
            else:
                # 这里可以用更复杂的相似度计算
                scores['relevance'] = 0.5
        else:
            scores['relevance'] = 0.0
            
        # 性质比较
        if self.nature and other.nature:
            if self.nature.lower() == other.nature.lower():
                scores['nature'] = 1.0
            else:
                # 这里可以用更复杂的相似度计算
                scores['nature'] = 0.5
        else:
            scores['nature'] = 0.0
            
        # 总体相似度
        scores['overall'] = (scores['relevance'] + scores['nature']) / 2.0
        
        return scores
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            实例的字符串表示
        """
        return f"相关性: {self.relevance or '未指定'}, 性质: {self.nature or '未指定'}"
