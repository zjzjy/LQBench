"""
LQBench 对话评估模块
提供全面的对话质量评估和角色特征分析功能
"""

import os
import re
import json
import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import Counter, defaultdict

# 导入DeepSeek API调用相关模块
try:
    from api.llm import LLMClient
except ImportError:
    # 如果导入失败，提供一个空的实现
    class LLMClient:
        def __init__(self, *args, **kwargs):
            print("警告: 无法导入LLMClient，将使用模拟的API调用")
            
        def call(self, *args, **kwargs):
            return "未知"

class ConsistencyEvaluator:
    """
    角色特征归类器 - 分析对话内容，识别角色的沟通模式和依恋类型
    """
    
    def __init__(self, debug=False, use_api_fallback=True):
        """初始化评估器"""
        # 添加调试模式标志
        self.debug = debug
        # 是否启用API回退
        self.use_api_fallback = use_api_fallback
        # 初始化LLM客户端
        try:
            self.llm_client = LLMClient()
        except Exception as e:
            if self.debug:
                print(f"初始化LLM客户端失败: {str(e)}")
            self.llm_client = None
            self.use_api_fallback = False
        
        # 沟通类型关键词
        self.communication_keywords = {
            "直接表达": ["直接", "明确", "清楚", "坦率", "坦白", "直说", "实话"],
            "间接表达": ["可能", "也许", "或许", "好像", "感觉", "觉得", "我想"],
            "情感表达": ["开心", "难过", "失望", "生气", "感动", "愤怒", "失落", "伤心", "高兴", "担心"],
            "理性分析": ["分析", "理性", "逻辑", "思考", "认为", "合理", "原因", "因为", "所以"],
            "问题导向": ["为什么", "怎么", "如何", "是否", "是不是", "有没有", "吗", "？", "?"],
            "解决导向": ["解决", "办法", "方法", "建议", "对策", "措施", "行动", "试试", "尝试"]
        }
        
        # 依恋类型关键词和行为特征
        self.attachment_keywords = {
            "安全型": ["我爱你", "我理解", "我们可以", "一起解决", "尊重你", "理解你", "信任", "支持"],
            "焦虑型": ["真的吗", "确定吗", "离开我", "失去你", "需要你", "依赖你", "害怕", "担心", "不安"],
            "回避型": ["无所谓", "自己解决", "不重要", "空间", "不需要", "以后再说", "单独", "独立"],
            "混乱型": ["纠结", "困惑", "矛盾", "突然", "爆发", "指责", "不知道", "反复", "莫名"]
        }
        
        # 违禁行为关键词
        self.forbidden_behaviors = [
            "滚", "傻逼", "神经病", "贱", "烦死了", "滚开", "闭嘴", "白痴", "懒得理你", 
            "不想说了", "分手", "拉黑", "删除", "再见", "懒得搭理"
        ]
        
    def evaluate_dialogue(self, dialogue_history: List[Dict[str, Any]], debug=None) -> Dict[str, Any]:
        """
        分析整个对话历史，提取和归类角色特征
        
        Args:
            dialogue_history: 对话历史记录（消息列表）
            debug: 是否启用调试输出
        
        Returns:
            包含沟通类型、依恋类型等完整分析结果的字典
        """
        # 设置调试模式
        if debug is not None:
            self.debug = debug
            
        if self.debug:
            print("\n===== 开始评估对话(ConsistencyEvaluator) =====")
            print(f"对话历史包含 {len(dialogue_history)} 条记录")
            
        # 提取角色消息
        partner_messages = []
        partner_name = None
        
        if not dialogue_history:
            if self.debug:
                print("警告: 对话历史为空")
            return {
                "communication_type": "未知",
                "attachment_type": "未知",
                "forbidden_behaviors_count": 0,
                "communication_breakdown": {},
                "attachment_breakdown": {}
            }
            
        # 识别对话伴侣名称（如果有）
        for turn in dialogue_history:
            if "partner_name" in turn:
                partner_name = turn["partner_name"]
                break
        
        if self.debug:
            print(f"找到对话伴侣名称: {partner_name if partner_name else '未知'}")
            
        # 筛选对话伴侣消息
        for turn in dialogue_history:
            if "partner_message" in turn and turn["partner_message"]:
                partner_messages.append({
                    "message": turn["partner_message"],
                    "partner_name": partner_name
                })
        
        if self.debug:
            print(f"提取到 {len(partner_messages)} 条对话伴侣消息")
            for i, msg in enumerate(partner_messages):
                print(f"  消息 {i+1}: {msg['message'][:30]}..." if len(msg['message']) > 30 else f"  消息 {i+1}: {msg['message']}")
            
        # 评估沟通类型
        communication_type = self._evaluate_communication(partner_messages)
        
        # 如果规则式无法判断，尝试使用API
        if communication_type == "未知" and self.use_api_fallback and self.llm_client is not None:
            if self.debug:
                print("\n规则式方法无法判断沟通类型，尝试使用API分析...")
            communication_type = self._evaluate_communication_with_api(partner_messages)
        
        # 评估依恋类型
        attachment_type = self._evaluate_attachment(partner_messages)
        
        # 如果规则式无法判断，尝试使用API
        if attachment_type == "未知" and self.use_api_fallback and self.llm_client is not None:
            if self.debug:
                print("\n规则式方法无法判断依恋类型，尝试使用API分析...")
            attachment_type = self._evaluate_attachment_with_api(partner_messages)
        
        # 检测违反预设规则的行为
        forbidden_behaviors_count = self._count_forbidden_behaviors(partner_messages)
        
        # 获取详细统计数据
        communication_breakdown = self._get_communication_breakdown(partner_messages)
        attachment_breakdown = self._get_attachment_breakdown(partner_messages)
        
        if self.debug:
            print(f"评估结果:")
            print(f"  沟通类型: {communication_type}")
            print(f"  依恋类型: {attachment_type}")
            print(f"  违禁行为数量: {forbidden_behaviors_count}")
            print(f"  沟通类型详细分布: {communication_breakdown}")
            print(f"  依恋类型详细分布: {attachment_breakdown}")
            print("===== 评估对话完成 =====\n")
            
        # 组装结果
        result = {
            "communication_type": communication_type,
            "attachment_type": attachment_type,
            "forbidden_behaviors_count": forbidden_behaviors_count,
            "communication_breakdown": communication_breakdown,
            "attachment_breakdown": attachment_breakdown
        }
        
        return result
    
    def _evaluate_communication(self, messages: List[Dict[str, Any]]) -> str:
        """
        分析文本，确定主导沟通方式
        
        Args:
            messages: 角色消息列表
        
        Returns:
            主导沟通类型
        """
        if not messages:
            if self.debug:
                print("_evaluate_communication: 没有消息可供分析，返回'未知'")
            return "未知"
            
        # 统计各类型关键词出现频率
        type_counts = defaultdict(int)
        
        if self.debug:
            print("\n--- 沟通类型评估详情 ---")
            print(f"分析 {len(messages)} 条消息")
            
        for i, msg in enumerate(messages):
            text = msg["message"].lower()
            if self.debug:
                print(f"\n消息 {i+1}: {text[:50]}..." if len(text) > 50 else f"\n消息 {i+1}: {text}")
                matched_types = []
                
            for comm_type, keywords in self.communication_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        type_counts[comm_type] += 1
                        if self.debug:
                            matched_types.append(f"{comm_type}(关键词:{keyword})")
                            
            if self.debug:
                if matched_types:
                    print(f"  匹配类型: {', '.join(matched_types)}")
                else:
                    print("  未匹配任何沟通类型关键词")
        
        # 如果没有匹配任何类型，返回未知
        if not type_counts:
            if self.debug:
                print("\n未匹配任何沟通类型关键词，返回'未知'")
            return "未知"
            
        # 返回出现频率最高的类型
        dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]
        
        if self.debug:
            print("\n沟通类型统计结果:")
            for comm_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {comm_type}: {count} 次匹配")
            print(f"主导沟通类型: {dominant_type}")
            
        return dominant_type
    
    def _evaluate_attachment(self, messages: List[Dict[str, Any]]) -> str:
        """
        基于依恋理论分析文本，确定主导依恋类型
        
        Args:
            messages: 角色消息列表
        
        Returns:
            主导依恋类型
        """
        if not messages:
            if self.debug:
                print("_evaluate_attachment: 没有消息可供分析，返回'未知'")
            return "未知"
            
        # 统计各类型特征匹配度
        type_scores = defaultdict(int)
        
        if self.debug:
            print("\n--- 依恋类型评估详情 ---")
            print(f"分析 {len(messages)} 条消息")
            
        for i, msg in enumerate(messages):
            text = msg["message"].lower()
            if self.debug:
                print(f"\n消息 {i+1}: {text[:50]}..." if len(text) > 50 else f"\n消息 {i+1}: {text}")
                matched_types = []
                
            for attach_type, keywords in self.attachment_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        type_scores[attach_type] += 1
                        if self.debug:
                            matched_types.append(f"{attach_type}(关键词:{keyword})")
                            
            if self.debug:
                if matched_types:
                    print(f"  匹配类型: {', '.join(matched_types)}")
                else:
                    print("  未匹配任何依恋类型关键词")
        
        # 如果没有匹配任何类型，返回未知
        if not type_scores:
            if self.debug:
                print("\n未匹配任何依恋类型关键词，返回'未知'")
            return "未知"
            
        # 返回匹配度最高的类型
        dominant_type = max(type_scores.items(), key=lambda x: x[1])[0]
        
        if self.debug:
            print("\n依恋类型统计结果:")
            for attach_type, count in sorted(type_scores.items(), key=lambda x: x[1], reverse=True):
                print(f"  {attach_type}: {count} 次匹配")
            print(f"主导依恋类型: {dominant_type}")
            
        return dominant_type
    
    def _count_forbidden_behaviors(self, messages: List[Dict[str, Any]]) -> int:
        """
        检测违反预设沟通规则的行为
        
        Args:
            messages: 角色消息列表
        
        Returns:
            违禁行为出现次数
        """
        if not messages:
            return 0
            
        count = 0
        for msg in messages:
            text = msg["message"].lower()
            for behavior in self.forbidden_behaviors:
                if behavior in text:
                    count += 1
                    break  # 每条消息只计算一次违禁行为
        
        return count
    
    def _get_communication_breakdown(self, messages: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        提供各种沟通方式的详细比例统计
        
        Args:
            messages: 角色消息列表
        
        Returns:
            各沟通类型的归一化占比
        """
        if not messages:
            return {comm_type: 0.0 for comm_type in self.communication_keywords.keys()}
            
        # 统计各类型关键词出现频率
        type_counts = defaultdict(int)
        total_matches = 0
        
        for msg in messages:
            text = msg["message"].lower()
            for comm_type, keywords in self.communication_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        type_counts[comm_type] += 1
                        total_matches += 1
        
        # 计算比例
        breakdown = {}
        if total_matches > 0:
            for comm_type in self.communication_keywords.keys():
                breakdown[comm_type] = type_counts[comm_type] / total_matches if comm_type in type_counts else 0.0
        else:
            breakdown = {comm_type: 0.0 for comm_type in self.communication_keywords.keys()}
        
        return breakdown
    
    def _get_attachment_breakdown(self, messages: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        提供各种依恋类型的详细比例统计
        
        Args:
            messages: 角色消息列表
        
        Returns:
            各依恋类型的比例统计
        """
        if not messages:
            return {attach_type: 0.0 for attach_type in self.attachment_keywords.keys()}
            
        # 统计各类型特征匹配度
        type_scores = defaultdict(int)
        total_matches = 0
        
        for msg in messages:
            text = msg["message"].lower()
            for attach_type, keywords in self.attachment_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        type_scores[attach_type] += 1
                        total_matches += 1
        
        # 计算比例
        breakdown = {}
        if total_matches > 0:
            for attach_type in self.attachment_keywords.keys():
                breakdown[attach_type] = type_scores[attach_type] / total_matches if attach_type in type_scores else 0.0
        else:
            breakdown = {attach_type: 0.0 for attach_type in self.attachment_keywords.keys()}
        
        return breakdown
    
    def _evaluate_communication_with_api(self, messages: List[Dict[str, Any]]) -> str:
        """
        使用DeepSeek API分析文本，确定主导沟通方式
        
        Args:
            messages: 角色消息列表
        
        Returns:
            主导沟通类型
        """
        if not messages or not self.llm_client:
            return "未知"
            
        # 构建消息文本，用于API分析
        all_messages = "\n".join([f"{i+1}. {msg['message']}" for i, msg in enumerate(messages)])
        
        # 构建查询提示
        prompt = f"""请分析以下对话消息，判断其主要沟通类型，只从以下6个类型中选择一个最匹配的：
1. 直接表达：明确、清晰表达想法，直接陈述事实
2. 间接表达：委婉、含蓄表达想法，使用可能、也许等词语
3. 情感表达：侧重表达情感和感受，情绪化表达
4. 理性分析：侧重逻辑分析和理性思考，使用因为、所以等因果词语
5. 问题导向：通过提问探索问题，使用为什么、怎么等疑问词
6. 解决导向：注重寻找解决方案，提供具体建议和方法

消息内容：
{all_messages}

请分析这些消息的主要沟通类型，只返回对应的类型名称，不需要解释。例如：直接表达
"""
        
        try:
            # 调用DeepSeek API
            response = self.llm_client.call(prompt, temperature=0.1, max_tokens=50)
            
            if self.debug:
                print(f"API响应: {response}")
            
            # 从响应中提取沟通类型
            valid_types = ["直接表达", "间接表达", "情感表达", "理性分析", "问题导向", "解决导向"]
            
            # 查找有效类型
            for comm_type in valid_types:
                if comm_type in response:
                    return comm_type
                    
            return "未知"
            
        except Exception as e:
            if self.debug:
                print(f"API调用失败: {str(e)}")
            return "未知"
    
    def _evaluate_attachment_with_api(self, messages: List[Dict[str, Any]]) -> str:
        """
        使用DeepSeek API分析文本，确定主导依恋类型
        
        Args:
            messages: 角色消息列表
        
        Returns:
            主导依恋类型
        """
        if not messages or not self.llm_client:
            return "未知"
            
        # 构建消息文本，用于API分析
        all_messages = "\n".join([f"{i+1}. {msg['message']}" for i, msg in enumerate(messages)])
        
        # 构建查询提示
        prompt = f"""请分析以下对话消息，判断其表现出的主要依恋类型，只从以下4个类型中选择一个最匹配的：
1. 安全型：表现为信任、支持、理解、合作，能够坦诚交流
2. 焦虑型：表现为担忧、害怕被抛弃、不安全感，过度依赖、需要不断确认
3. 回避型：表现为保持距离、强调自我空间、回避情感交流、追求独立
4. 混乱型：表现为情绪不稳定、反复无常、矛盾心理

消息内容：
{all_messages}

请分析这些消息表现出的主要依恋类型，只返回对应的类型名称，不需要解释。例如：安全型
"""
        
        try:
            # 调用DeepSeek API
            response = self.llm_client.call(prompt, temperature=0.1, max_tokens=50)
            
            if self.debug:
                print(f"API响应: {response}")
            
            # 从响应中提取依恋类型
            valid_types = ["安全型", "焦虑型", "回避型", "混乱型"]
            
            # 查找有效类型
            for attach_type in valid_types:
                if attach_type in response:
                    return attach_type
                    
            return "未知"
            
        except Exception as e:
            if self.debug:
                print(f"API调用失败: {str(e)}")
            return "未知"


class DialogueEvaluator:
    """
    对话质量评估器 - 全面评估对话质量，分析互动模式
    """
    
    def __init__(self, dialogue_history: List[Dict[str, Any]] = None):
        """
        初始化评估器
        
        Args:
            dialogue_history: 对话历史记录
        """
        self.dialogue_history = dialogue_history
        self.emotion_history = None
        
        # 如果提供了对话历史，提取情感数据
        if dialogue_history:
            self._extract_emotion_history()
    
    def _extract_emotion_history(self):
        """提取情感历史数据"""
        if not self.dialogue_history:
            self.emotion_history = []
            return
            
        # 尝试从对话历史中提取情感数据
        self.emotion_history = []
        for entry in self.dialogue_history:
            if "emotion_info" in entry and entry["emotion_info"]:
                self.emotion_history.append(entry["emotion_info"])
    
    def evaluate_dialogue(self, dialogue_history=None, emotion_history=None) -> Dict[str, Any]:
        """
        执行全面评估，调用多个子评估模块
        
        Args:
            dialogue_history: 对话历史记录，如果为None则使用初始化时的对话历史
            emotion_history: 情感历史记录，如果为None则使用初始化时的情感历史
        
        Returns:
            包含多维度评估结果的综合字典
        """
        # 更新对话历史和情感历史（如果提供）
        if dialogue_history:
            self.dialogue_history = dialogue_history
            # 重新提取情感历史
            self._extract_emotion_history()
        
        if emotion_history:
            self.emotion_history = emotion_history
        
        # 如果没有对话历史，返回空结果
        if not self.dialogue_history:
            return {
                "dialogue_stats": {},
                "emotion_stats": {},
                "topic_coherence": 0.0,
                "interaction_quality": 0.0,
                "speaking_style": {},
                "listening_clarity": {},
                "positive_negative_factors": {},
                "consistency_score": 0.0,
                "quality_score": 0.0
            }
        
        # 计算各部分评估结果
        dialogue_stats = self._calculate_dialogue_stats(self.dialogue_history)
        emotion_stats = self._calculate_emotion_stats(self.emotion_history)
        topic_coherence = self._evaluate_topic_coherence(self.dialogue_history)
        interaction_quality = self._evaluate_interaction_quality(self.dialogue_history)
        speaking_style = self._evaluate_speaking_style(self.dialogue_history)
        listening_clarity = self._evaluate_listening_clarity(self.dialogue_history)
        positive_negative_factors = self._evaluate_positive_negative_factors(self.dialogue_history)
        
        # 计算综合评分
        consistency_score = self.evaluate_consistency()
        quality_score = self.evaluate_quality()
        
        # 组装结果
        result = {
            "dialogue_stats": dialogue_stats,
            "emotion_stats": emotion_stats,
            "topic_coherence": topic_coherence,
            "interaction_quality": interaction_quality,
            "speaking_style": speaking_style,
            "listening_clarity": listening_clarity,
            "positive_negative_factors": positive_negative_factors,
            "consistency_score": consistency_score,
            "quality_score": quality_score
        }
        
        return result
    
    def _calculate_dialogue_stats(self, dialogue_history) -> Dict[str, Any]:
        """
        计算基础对话统计数据
        
        Args:
            dialogue_history: 对话历史记录
        
        Returns:
            包含对话统计指标的字典
        """
        if not dialogue_history:
            return {
                "total_messages": 0,
                "avg_message_length": 0,
                "character_message_count": 0,
                "partner_message_count": 0,
                "partner_message_ratio": 0,
                "avg_partner_message_length": 0,
                "vocabulary_diversity": 0
            }
        
        # 提取消息
        character_messages = []
        partner_messages = []
        partner_name = None
        
        # 识别对话伴侣名称（如果有）
        for turn in dialogue_history:
            if "partner_name" in turn:
                partner_name = turn["partner_name"]
                break
        
        # 分类消息
        for turn in dialogue_history:
            if "character_message" in turn and turn["character_message"]:
                character_messages.append(turn["character_message"])
            if "partner_message" in turn and turn["partner_message"]:
                partner_messages.append(turn["partner_message"])
        
        # 计算统计数据
        total_messages = len(character_messages) + len(partner_messages)
        character_message_count = len(character_messages)
        partner_message_count = len(partner_messages)
        
        # 计算消息长度
        character_message_lengths = [len(msg) for msg in character_messages]
        partner_message_lengths = [len(msg) for msg in partner_messages]
        
        # 计算平均长度
        avg_character_message_length = np.mean(character_message_lengths) if character_messages else 0
        avg_partner_message_length = np.mean(partner_message_lengths) if partner_messages else 0
        avg_message_length = np.mean(character_message_lengths + partner_message_lengths) if total_messages > 0 else 0
        
        # 计算消息比例
        partner_message_ratio = partner_message_count / total_messages if total_messages > 0 else 0
        
        # 计算词汇多样性（Type-Token Ratio）
        all_words = []
        for msg in partner_messages:  # 只分析对话伴侣的词汇多样性
            words = re.findall(r'\w+', msg.lower())
            all_words.extend(words)
        
        unique_words = set(all_words)
        vocabulary_diversity = len(unique_words) / len(all_words) if all_words else 0
        
        # 组装结果
        result = {
            "total_messages": total_messages,
            "avg_message_length": avg_message_length,
            "character_message_count": character_message_count,
            "partner_message_count": partner_message_count,
            "partner_message_ratio": partner_message_ratio,
            "avg_partner_message_length": avg_partner_message_length,
            "vocabulary_diversity": vocabulary_diversity
        }
        
        return result
    
    def _calculate_emotion_stats(self, emotion_history) -> Dict[str, Any]:
        """
        分析情感变化指标
        
        Args:
            emotion_history: 情感历史记录
        
        Returns:
            包含情感统计指标的字典
        """
        if not emotion_history:
            return {
                "emotion_range": 0,
                "emotion_volatility": 0,
                "final_emotion": 0,
                "start_emotion": 0,
                "emotion_change": 0,  # 开始和结束的情绪差距
                "avg_emotion": 0,     # 平均情绪值
                "emotional_variance": 0,  # 情绪变化的方差
                "dominant_emotions": [],
                "emotion_trajectory": []
            }
        
        # 提取情感分数
        emotion_scores = []
        emotions_list = []
        
        for entry in emotion_history:
            # 兼容不同结构的情感数据
            if "score" in entry:
                emotion_scores.append(entry["score"])
            elif "emotion_score" in entry:
                emotion_scores.append(entry["emotion_score"])
                
            # 提取情感类型
            if "emotions" in entry and isinstance(entry["emotions"], list):
                emotions_list.extend(entry["emotions"])
            elif "primary_emotion" in entry:
                emotions_list.append(entry["primary_emotion"])
        
        # 如果没有情感数据，返回默认值
        if not emotion_scores:
            return {
                "emotion_range": 0,
                "emotion_volatility": 0,
                "final_emotion": 0,
                "start_emotion": 0,
                "emotion_change": 0,
                "avg_emotion": 0,
                "emotional_variance": 0,
                "dominant_emotions": [],
                "emotion_trajectory": []
            }
        
        # 计算情感范围（最高分-最低分）
        emotion_range = max(emotion_scores) - min(emotion_scores)
        
        # 计算情感波动性（相邻轮次情感变化的平均幅度）
        emotion_changes = [abs(emotion_scores[i] - emotion_scores[i-1]) for i in range(1, len(emotion_scores))]
        emotion_volatility = np.mean(emotion_changes) if emotion_changes else 0
        
        # 最终情感状态
        final_emotion = emotion_scores[-1] if emotion_scores else 0
        
        # 起始情感状态
        start_emotion = emotion_scores[0] if emotion_scores else 0
        
        # 计算情感变化（结束-开始）
        emotion_change = final_emotion - start_emotion
        
        # 计算平均情感值
        avg_emotion = np.mean(emotion_scores) if emotion_scores else 0
        
        # 计算情感方差（情绪波动幅度的另一种衡量）
        emotional_variance = np.var(emotion_scores) if len(emotion_scores) > 1 else 0
        
        # 主导情感类型
        emotion_counter = Counter(emotions_list)
        dominant_emotions = emotion_counter.most_common(3) if emotion_counter else []
        dominant_emotions = [emotion for emotion, count in dominant_emotions]
        
        # 情感分数变化曲线
        emotion_trajectory = emotion_scores
        
        # 组装结果
        result = {
            "emotion_range": emotion_range,
            "emotion_volatility": emotion_volatility,
            "final_emotion": final_emotion,
            "start_emotion": start_emotion,
            "emotion_change": emotion_change,
            "avg_emotion": avg_emotion,
            "emotional_variance": emotional_variance,
            "dominant_emotions": dominant_emotions,
            "emotion_trajectory": emotion_trajectory
        }
        
        return result
    
    def _evaluate_topic_coherence(self, dialogue_history) -> float:
        """
        评估对话主题的连贯性和流畅过渡
        
        Args:
            dialogue_history: 对话历史记录
        
        Returns:
            0-1范围的连贯性分数
        """
        if not dialogue_history or len(dialogue_history) < 2:
            return 0.0
        
        # 提取消息文本
        messages = []
        for turn in dialogue_history:
            if "character_message" in turn and turn["character_message"]:
                messages.append(turn["character_message"])
            if "partner_message" in turn and turn["partner_message"]:
                messages.append(turn["partner_message"])
        
        if len(messages) < 2:
            return 0.0
        
        # 计算相邻消息的词汇重叠度
        coherence_scores = []
        
        for i in range(1, len(messages)):
            prev_message = messages[i-1].lower()
            curr_message = messages[i].lower()
            
            # 分词
            prev_words = set(re.findall(r'\w+', prev_message))
            curr_words = set(re.findall(r'\w+', curr_message))
            
            # 如果一条消息没有有效词汇，跳过
            if not prev_words or not curr_words:
                continue
            
            # 计算重叠度（Jaccard相似度）
            overlap = len(prev_words.intersection(curr_words))
            union = len(prev_words.union(curr_words))
            
            if union > 0:
                coherence_scores.append(overlap / union)
        
        # 如果没有有效的重叠度计算，返回0
        if not coherence_scores:
            return 0.0
        
        # 返回平均重叠度作为连贯性分数
        return np.mean(coherence_scores)
    
    def _evaluate_interaction_quality(self, dialogue_history) -> float:
        """
        评估对话互动的质量和有效性
        
        Args:
            dialogue_history: 对话历史记录
        
        Returns:
            0-1范围的互动质量分数
        """
        if not dialogue_history or len(dialogue_history) < 2:
            return 0.0
        
        # 计算回复及时性（主要评估对话中的交替发言的流畅度）
        messages_flow_score = 0.0
        character_messages = []
        partner_messages = []
        
        # 分类消息
        for turn in dialogue_history:
            if "character_message" in turn and turn["character_message"]:
                character_messages.append(turn["character_message"])
            if "partner_message" in turn and turn["partner_message"]:
                partner_messages.append(turn["partner_message"])
        
        # 理想情况是角色和伴侣交替发言，消息数量相差不大
        if character_messages and partner_messages:
            min_messages = min(len(character_messages), len(partner_messages))
            max_messages = max(len(character_messages), len(partner_messages))
            messages_flow_score = min_messages / max_messages
        
        # 评估问题是否得到回应
        question_response_score = 0.0
        question_count = 0
        response_count = 0
        
        # 提取消息序列
        messages = []
        for turn in dialogue_history:
            if "character_message" in turn and turn["character_message"]:
                messages.append({"role": "character", "text": turn["character_message"]})
            if "partner_message" in turn and turn["partner_message"]:
                messages.append({"role": "partner", "text": turn["partner_message"]})
        
        # 检测问题和回应
        for i in range(len(messages) - 1):
            curr_message = messages[i]["text"]
            next_message = messages[i+1]["text"]
            
            # 检测当前消息是否包含问题
            if re.search(r'[?？]|\b(为什么|怎么|如何|是不是|能否|可不可以)\b', curr_message):
                question_count += 1
                
                # 检测下一条消息是否包含回应（简单启发式方法）
                if len(next_message) > 10:  # 回应通常有一定长度
                    response_count += 1
        
        # 计算问答对完整性得分
        if question_count > 0:
            question_response_score = response_count / question_count
        
        # 组合得分，权重可调整
        combined_score = 0.6 * messages_flow_score + 0.4 * question_response_score
        
        return combined_score
    
    def _evaluate_speaking_style(self, dialogue_history) -> Dict[str, Any]:
        """
        识别对话伴侣独特的说话风格和语言特征
        
        Args:
            dialogue_history: 对话历史记录
        
        Returns:
            说话风格分析结果
        """
        if not dialogue_history:
            return {
                "style_markers": {},
                "primary_style": "未知",
                "style_uniqueness": 0.0,
                "style_consistency": 0.0
            }
        
        # 风格标记分类
        style_markers = {
            "礼貌用语": ["请", "谢谢", "麻烦", "抱歉", "对不起", "感谢"],
            "撒娇语气": ["嘛", "呀", "啦", "哦", "呢", "嘤", "么么哒"],
            "犹豫语气": ["可能", "也许", "大概", "应该", "吧", "的话"],
            "强调语气": ["真的", "非常", "特别", "超级", "绝对", "一定"],
            "情感表达": ["爱", "喜欢", "开心", "难过", "生气", "害怕"],
            "口头禅": ["就是", "那个", "你知道", "其实", "说实话"],
            "疑问式表达": ["是吗", "对吗", "好吗", "可以吗", "行吗"],
            "条件式表达": ["如果", "要是", "假如", "除非", "只要"]
        }
        
        # 提取对话伴侣消息
        partner_messages = []
        for turn in dialogue_history:
            if "partner_message" in turn and turn["partner_message"]:
                partner_messages.append(turn["partner_message"])
        
        if not partner_messages:
            return {
                "style_markers": {style: 0 for style in style_markers},
                "primary_style": "未知",
                "style_uniqueness": 0.0,
                "style_consistency": 0.0
            }
        
        # 统计风格标记出现次数
        style_counts = defaultdict(int)
        total_style_markers = 0
        
        for msg in partner_messages:
            message_markers = set()  # 每条消息只计一次特定风格标记
            for style, markers in style_markers.items():
                for marker in markers:
                    if marker in msg:
                        style_counts[style] += 1
                        message_markers.add(style)
                        total_style_markers += 1
        
        # 计算风格比例
        style_ratios = {}
        for style in style_markers:
            style_ratios[style] = style_counts[style] / total_style_markers if total_style_markers > 0 else 0
        
        # 确定主要风格
        primary_style = max(style_ratios.items(), key=lambda x: x[1])[0] if style_ratios else "未知"
        
        # 计算风格独特性（主要风格与其他风格的区分度）
        primary_ratio = style_ratios.get(primary_style, 0)
        other_ratios = [ratio for style, ratio in style_ratios.items() if style != primary_style]
        avg_other_ratio = np.mean(other_ratios) if other_ratios else 0
        style_uniqueness = primary_ratio - avg_other_ratio if primary_ratio > 0 else 0
        
        # 计算风格一致性（消息中保持主要风格特征的比例）
        style_consistency = 0.0
        if partner_messages and primary_style != "未知":
            messages_with_primary_style = 0
            for msg in partner_messages:
                for marker in style_markers[primary_style]:
                    if marker in msg:
                        messages_with_primary_style += 1
                        break
            
            style_consistency = messages_with_primary_style / len(partner_messages)
        
        # 组装结果
        result = {
            "style_markers": style_ratios,
            "primary_style": primary_style,
            "style_uniqueness": style_uniqueness,
            "style_consistency": style_consistency
        }
        
        return result
    
    def _evaluate_listening_clarity(self, dialogue_history) -> Dict[str, Any]:
        """
        评估对话伴侣的倾听能力和表达清晰度
        
        Args:
            dialogue_history: 对话历史记录
        
        Returns:
            倾听能力和表达清晰度评估结果
        """
        if not dialogue_history or len(dialogue_history) < 2:
            return {
                "listening_score": 0.0,
                "clarity_score": 0.0,
                "avg_sentence_length": 0,
                "punctuation_ratio": 0.0,
                "overall_score": 0.0
            }
        
        # 提取对话消息序列
        messages = []
        for turn in dialogue_history:
            if "character_message" in turn and turn["character_message"]:
                messages.append({"role": "character", "text": turn["character_message"]})
            if "partner_message" in turn and turn["partner_message"]:
                messages.append({"role": "partner", "text": turn["partner_message"]})
        
        # 分析倾听能力
        listening_score = 0.0
        reference_count = 0
        valid_pairs = 0
        
        # 排除常见虚词和代词
        stopwords = ["的", "了", "是", "在", "我", "你", "他", "她", "它", "们", "和", "与", "这", "那", "就", "也", "都"]
        
        # 检测回复中对前一消息关键内容的引用
        for i in range(1, len(messages)):
            prev_message = messages[i-1]["text"]
            curr_message = messages[i]["text"]
            
            # 如果不是对话伴侣的回复，跳过
            if messages[i]["role"] != "partner":
                continue
                
            valid_pairs += 1
            
            # 分词并过滤虚词
            prev_words = [word for word in re.findall(r'\w+', prev_message) if word not in stopwords]
            
            # 检查回复中是否引用前一消息的关键内容
            for word in prev_words:
                if word in curr_message:
                    reference_count += 1
                    break
        
        # 计算倾听能力分数
        if valid_pairs > 0:
            listening_score = reference_count / valid_pairs
        
        # 分析表达清晰度
        clarity_score = 0.0
        total_sentences = 0
        total_chars = 0
        total_punctuations = 0
        
        for msg in messages:
            if msg["role"] != "partner":
                continue
                
            text = msg["text"]
            
            # 分句（使用句号、问号、感叹号作为分隔符）
            sentences = re.split(r'[。？！.?!]', text)
            sentences = [s for s in sentences if s.strip()]
            
            if not sentences:
                continue
                
            total_sentences += len(sentences)
            
            # 计算句子长度
            for sent in sentences:
                total_chars += len(sent)
            
            # 计算标点符号
            punctuations = len(re.findall(r'[，。、；：""？！,.;:"\'\?!]', text))
            total_punctuations += punctuations
        
        # 计算平均句长和标点比例
        avg_sentence_length = total_chars / total_sentences if total_sentences > 0 else 0
        punctuation_ratio = total_punctuations / total_chars if total_chars > 0 else 0
        
        # 理想句子长度区间10-25个字符
        length_score = 0.0
        if avg_sentence_length > 0:
            if 10 <= avg_sentence_length <= 25:
                length_score = 1.0
            elif avg_sentence_length < 10:
                length_score = avg_sentence_length / 10
            else:  # > 25
                length_score = max(0, 1 - (avg_sentence_length - 25) / 25)
        
        # 理想标点符号比例5%-15%
        punctuation_score = 0.0
        if punctuation_ratio > 0:
            if 0.05 <= punctuation_ratio <= 0.15:
                punctuation_score = 1.0
            elif punctuation_ratio < 0.05:
                punctuation_score = punctuation_ratio / 0.05
            else:  # > 0.15
                punctuation_score = max(0, 1 - (punctuation_ratio - 0.15) / 0.15)
        
        # 计算表达清晰度分数
        clarity_score = 0.6 * length_score + 0.4 * punctuation_score
        
        # 计算总体分数
        overall_score = 0.6 * listening_score + 0.4 * clarity_score
        
        # 组装结果
        result = {
            "listening_score": listening_score,
            "clarity_score": clarity_score,
            "avg_sentence_length": avg_sentence_length,
            "punctuation_ratio": punctuation_ratio,
            "overall_score": overall_score
        }
        
        return result
    
    def _evaluate_positive_negative_factors(self, dialogue_history) -> Dict[str, Any]:
        """
        评估对话中积极因素和负面因素的程度和平衡
        
        Args:
            dialogue_history: 对话历史记录
        
        Returns:
            积极因素和负面因素评估结果
        """
        if not dialogue_history:
            return {
                "positive_factors": {},
                "negative_factors": {},
                "positive_ratio": 0.0,
                "negative_ratio": 0.0,
                "balance_score": 0.0
            }
        
        # 积极因素类别和关键词
        positive_factors = {
            "我语句表达": ["我感到", "我觉得", "我认为", "对我来说", "让我", "使我"],
            "共情倾听": ["你的意思是", "你觉得", "你刚才说", "你的想法", "你的感受"],
            "开放式问题": ["怎么看", "为什么会", "是什么让你", "能说说", "怎么想的"],
            "积极肯定": ["谢谢你", "感谢你", "很欣赏", "很高兴", "好的一面", "做得好"],
            "寻求解决方案": ["我们可以", "或许我们", "有什么方法", "怎么解决", "一起想办法"]
        }
        
        # 负面因素类别和关键词
        negative_factors = {
            "批评": ["你总是", "你从不", "你每次", "又是这样", "就知道", "什么都不"],
            "轻蔑": ["呵呵", "真可笑", "无语", "懒得", "不值得", "白眼", "幼稚"],
            "防御": ["不是我的错", "又不是我", "关我什么事", "与我无关", "你才是"],
            "冷淡": ["随便吧", "不想说了", "不说了", "无所谓", "不理你了", "不回了"],
            "威胁": ["分手", "不理你", "不再", "如果你不", "后果", "绝交", "不原谅"],
            "过度概括": ["永远", "从来不", "一直都", "永远不会", "全都是", "所有人都"]
        }
        
        # 提取对话伴侣消息
        partner_messages = []
        for turn in dialogue_history:
            if "partner_message" in turn and turn["partner_message"]:
                partner_messages.append(turn["partner_message"])
        
        if not partner_messages:
            return {
                "positive_factors": {factor: 0 for factor in positive_factors},
                "negative_factors": {factor: 0 for factor in negative_factors},
                "positive_ratio": 0.0,
                "negative_ratio": 0.0,
                "balance_score": 0.0
            }
        
        # 统计积极因素
        positive_counts = defaultdict(int)
        total_positive = 0
        
        for msg in partner_messages:
            for factor, keywords in positive_factors.items():
                for keyword in keywords:
                    if keyword in msg:
                        positive_counts[factor] += 1
                        total_positive += 1
                        break  # 每个因素在一条消息中只计算一次
        
        # 统计负面因素
        negative_counts = defaultdict(int)
        total_negative = 0
        
        for msg in partner_messages:
            for factor, keywords in negative_factors.items():
                for keyword in keywords:
                    if keyword in msg:
                        negative_counts[factor] += 1
                        total_negative += 1
                        break  # 每个因素在一条消息中只计算一次
        
        # 计算积极和负面因素的比例
        total_factors = total_positive + total_negative
        positive_ratio = total_positive / total_factors if total_factors > 0 else 0
        negative_ratio = total_negative / total_factors if total_factors > 0 else 0
        
        # 计算平衡分数
        # 基于戈特曼5:1理论，设定理想积极/负面比例为7:3至8:2
        balance_score = 0.0
        if total_factors > 0:
            # 如果积极比例在理想区间内
            if 0.7 <= positive_ratio <= 0.8:
                balance_score = 1.0
            # 如果积极比例过低
            elif positive_ratio < 0.7:
                balance_score = positive_ratio / 0.7
            # 如果积极比例过高（缺乏一定的负面表达）
            else:  # > 0.8
                balance_score = max(0, 1 - (positive_ratio - 0.8) / 0.2)
        
        # 计算积极因素的详细比例
        positive_factor_ratios = {}
        for factor in positive_factors:
            positive_factor_ratios[factor] = positive_counts[factor] / total_positive if total_positive > 0 else 0
        
        # 计算负面因素的详细比例
        negative_factor_ratios = {}
        for factor in negative_factors:
            negative_factor_ratios[factor] = negative_counts[factor] / total_negative if total_negative > 0 else 0
        
        # 组装结果
        result = {
            "positive_factors": positive_factor_ratios,
            "negative_factors": negative_factor_ratios,
            "positive_ratio": positive_ratio,
            "negative_ratio": negative_ratio,
            "balance_score": balance_score
        }
        
        return result
    
    def evaluate_consistency(self) -> float:
        """
        评估对话一致性得分
        
        Returns:
            0-10范围的一致性得分
        """
        if not self.dialogue_history:
            return 0.0
        
        # 获取各部分评分
        topic_coherence = self._evaluate_topic_coherence(self.dialogue_history)
        interaction_quality = self._evaluate_interaction_quality(self.dialogue_history)
        
        # 获取说话风格一致性
        speaking_style = self._evaluate_speaking_style(self.dialogue_history)
        style_consistency = speaking_style.get("style_consistency", 0.0)
        
        # 计算加权得分
        weighted_score = (
            0.4 * topic_coherence +
            0.4 * interaction_quality +
            0.2 * style_consistency
        )
        
        # 转换到0-10范围
        consistency_score = weighted_score * 10
        
        return consistency_score
    
    def evaluate_quality(self) -> float:
        """
        评估整体对话质量得分
        
        Returns:
            0-10范围的质量得分
        """
        if not self.dialogue_history:
            return 0.0
        
        # 获取各部分评分
        topic_coherence = self._evaluate_topic_coherence(self.dialogue_history)
        interaction_quality = self._evaluate_interaction_quality(self.dialogue_history)
        
        # 获取词汇多样性
        dialogue_stats = self._calculate_dialogue_stats(self.dialogue_history)
        vocabulary_diversity = dialogue_stats.get("vocabulary_diversity", 0.0)
        
        # 获取说话风格独特性
        speaking_style = self._evaluate_speaking_style(self.dialogue_history)
        style_uniqueness = speaking_style.get("style_uniqueness", 0.0)
        
        # 获取倾听和表达清晰度
        listening_clarity = self._evaluate_listening_clarity(self.dialogue_history)
        listening_clarity_score = listening_clarity.get("overall_score", 0.0)
        
        # 获取积极/负面因素平衡
        positive_negative = self._evaluate_positive_negative_factors(self.dialogue_history)
        balance_score = positive_negative.get("balance_score", 0.0)
        
        # 计算加权得分
        weighted_score = (
            0.2 * topic_coherence +
            0.2 * interaction_quality +
            0.1 * vocabulary_diversity +
            0.15 * style_uniqueness +
            0.2 * listening_clarity_score +
            0.15 * balance_score
        )
        
        # 转换到0-10范围
        quality_score = weighted_score * 10
        
        return quality_score
    
    def get_emotion_statistics(self) -> Dict[str, int]:
        """
        获取对话中情感表达的统计数据
        
        Returns:
            各情感出现次数的字典
        """
        if not self.dialogue_history:
            return {
                "高兴": 0,
                "难过": 0,
                "生气": 0,
                "焦虑": 0,
                "嫉妒": 0,
                "平静": 0
            }
        
        # 情感类别映射
        emotion_mapping = {
            "快乐": "高兴", "开心": "高兴", "高兴": "高兴", "喜悦": "高兴", "欣喜": "高兴", "愉悦": "高兴",
            "悲伤": "难过", "难过": "难过", "伤心": "难过", "忧郁": "难过", "沮丧": "难过", "失落": "难过",
            "愤怒": "生气", "生气": "生气", "恼怒": "生气", "烦躁": "生气", "不满": "生气", "厌恶": "生气",
            "焦虑": "焦虑", "担忧": "焦虑", "紧张": "焦虑", "恐惧": "焦虑", "害怕": "焦虑", "不安": "焦虑",
            "嫉妒": "嫉妒", "妒忌": "嫉妒", "羡慕": "嫉妒",
            "平静": "平静", "满足": "平静", "安心": "平静", "放松": "平静", "中性": "平静", "neutral": "平静"
        }
        
        # 统计情感出现次数
        emotion_counts = defaultdict(int)
        emotions_list = []
        
        # 从情感历史中提取情感类型
        if self.emotion_history:
            for entry in self.emotion_history:
                if "emotions" in entry and isinstance(entry["emotions"], list):
                    emotions_list.extend(entry["emotions"])
                elif "primary_emotion" in entry:
                    emotions_list.append(entry["primary_emotion"])
        
        # 从对话文本中识别情感词汇
        emotion_keywords = {
            "高兴": ["开心", "高兴", "快乐", "喜悦", "欣喜", "愉快", "兴奋", "甜蜜", "雀跃"],
            "难过": ["难过", "伤心", "悲伤", "忧郁", "沮丧", "失落", "痛苦", "心碎", "低落"],
            "生气": ["生气", "愤怒", "恼火", "生闷气", "发火", "恼怒", "烦躁", "不满", "厌恶"],
            "焦虑": ["焦虑", "担忧", "紧张", "害怕", "恐惧", "慌张", "不安", "压力", "忧虑"],
            "嫉妒": ["嫉妒", "妒忌", "羡慕", "眼红", "不平衡"],
            "平静": ["平静", "安稳", "满足", "安心", "放松", "平和", "淡定", "安定"]
        }
        
        # 从对话文本中识别情感
        for turn in self.dialogue_history:
            if "character_message" in turn and turn["character_message"]:
                message = turn["character_message"].lower()
                for emotion, keywords in emotion_keywords.items():
                    for keyword in keywords:
                        if keyword in message:
                            emotions_list.append(emotion)
                            break
        
        # 映射情感类型并统计
        for emotion in emotions_list:
            if isinstance(emotion, str):
                emotion_lower = emotion.lower()
                mapped_emotion = None
                
                # 尝试直接映射
                for key, value in emotion_mapping.items():
                    if emotion_lower == key.lower():
                        mapped_emotion = value
                        break
                
                # 如果没有直接映射，尝试部分匹配
                if not mapped_emotion:
                    for key, value in emotion_mapping.items():
                        if emotion_lower in key.lower() or key.lower() in emotion_lower:
                            mapped_emotion = value
                            break
                
                # 如果仍然没有映射，归类为平静
                if not mapped_emotion:
                    mapped_emotion = "平静"
                
                emotion_counts[mapped_emotion] += 1
        
        # 确保所有情感类别都存在
        result = {
            "高兴": emotion_counts.get("高兴", 0),
            "难过": emotion_counts.get("难过", 0),
            "生气": emotion_counts.get("生气", 0),
            "焦虑": emotion_counts.get("焦虑", 0),
            "嫉妒": emotion_counts.get("嫉妒", 0),
            "平静": emotion_counts.get("平静", 0)
        }
        
        return result


def analyze_dialogue_log(log_file: str) -> Dict[str, Any]:
    """
    分析单个对话日志文件
    
    Args:
        log_file: 日志文件路径
    
    Returns:
        包含一致性和对话质量评估的完整结果字典
    """
    try:
        # 加载日志文件
        with open(log_file, 'r', encoding='utf-8') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"解析日志文件 {log_file} 时出错: {str(e)}")
                return {
                    "error": f"解析日志文件时出错: {str(e)}",
                    "file": log_file,
                    "status": "error"
                }
        
        # 提取对话历史和元数据
        dialogue_history = log_data.get("dialogue_history", [])
        character = log_data.get("character", {})
        scenario = log_data.get("scenario", {})
        emotion_history = log_data.get("emotion_history", [])
        
        # 创建评估器实例
        consistency_evaluator = ConsistencyEvaluator()
        dialogue_evaluator = DialogueEvaluator(dialogue_history)
        
        # 执行评估
        consistency_result = consistency_evaluator.evaluate_dialogue(dialogue_history)
        dialogue_result = dialogue_evaluator.evaluate_dialogue(dialogue_history, emotion_history)
        
        # 合并元数据和评估结果
        result = {
            "file": log_file,
            "character": {
                "name": character.get("name", "未知"),
                "id": character.get("id", "未知"),
                "gender": character.get("gender", "未知"),
                "age": character.get("age", "未知"),
                "personality_type": character.get("personality_type", "未知"),
                "attachment_style": character.get("attachment_style", "未知")
            },
            "scenario": {
                "id": scenario.get("scenario", {}).get("id", "未知") if isinstance(scenario.get("scenario"), dict) else "未知",
                "name": scenario.get("scenario", {}).get("name", "未知") if isinstance(scenario.get("scenario"), dict) else "未知",
                "situation": scenario.get("situation", {}).get("name", "未知") if isinstance(scenario.get("situation"), dict) else "未知"
            },
            "dialogue_stats": dialogue_result["dialogue_stats"],
            "emotion_stats": dialogue_result["emotion_stats"],
            "consistency": {
                "score": dialogue_result["consistency_score"],
                "topic_coherence": dialogue_result["topic_coherence"],
                "interaction_quality": dialogue_result["interaction_quality"],
                "speaking_style": dialogue_result["speaking_style"]
            },
            "quality": {
                "score": dialogue_result["quality_score"],
                "listening_clarity": dialogue_result["listening_clarity"],
                "positive_negative": dialogue_result["positive_negative_factors"]
            },
            "character_traits": {
                "communication_type": consistency_result["communication_type"],
                "attachment_type": consistency_result["attachment_type"],
                "forbidden_behaviors_count": consistency_result["forbidden_behaviors_count"],
                "communication_breakdown": consistency_result["communication_breakdown"],
                "attachment_breakdown": consistency_result["attachment_breakdown"]
            },
            "emotions": dialogue_evaluator.get_emotion_statistics(),
            "status": "success"
        }
        
        return result
    
    except Exception as e:
        # 处理任何其他异常
        print(f"分析日志文件 {log_file} 时出现异常: {str(e)}")
        return {
            "error": f"分析日志文件时出现异常: {str(e)}",
            "file": log_file,
            "status": "error"
        }


