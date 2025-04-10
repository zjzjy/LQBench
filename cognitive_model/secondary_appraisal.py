"""
认知模型中的次级评估（Secondary Appraisal）实现
"""
from typing import Dict, Any, List, Optional


class SecondaryAppraisal:
    """
    次级评估类，用于表示个体对情境的进一步评估
    """
    
    def __init__(self, 
                 attribution: str = None, 
                 coping_ability: str = None, 
                 coping_strategy: str = None):
        """
        初始化次级评估
        
        Args:
            attribution: 责任归因，描述个体将情境责任归于何处
            coping_ability: 应对能力评估，描述个体对自己应对情境能力的评估
            coping_strategy: 应对策略，描述个体采用的应对方式
        """
        self.attribution = attribution
        self.coping_ability = coping_ability
        self.coping_strategy = coping_strategy
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecondaryAppraisal':
        """
        从字典创建次级评估实例
        
        Args:
            data: 包含次级评估信息的字典
            
        Returns:
            次级评估实例
        """
        attribution = data.get('attribution')
        coping_ability = data.get('coping_ability')
        coping_strategy = data.get('coping_strategy')
        return cls(
            attribution=attribution,
            coping_ability=coping_ability,
            coping_strategy=coping_strategy
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将次级评估转换为字典
        
        Returns:
            包含次级评估信息的字典
        """
        return {
            'attribution': self.attribution,
            'coping_ability': self.coping_ability,
            'coping_strategy': self.coping_strategy
        }
    
    def compare(self, other: 'SecondaryAppraisal') -> Dict[str, float]:
        """
        比较两个次级评估的相似度
        
        Args:
            other: 另一个次级评估实例
            
        Returns:
            包含相似度分数的字典
        """
        # 简单实现，后续可以用更复杂的语义相似度计算
        scores = {}
        
        # 责任归因比较
        if self.attribution and other.attribution:
            if self.attribution.lower() == other.attribution.lower():
                scores['attribution'] = 1.0
            else:
                # 这里可以用更复杂的相似度计算
                scores['attribution'] = 0.5
        else:
            scores['attribution'] = 0.0
            
        # 应对能力比较
        if self.coping_ability and other.coping_ability:
            if self.coping_ability.lower() == other.coping_ability.lower():
                scores['coping_ability'] = 1.0
            else:
                # 这里可以用更复杂的相似度计算
                scores['coping_ability'] = 0.5
        else:
            scores['coping_ability'] = 0.0
            
        # 应对策略比较
        if self.coping_strategy and other.coping_strategy:
            if self.coping_strategy.lower() == other.coping_strategy.lower():
                scores['coping_strategy'] = 1.0
            else:
                # 这里可以用更复杂的相似度计算
                scores['coping_strategy'] = 0.5
        else:
            scores['coping_strategy'] = 0.0
            
        # 总体相似度
        scores['overall'] = (scores['attribution'] + scores['coping_ability'] + scores['coping_strategy']) / 3.0
        
        return scores
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            实例的字符串表示
        """
        return (
            f"责任归因: {self.attribution or '未指定'}, "
            f"应对能力: {self.coping_ability or '未指定'}, "
            f"应对策略: {self.coping_strategy or '未指定'}"
        )
