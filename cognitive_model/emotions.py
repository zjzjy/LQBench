"""
情绪处理类，用于表示和处理情绪状态
"""
from typing import Dict, List, Any, Optional, Set


class Emotions:
    """
    情绪处理类，用于管理和比较情绪列表
    """
    
    # 常见情绪类别
    POSITIVE_EMOTIONS = {
        "快乐", "开心", "高兴", "兴奋", "满足", "愉悦", "喜悦", "幸福", 
        "欣慰", "感激", "放松", "自豪", "安心", "舒适", "满意", "期待"
    }
    
    NEGATIVE_EMOTIONS = {
        "悲伤", "难过", "沮丧", "痛苦", "失望", "后悔", "自责", "内疚", 
        "焦虑", "紧张", "恐惧", "害怕", "担忧", "愤怒", "生气", "烦躁", 
        "厌倦", "厌恶", "嫉妒", "无奈", "绝望", "孤独", "委屈", "尴尬"
    }
    
    NEUTRAL_EMOTIONS = {
        "平静", "冷静", "专注", "思考", "好奇", "惊讶", "困惑", "迷茫"
    }
    
    def __init__(self, emotions: List[str] = None):
        """
        初始化情绪类
        
        Args:
            emotions: 情绪列表
        """
        self.emotions = emotions or []
    
    @classmethod
    def from_list(cls, emotions: List[str]) -> 'Emotions':
        """
        从列表创建情绪实例
        
        Args:
            emotions: 情绪列表
            
        Returns:
            情绪实例
        """
        return cls(emotions=emotions)
    
    def to_list(self) -> List[str]:
        """
        将情绪转换为列表
        
        Returns:
            情绪列表
        """
        return self.emotions
    
    def categorize(self) -> Dict[str, List[str]]:
        """
        将情绪分类为积极、消极和中性
        
        Returns:
            分类后的情绪字典
        """
        result = {
            "positive": [],
            "negative": [],
            "neutral": [],
            "unknown": []
        }
        
        for emotion in self.emotions:
            emotion_lower = emotion.lower()
            if emotion in self.POSITIVE_EMOTIONS:
                result["positive"].append(emotion)
            elif emotion in self.NEGATIVE_EMOTIONS:
                result["negative"].append(emotion)
            elif emotion in self.NEUTRAL_EMOTIONS:
                result["neutral"].append(emotion)
            else:
                result["unknown"].append(emotion)
                
        return result
    
    def sentiment_score(self) -> float:
        """
        计算情绪的整体情感得分
        
        Returns:
            情感得分，范围为[-1, 1]，其中-1表示极度负面，1表示极度正面
        """
        if not self.emotions:
            return 0.0
            
        categorized = self.categorize()
        positive_count = len(categorized["positive"])
        negative_count = len(categorized["negative"])
        neutral_count = len(categorized["neutral"])
        unknown_count = len(categorized["unknown"])
        
        total = positive_count + negative_count + neutral_count + unknown_count
        
        if total == 0:
            return 0.0
            
        # 计算得分，积极情绪为正，消极情绪为负，中性和未知为0
        score = (positive_count - negative_count) / total
        return score
    
    def compare(self, other: 'Emotions') -> Dict[str, float]:
        """
        比较两个情绪集合的相似度
        
        Args:
            other: 另一个情绪实例
            
        Returns:
            包含相似度分数的字典
        """
        if not self.emotions or not other.emotions:
            return {"overlap": 0.0}
            
        set1 = set(e.lower() for e in self.emotions)
        set2 = set(e.lower() for e in other.emotions)
        
        # 计算重叠度 (Jaccard系数)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            overlap = 0.0
        else:
            overlap = intersection / union
            
        # 情感倾向相似度
        sentiment1 = self.sentiment_score()
        sentiment2 = other.sentiment_score()
        sentiment_diff = abs(sentiment1 - sentiment2)
        sentiment_sim = 1.0 - sentiment_diff
        
        return {
            "overlap": overlap,
            "sentiment_similarity": sentiment_sim,
            "overall": (overlap + sentiment_sim) / 2.0
        }
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            实例的字符串表示
        """
        if not self.emotions:
            return "无情绪"
        return ", ".join(self.emotions)