def batch_analyze_logs(log_dir: str) -> Dict[str, Any]:
    """
    批量分析目录中的所有对话日志
    
    Args:
        log_dir: 日志目录路径
    
    Returns:
        包含汇总统计和详细结果的字典
    """
    if not os.path.exists(log_dir) or not os.path.isdir(log_dir):
        return {
            "error": f"日志目录 {log_dir} 不存在或不是一个目录",
            "status": "error"
        }
    
    # 获取所有JSON日志文件（排除带有prompts的文件）
    log_files = []
    for file in os.listdir(log_dir):
        if file.endswith('.json') and 'prompts' not in file:
            log_files.append(os.path.join(log_dir, file))
    
    if not log_files:
        return {
            "error": f"日志目录 {log_dir} 中没有找到有效的日志文件",
            "status": "error"
        }
    
    # 分析每个日志文件
    results = []
    success_count = 0
    error_count = 0
    
    for log_file in log_files:
        result = analyze_dialogue_log(log_file)
        results.append(result)
        
        if result.get("status") == "success":
            success_count += 1
        else:
            error_count += 1
    
    # 计算汇总统计
    avg_consistency_score = 0.0
    avg_quality_score = 0.0
    avg_turns = 0.0
    communication_types = defaultdict(int)
    attachment_types = defaultdict(int)
    emotion_counts = defaultdict(int)
    
    for result in results:
        if result.get("status") != "success":
            continue
            
        avg_consistency_score += result.get("consistency", {}).get("score", 0)
        avg_quality_score += result.get("quality", {}).get("score", 0)
        avg_turns += result.get("dialogue_stats", {}).get("total_messages", 0)
        
        # 统计沟通类型和依恋类型
        comm_type = result.get("character_traits", {}).get("communication_type")
        if comm_type:
            communication_types[comm_type] += 1
            
        attach_type = result.get("character_traits", {}).get("attachment_type")
        if attach_type:
            attachment_types[attach_type] += 1
            
        # 汇总情感统计
        emotions = result.get("emotions", {})
        for emotion, count in emotions.items():
            emotion_counts[emotion] += count
    
    # 计算平均值
    if success_count > 0:
        avg_consistency_score /= success_count
        avg_quality_score /= success_count
        avg_turns /= success_count
    
    # 组装汇总结果
    summary = {
        "total_logs": len(log_files),
        "success_count": success_count,
        "error_count": error_count,
        "avg_consistency_score": avg_consistency_score,
        "avg_quality_score": avg_quality_score,
        "avg_turns": avg_turns,
        "communication_types": dict(communication_types),
        "attachment_types": dict(attachment_types),
        "emotion_counts": dict(emotion_counts)
    }
    
    # 返回汇总和详细结果
    return {
        "summary": summary,
        "results": results,
        "status": "success"
    }


# 以下代码用于测试和示例
if __name__ == "__main__":
    import argparse
    import datetime
    import os
    
    # 设置命令行参数
    parser = argparse.ArgumentParser(description="LQBench对话评估工具")
    
    # 配置文件选项
    parser.add_argument("-c", "--config", help="配置文件路径，JSON格式")
    
    # 输入选项
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument("-f", "--file", help="评估单个对话日志文件")
    input_group.add_argument("-d", "--directory", help="批量评估指定目录中的所有对话日志文件")
    
    # 输出选项
    parser.add_argument("-o", "--output", help="评估结果输出目录", default="evaluation_results")
    
    # API配置选项
    parser.add_argument("--use-api", action="store_true", help="启用API回退功能，当规则式方法无法判断时使用")
    parser.add_argument("--api-key", help="API密钥")
    parser.add_argument("--model", help="使用的模型名称")
    
    # 调试选项
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    # 解析参数
    args = parser.parse_args()
    
    # 加载配置文件(如果指定)
    config = {}
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"已加载配置文件: {args.config}")
        except Exception as e:
            print(f"加载配置文件出错: {str(e)}")
    
    # 合并配置，命令行参数优先
    def get_param(arg_name, config_name=None):
        if config_name is None:
            config_name = arg_name
        # 检查命令行参数
        arg_value = getattr(args, arg_name)
        # 如果命令行参数未指定，尝试从配置文件获取
        if arg_value is None or (isinstance(arg_value, bool) and arg_value is False):
            return config.get(config_name, arg_value)
        return arg_value

    # 获取参数值（命令行优先，然后是配置文件）
    use_api = get_param("use_api")
    api_key = get_param("api_key")
    model = get_param("model")
    debug = get_param("debug")
    output_dir = get_param("output", "output_dir")
    single_file = get_param("file", "input_file")
    directory = get_param("directory", "input_directory")
    
    # 确保至少有一个输入源
    if not single_file and not directory:
        if "input_file" in config:
            single_file = config["input_file"]
        elif "input_directory" in config:
            directory = config["input_directory"]
        else:
            print("错误: 必须指定输入文件(-f/--file)或输入目录(-d/--directory)")
            parser.print_help()
            sys.exit(1)
    
    # 配置API客户端
    api_config = {}
    if use_api:
        if api_key:
            api_config["api_key"] = api_key
        if model:
            api_config["model"] = model
            
        # 尝试导入LLMClient
        try:
            from api.llm import LLMClient
            llm_client = LLMClient(**api_config)
        except ImportError:
            print("警告: 无法导入LLMClient，API回退功能将不可用")
            use_api = False
        except Exception as e:
            print(f"初始化API客户端失败: {str(e)}")
            use_api = False
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 生成时间戳，用于文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 处理单个文件评估
    if single_file:
        print(f"正在评估单个文件: {single_file}")
        
        # 创建评估器实例
        evaluator = ConsistencyEvaluator(debug=debug, use_api_fallback=use_api)
        if use_api and 'llm_client' in locals():
            evaluator.llm_client = llm_client
        
        # 执行评估
        result = analyze_dialogue_log(single_file)
        
        # 保存结果
        output_file = os.path.join(output_dir, f"evaluation_{os.path.basename(single_file)}_{timestamp}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"评估完成，结果已保存至: {output_file}")
        
        # 打印简要结果
        if result.get("status") == "success":
            print("\n=== 评估结果摘要 ===")
            print(f"沟通类型: {result.get('character_traits', {}).get('communication_type', '未知')}")
            print(f"依恋类型: {result.get('character_traits', {}).get('attachment_type', '未知')}")
            print(f"一致性得分: {result.get('consistency', {}).get('score', 0):.2f}")
            print(f"质量得分: {result.get('quality', {}).get('score', 0):.2f}")
        else:
            print(f"评估出错: {result.get('error', '未知错误')}")
    
    # 处理目录批量评估
    elif directory:
        print(f"正在批量评估目录: {directory}")
        
        # 配置全局LLMClient（如果启用API）
        if use_api and 'llm_client' in locals():
            # 修补ConsistencyEvaluator类以使用全局LLMClient
            original_init = ConsistencyEvaluator.__init__
            
            def patched_init(self, debug=False, use_api_fallback=True):
                original_init(self, debug, use_api_fallback)
                if 'llm_client' in globals():
                    self.llm_client = llm_client
                    
            ConsistencyEvaluator.__init__ = patched_init
        
        # 执行批量评估
        batch_results = batch_analyze_logs(directory)
        
        # 保存批量结果
        output_file = os.path.join(output_dir, f"batch_evaluation_{timestamp}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, ensure_ascii=False, indent=2)
        
        print(f"批量评估完成，结果已保存至: {output_file}")
        
        # 打印汇总信息
        if batch_results.get("status") == "success":
            summary = batch_results.get("summary", {})
            print("\n=== 批量评估摘要 ===")
            print(f"总文件数: {summary.get('total_logs', 0)}")
            print(f"成功: {summary.get('success_count', 0)}, 失败: {summary.get('error_count', 0)}")
            print(f"平均对话轮次: {summary.get('avg_turns', 0):.2f}")
            print(f"平均一致性得分: {summary.get('avg_consistency_score', 0):.2f}")
            print(f"平均质量得分: {summary.get('avg_quality_score', 0):.2f}")
            
            # 打印沟通类型和依恋类型统计
            print("\n沟通类型统计:")
            for comm_type, count in summary.get('communication_types', {}).items():
                print(f"  {comm_type}: {count}")
                
            print("\n依恋类型统计:")
            for attach_type, count in summary.get('attachment_types', {}).items():
                print(f"  {attach_type}: {count}")
        else:
            print(f"批量评估出错: {batch_results.get('error', '未知错误')}")