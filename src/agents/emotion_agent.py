import json
import logging
import os
import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import random
import numpy as np

# 导入NLP库
import jieba
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from snownlp import SnowNLP
from textblob import TextBlob

# 确保下载NLTK必要的资源
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')
    nltk.download('punkt')

class EmotionAgent:
    """
    情绪监测Agent，使用自然语言处理方法实时分析角色的情绪状态
    """
    
    def __init__(self):
        """
        初始化情绪监测Agent，使用NLP方法替代大语言模型
        """
        self.logger = logging.getLogger(__name__)
        self.character_info = None
        self.current_scenario = None
        self.emotion_history = []
        
        # 定义主要情绪类别
        self.primary_emotions = [
            "angry", "sad", "afraid", "happy", "surprised", "disgusted", "neutral"
        ]
        
        # 情绪词典
        self.emotion_lexicon = self._load_emotion_lexicon()
        
        # 中文情绪词典
        if self.emotion_lexicon and "emotions" in self.emotion_lexicon:
            self.emotion_keywords = {emotion: data.get("words", []) 
                                    for emotion, data in self.emotion_lexicon["emotions"].items()}
        else:
            # 基础情绪词典
            self.emotion_keywords = {
                "angry": ["生气", "愤怒", "烦躁", "恼火", "不满", "暴躁", "气愤", "恼怒", "激动", "发火"],
                "sad": ["悲伤", "难过", "伤心", "沮丧", "痛苦", "忧伤", "哀愁", "凄凉", "苦闷", "忧郁"],
                "afraid": ["害怕", "恐惧", "担心", "忧虑", "惊恐", "焦虑", "惊慌", "担忧", "惶恐", "不安"],
                "happy": ["开心", "高兴", "快乐", "喜悦", "欣喜", "愉快", "兴奋", "欢乐", "满足", "幸福"],
                "surprised": ["惊讶", "震惊", "吃惊", "诧异", "意外", "不可思议", "惊异", "惊诧", "惊愕", "愕然"],
                "disgusted": ["厌恶", "反感", "恶心", "讨厌", "嫌弃", "憎恨", "鄙视", "唾弃", "痛恨", "蔑视"],
                "neutral": ["平静", "中性", "一般", "正常", "普通", "无感", "平淡", "平常", "不置可否", "不冷不热"]
            }
        
        # 情绪强度阈值设置
        self.emotion_intensity_threshold = {
            "positive": 85,  # 高于此值视为非常积极
            "negative": 15   # 低于此值视为非常消极
        }
        
        # 初始化情感分析器
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # 加载配置
        self._load_thresholds()
        
    def _load_emotion_lexicon(self) -> Dict:
        """
        加载情感词典
        
        Returns:
            情感词典字典
        """
        try:
            base_dir = Path(__file__).resolve().parent.parent.parent
            lexicon_path = base_dir / "data" / "nlp" / "chinese_emotion_lexicon.json"
            
            if not lexicon_path.exists():
                self.logger.warning(f"情感词典文件不存在: {lexicon_path}")
                return {}
                
            with open(lexicon_path, 'r', encoding='utf-8') as f:
                lexicon = json.load(f)
                
            self.logger.info(f"成功加载情感词典: {lexicon_path}")
            return lexicon
                
        except Exception as e:
            self.logger.error(f"加载情感词典失败: {e}")
            return {}
    
    def _load_thresholds(self) -> None:
        """从配置文件加载情绪阈值设置"""
        try:
            base_dir = Path(__file__).resolve().parent.parent.parent
            config_path = base_dir / "config" / "experiment_config.json"
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            thresholds = config.get("experiment", {}).get("default_stop_conditions", {}).get("emotion", {})
            if thresholds:
                self.emotion_intensity_threshold["positive"] = thresholds.get(
                    "positive_threshold", self.emotion_intensity_threshold["positive"]
                )
                self.emotion_intensity_threshold["negative"] = thresholds.get(
                    "negative_threshold", self.emotion_intensity_threshold["negative"]
                )
                self.logger.info(f"已加载情绪阈值：积极={self.emotion_intensity_threshold['positive']}，"
                              f"消极={self.emotion_intensity_threshold['negative']}")
        except Exception as e:
            self.logger.warning(f"加载情绪阈值设置失败，使用默认值: {e}")
    
    def set_character_info(self, character_info: Dict) -> None:
        """
        设置角色信息
        
        Args:
            character_info: 角色定义字典
        """
        self.character_info = character_info
        self.logger.info(f"为情绪监测Agent设置角色 {character_info.get('name', 'unknown')}")
    
    def set_scenario_info(self, scenario: Dict) -> None:
        """
        设置当前场景
        
        Args:
            scenario: 场景定义字典
        """
        self.current_scenario = scenario
        self.logger.info(f"为情绪监测Agent设置场景 {scenario.get('id', 'unknown')}")
        
    def set_scenario(self, scenario: Dict) -> None:
        """
        设置当前场景（兼容旧API）
        
        Args:
            scenario: 场景定义字典
        """
        self.set_scenario_info(scenario)
    
    def _build_system_prompt(self) -> str:
        """
        构建系统提示词
        
        Returns:
            系统提示词
        """
        system_prompt = """你是一位情感分析专家，专门负责分析对话中人物的情绪状态。你需要根据提供的对话内容，分析角色的情绪状态，并给出情绪类型和强度评分。

你的任务是：
1. 确定主要情绪 (angry, sad, afraid, happy, surprised, disgusted, neutral)
2. 确定情绪强度（0-100分，其中0表示极端负面情绪，100表示极端正面情绪，50表示中性）
3. 提供对情绪变化的简要解释

请以JSON格式输出结果，不要添加任何额外的文字。正确的输出格式示例：
{
    "primary_emotion": "sad",
    "emotion_intensity": 35,
    "explanation": "角色表现出明显的伤心情绪，因为感到被忽视和不被重视。"
}

只评估角色的情绪，不要评估伴侣的情绪。你的输出必须是有效的JSON格式。"""
        return system_prompt
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """
        使用多种NLP工具分析文本情感
        
        Args:
            text: 待分析的文本
            
        Returns:
            情感分析结果，包含积极性得分
        """
        result = {"compound": 0.0, "positive": 0.0, "negative": 0.0, "neutral": 0.0}
        
        # 使用VADER进行情感分析（英文文本）
        vader_scores = self.sentiment_analyzer.polarity_scores(text)
        
        # 使用SnowNLP进行中文情感分析
        try:
            # SnowNLP的情感分析结果是0-1之间的数，1为积极，0为消极
            snow_score = SnowNLP(text).sentiments
            snow_positive = snow_score
            snow_negative = 1 - snow_score
        except Exception as e:
            self.logger.warning(f"SnowNLP分析失败: {e}")
            snow_positive = 0.5
            snow_negative = 0.5
        
        # 综合多种分析结果
        result["positive"] = (vader_scores["pos"] + snow_positive) / 2
        result["negative"] = (vader_scores["neg"] + snow_negative) / 2
        result["neutral"] = vader_scores["neu"]
        
        # 计算复合得分 (-1到1之间)
        result["compound"] = vader_scores["compound"] * 0.5 + (snow_positive - 0.5) * 1.0
        
        # 使用自定义情感词典进行额外分析
        lexicon_score = self._analyze_with_lexicon(text)
        if lexicon_score:
            # 综合词典分析结果
            result["compound"] = (result["compound"] + lexicon_score["score"]) / 2
            result["emotion_type"] = lexicon_score["emotion_type"]
            
        return result
    
    def _analyze_with_lexicon(self, text: str) -> Dict:
        """
        使用情感词典分析文本
        
        Args:
            text: 待分析的文本
            
        Returns:
            分析结果，包含情绪类型和得分
        """
        if not self.emotion_lexicon:
            return {}
            
        # 分词
        words = list(jieba.cut(text))
        
        # 记录每种情绪的匹配计数和强度
        emotion_scores = {emotion: {"count": 0, "score": 0.0} for emotion in self.primary_emotions}
        
        # 检测否定词
        negations = self.emotion_lexicon.get("negations", ["不", "没", "没有", "不是"])
        negation_positions = [i for i, word in enumerate(words) if word in negations]
        
        # 获取强度词
        intensifiers = self.emotion_lexicon.get("intensifiers", {})
        intensifiers_score = self.emotion_lexicon.get("intensifiers_score", {})
        all_intensifiers = []
        for category in intensifiers.values():
            all_intensifiers.extend(category)
        
        # 遍历单词
        for i, word in enumerate(words):
            # 检查是否是情绪词
            for emotion, keyword_list in self.emotion_keywords.items():
                if word in keyword_list:
                    # 检查前面是否有否定词
                    is_negated = any(neg_pos < i and i - neg_pos <= 3 for neg_pos in negation_positions)
                    
                    # 检查前面是否有强度词
                    intensity_modifier = 1.0
                    if i > 0 and words[i-1] in all_intensifiers:
                        intensity_modifier = intensifiers_score.get(words[i-1], 1.0)
                    
                    # 计算得分
                    base_score = 1.0
                    if is_negated:
                        # 否定词会改变情绪类型
                        if emotion in ["happy", "surprised"]:
                            emotion_scores["sad"]["count"] += 1
                            emotion_scores["sad"]["score"] += base_score * intensity_modifier
                        elif emotion in ["angry", "disgusted"]:
                            emotion_scores["neutral"]["count"] += 1
                            emotion_scores["neutral"]["score"] += base_score * intensity_modifier
                        else:
                            emotion_scores["neutral"]["count"] += 1
                            emotion_scores["neutral"]["score"] += base_score * intensity_modifier
                    else:
                        # 正常情绪得分
                        emotion_scores[emotion]["count"] += 1
                        emotion_scores[emotion]["score"] += base_score * intensity_modifier
        
        # 检查情绪短语
        if "emotions" in self.emotion_lexicon:
            for emotion, data in self.emotion_lexicon["emotions"].items():
                if "phrases" in data:
                    for phrase in data["phrases"]:
                        if phrase in text:
                            emotion_scores[emotion]["count"] += 2  # 短语匹配权重更高
                            emotion_scores[emotion]["score"] += 2.0
        
        # 确定主要情绪类型
        total_count = sum(data["count"] for data in emotion_scores.values())
        if total_count == 0:
            return {}
            
        # 找出得分最高的情绪
        max_emotion = max(emotion_scores.items(), key=lambda x: x[1]["score"])
        emotion_type = max_emotion[0]
        
        # 计算情绪得分 (-1到1之间)
        if emotion_type in ["happy", "surprised"]:
            score = max_emotion[1]["score"] / (total_count + 1) * 2 - 1  # 映射到(-1,1)区间
        elif emotion_type in ["angry", "sad", "afraid", "disgusted"]:
            score = -(max_emotion[1]["score"] / (total_count + 1) * 2)  # 负面情绪用负值表示
        else:
            score = 0.0  # 中性情绪
            
        return {
            "emotion_type": emotion_type,
            "score": max(-1.0, min(1.0, score)),  # 限制在[-1,1]范围内
            "emotion_counts": {e: data["count"] for e, data in emotion_scores.items() if data["count"] > 0}
        }
    
    def detect_emotion_keywords(self, text: str) -> Dict[str, int]:
        """
        检测文本中的情绪关键词
        
        Args:
            text: 待分析的文本
            
        Returns:
            各情绪类别的关键词计数
        """
        # 使用jieba进行中文分词
        words = list(jieba.cut(text))
        
        # 计算每种情绪的关键词出现次数
        emotion_counts = {emotion: 0 for emotion in self.primary_emotions}
        
        for word in words:
            for emotion, keywords in self.emotion_keywords.items():
                if word in keywords:
                    emotion_counts[emotion] += 1
        
        # 检查情绪短语
        if "emotions" in self.emotion_lexicon:
            for emotion, data in self.emotion_lexicon["emotions"].items():
                if "phrases" in data:
                    for phrase in data["phrases"]:
                        if phrase in text:
                            emotion_counts[emotion] += 2  # 短语匹配权重更高
        
        return emotion_counts
    
    def analyze_emotion(self, 
                       character_message: str, 
                       dialogue_history: Optional[List[Dict]] = None,
                       turn_number: Optional[int] = None) -> Dict:
        """
        分析角色的情绪状态，使用增强的上下文感知方法
        
        Args:
            character_message: 角色最新的消息
            dialogue_history: 可选的对话历史
            turn_number: 当前对话回合数
            
        Returns:
            情绪分析结果字典
        """
        try:
            # 1. 基础情感分析
            sentiment_result = self.analyze_text_sentiment(character_message)
            
            # 2. 检测情绪关键词
            emotion_keywords = self.detect_emotion_keywords(character_message)
            
            # 3. 分析上下文情感（如果有对话历史）
            context_analysis = {}
            if dialogue_history and len(dialogue_history) > 1:
                context_analysis = self._analyze_context_emotions(dialogue_history, character_message)
            
            # 4. 分析句子结构和语气
            structure_analysis = self._analyze_sentence_structure(character_message)
            
            # 5. 综合分析结果确定主要情绪
            final_emotion, confidence = self._determine_final_emotion(
                sentiment_result, 
                emotion_keywords, 
                context_analysis,
                structure_analysis
            )
            
            # 6. 计算情绪强度 (0-100)
            emotion_intensity = self._calculate_emotion_intensity(
                final_emotion,
                sentiment_result,
                structure_analysis,
                context_analysis
            )
            
            # 7. 生成解释
            explanation = self._generate_emotion_explanation(
                final_emotion, 
                emotion_intensity, 
                sentiment_result,
                context_analysis
            )
            
            # 8. 构建结果
            result = {
                "primary_emotion": final_emotion,
                "emotion_intensity": emotion_intensity,
                "explanation": explanation,
                "confidence": confidence,
                "sentiment_scores": {
                    "positive": sentiment_result["positive"],
                    "negative": sentiment_result["negative"],
                    "neutral": sentiment_result["neutral"],
                    "compound": sentiment_result["compound"]
                },
                "emotion_keywords": emotion_keywords,
                "context_factors": context_analysis.get("factors", {}),
            }
            
            # 添加回合信息
            if turn_number is not None:
                result["turn"] = turn_number
            
            # 添加到历史
            self.emotion_history.append(result)
            
            return result
                
        except Exception as e:
            self.logger.error(f"情绪分析失败: {e}")
            # 返回默认值
            default_result = {
                "primary_emotion": "neutral",
                "emotion_intensity": 50,
                "explanation": f"情绪分析失败: {str(e)}，使用默认中性情绪。",
                "error": True
            }
            if turn_number is not None:
                default_result["turn"] = turn_number
            
            self.emotion_history.append(default_result)
            return default_result
    
    def _analyze_context_emotions(self, dialogue_history: List[Dict], current_message: str) -> Dict:
        """
        分析对话上下文中的情绪变化
        
        Args:
            dialogue_history: 对话历史
            current_message: 当前消息
            
        Returns:
            上下文情绪分析结果
        """
        # 提取角色的最近几条消息
        recent_character_messages = []
        recent_partner_messages = []
        
        # 默认最多看前5条消息
        for msg in dialogue_history[-5:]:
            sender = msg.get("sender", "")
            if sender == "character":
                recent_character_messages.append(msg.get("content", ""))
            elif sender == "partner":
                recent_partner_messages.append(msg.get("content", ""))
        
        # 分析角色之前的情绪状态
        previous_emotions = []
        for msg in recent_character_messages:
            sentiment = self.analyze_text_sentiment(msg)
            previous_emotions.append(sentiment.get("compound", 0))
        
        # 分析伙伴最近的情绪状态
        partner_emotion = 0
        if recent_partner_messages:
            partner_sentiment = self.analyze_text_sentiment(recent_partner_messages[-1])
            partner_emotion = partner_sentiment.get("compound", 0)
        
        # 分析情绪变化趋势
        emotion_trend = "stable"
        if previous_emotions:
            if len(previous_emotions) >= 2:
                if previous_emotions[-1] > previous_emotions[0] + 0.3:
                    emotion_trend = "improving"
                elif previous_emotions[-1] < previous_emotions[0] - 0.3:
                    emotion_trend = "deteriorating"
        
        # 检测对话中的情绪触发因素
        triggers = {}
        if recent_partner_messages:
            last_partner_msg = recent_partner_messages[-1]
            # 检测最后一条伙伴消息中可能触发情绪的关键词
            partner_keywords = self.detect_emotion_keywords(last_partner_msg)
            triggers["partner_emotions"] = partner_keywords
            
            # 检测问题和请求
            if "?" in last_partner_msg:
                triggers["question"] = True
            if any(word in last_partner_msg.lower() for word in ["请", "麻烦", "能否", "可以", "希望"]):
                triggers["request"] = True
            
            # 检测道歉和感谢
            if any(word in last_partner_msg for word in ["对不起", "抱歉", "不好意思", "道歉"]):
                triggers["apology"] = True
            if any(word in last_partner_msg for word in ["谢谢", "感谢", "谢谢你", "感激"]):
                triggers["gratitude"] = True
        
        return {
            "previous_emotions": previous_emotions,
            "emotion_trend": emotion_trend,
            "partner_emotion": partner_emotion,
            "factors": {
                "triggers": triggers,
                "recent_messages_count": len(recent_character_messages),
                "emotional_volatility": np.std(previous_emotions) if previous_emotions else 0
            }
        }
    
    def _analyze_sentence_structure(self, text: str) -> Dict:
        """
        分析句子结构和语气
        
        Args:
            text: 要分析的文本
            
        Returns:
            句子结构分析结果
        """
        # 检测句子类型
        sentence_types = {
            "question": "?" in text,
            "exclamation": "!" in text,
            "ellipsis": "..." in text or "…" in text,
        }
        
        # 计算标点符号频率
        punctuation_count = {
            "?": text.count("?"),
            "!": text.count("!"),
            ".": text.count("."),
            "...": text.count("...") + text.count("…"),
            "，": text.count("，"),
            "。": text.count("。"),
        }
        
        # 重复标点可能表示强烈情绪
        emphasis_score = punctuation_count["!"] * 0.5 + punctuation_count["?"] * 0.3
        
        # 检测强调词
        emphasis_words = ["非常", "太", "真的", "真是", "极其", "十分", "特别", "格外", "尤其"]
        emphasis_count = sum(1 for word in emphasis_words if word in text)
        
        # 检测情感强度词
        intensity_markers = {
            "high": ["极", "最", "绝对", "简直", "彻底"],
            "low": ["有点", "稍微", "略微", "一点点", "有些"]
        }
        
        intensity_high = sum(1 for word in intensity_markers["high"] if word in text)
        intensity_low = sum(1 for word in intensity_markers["low"] if word in text)
        
        # 检测句子长度
        words = list(jieba.cut(text))
        sentence_length = len(words)
        
        # 判断是否有重复表达
        repetition = self._check_repetition(words)
        
        return {
            "sentence_types": sentence_types,
            "punctuation": punctuation_count,
            "emphasis_score": emphasis_score + emphasis_count * 0.7,
            "intensity": {
                "high": intensity_high,
                "low": intensity_low,
                "score": intensity_high * 0.8 - intensity_low * 0.5
            },
            "sentence_length": sentence_length,
            "repetition": repetition
        }
    
    def _check_repetition(self, words: List[str]) -> Dict:
        """
        检查文本中的重复表达
        
        Args:
            words: 分词后的单词列表
            
        Returns:
            重复度分析
        """
        # 统计词频
        word_counts = {}
        for word in words:
            if len(word) > 1:  # 忽略单字符词
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # 找出重复的词
        repeated_words = {word: count for word, count in word_counts.items() if count > 1}
        
        # 计算重复度分数
        repetition_score = sum(count - 1 for count in repeated_words.values())
        
        return {
            "repeated_words": repeated_words,
            "score": repetition_score
        }
    
    def _determine_final_emotion(self, sentiment_result: Dict, emotion_keywords: Dict, 
                               context_analysis: Dict, structure_analysis: Dict) -> Tuple[str, float]:
        """
        综合各种分析结果确定最终情绪类型
        
        Args:
            sentiment_result: 情感分析结果
            emotion_keywords: 情绪关键词分析
            context_analysis: 上下文分析结果
            structure_analysis: 句子结构分析
            
        Returns:
            (最终情绪类型, 置信度)
        """
        # 初始候选情绪及权重
        candidates = {emotion: 0 for emotion in self.primary_emotions}
        
        # 1. 基于情感分析的初步判断
        compound_score = sentiment_result.get("compound", 0)
        if "emotion_type" in sentiment_result:
            candidates[sentiment_result["emotion_type"]] += 2.5
        elif compound_score >= 0.5:
            candidates["happy"] += 2.0
        elif compound_score <= -0.5:
            if sentiment_result["negative"] > 0.3:
                candidates["angry"] += 1.0
                candidates["sad"] += 1.0
            else:
                candidates["sad"] += 1.5
        elif compound_score < 0 and compound_score > -0.5:
            candidates["afraid"] += 0.7
            candidates["sad"] += 0.7
        else:
            candidates["neutral"] += 1.5
        
        # 2. 基于情绪关键词的权重添加
        max_keyword_count = max(emotion_keywords.values()) if emotion_keywords else 0
        if max_keyword_count > 0:
            for emotion, count in emotion_keywords.items():
                candidates[emotion] += count * 1.5
        
        # 3. 句子结构对情绪的影响
        # 感叹句和强调词增强情绪强度
        if structure_analysis["sentence_types"]["exclamation"]:
            if compound_score > 0:
                candidates["happy"] += 0.8
                candidates["surprised"] += 0.6
            else:
                candidates["angry"] += 0.8
                candidates["sad"] += 0.4
        
        # 问句可能表示惊讶或担忧
        if structure_analysis["sentence_types"]["question"]:
            candidates["surprised"] += 0.5
            candidates["afraid"] += 0.3
        
        # 省略号可能表示犹豫或悲伤
        if structure_analysis["sentence_types"]["ellipsis"]:
            candidates["sad"] += 0.4
            candidates["afraid"] += 0.3
        
        # 高强度词增强情绪
        intensity_score = structure_analysis["intensity"]["score"]
        if intensity_score > 0:
            # 放大最高的情绪
            max_emotion = max(candidates.items(), key=lambda x: x[1])[0]
            candidates[max_emotion] += intensity_score * 0.5
        
        # 4. 上下文因素的影响
        if context_analysis:
            # 考虑情绪趋势
            trend = context_analysis.get("emotion_trend", "stable")
            if trend == "improving":
                candidates["happy"] += 0.6
                candidates["neutral"] += 0.3
            elif trend == "deteriorating":
                candidates["sad"] += 0.4
                candidates["angry"] += 0.4
            
            # 考虑伙伴情绪的影响（情绪共鸣或反向反应）
            partner_emotion = context_analysis.get("partner_emotion", 0)
            if partner_emotion > 0.3:  # 伙伴情绪积极
                candidates["happy"] += 0.4  # 情绪共鸣
            elif partner_emotion < -0.3:  # 伙伴情绪消极
                if compound_score < 0:  # 角色也消极，可能共鸣
                    candidates["sad"] += 0.3
                    candidates["angry"] += 0.2
            
            # 考虑触发因素
            triggers = context_analysis.get("factors", {}).get("triggers", {})
            if triggers.get("apology", False):
                # 对方道歉可能缓解愤怒
                candidates["angry"] -= 0.5
                if compound_score > 0:
                    candidates["happy"] += 0.4
            if triggers.get("gratitude", False):
                # 对方感谢可能增加快乐
                candidates["happy"] += 0.3
        
        # 确定最终情绪
        final_emotion = max(candidates.items(), key=lambda x: x[1])[0]
        
        # 计算置信度 (0-1)
        total_weight = sum(candidates.values())
        confidence = candidates[final_emotion] / total_weight if total_weight > 0 else 0.5
        
        return final_emotion, min(1.0, confidence)
    
    def _calculate_emotion_intensity(self, emotion: str, sentiment_result: Dict, 
                                   structure_analysis: Dict, context_analysis: Dict) -> int:
        """
        计算情绪强度
        
        Args:
            emotion: 情绪类型
            sentiment_result: 情感分析结果
            structure_analysis: 句子结构分析
            context_analysis: 上下文分析
            
        Returns:
            情绪强度 (0-100)
        """
        # 基础强度 (0-100)
        base_intensity = int((sentiment_result["compound"] + 1) * 50)
        
        # 结构因素调整
        structure_adjustment = 0
        structure_adjustment += structure_analysis["emphasis_score"] * 5
        structure_adjustment += structure_analysis["intensity"]["score"] * 5
        structure_adjustment += min(5, structure_analysis["repetition"]["score"] * 3)
        
        # 标点符号影响
        structure_adjustment += structure_analysis["punctuation"]["!"] * 5
        structure_adjustment += structure_analysis["punctuation"]["?"] * 2
        
        # 上下文因素调整
        context_adjustment = 0
        if context_analysis:
            # 情绪波动性影响强度
            volatility = context_analysis.get("factors", {}).get("emotional_volatility", 0)
            context_adjustment += volatility * 10
            
            # 考虑前一轮情绪的影响
            previous_emotions = context_analysis.get("previous_emotions", [])
            if previous_emotions and len(previous_emotions) > 0:
                last_emotion = previous_emotions[-1]
                # 情绪强度的惯性
                context_adjustment += (last_emotion + 1) * 10  # 转换到0-20范围
        
        # 情绪特定调整
        emotion_adjustment = 0
        if emotion in ["angry", "surprised"]:
            # 这些情绪通常表现更强烈
            emotion_adjustment += 10
        elif emotion in ["sad", "afraid"]:
            # 这些情绪可能更内敛
            emotion_adjustment += 5
        
        # 计算最终强度
        final_intensity = base_intensity + structure_adjustment + context_adjustment + emotion_adjustment
        
        # 确保在0-100范围内
        return max(0, min(100, final_intensity))
    
    def _generate_emotion_explanation(self, emotion: str, intensity: int, 
                                    sentiment_result: Dict, context_analysis: Dict) -> str:
        """
        生成情绪解释文本
        
        Args:
            emotion: 情绪类型
            intensity: 情绪强度
            sentiment_result: 情感分析结果
            context_analysis: 上下文分析
            
        Returns:
            解释文本
        """
        # 获取情绪中文名称
        emotion_name = self._get_emotion_chinese_name(emotion)
        
        # 强度描述
        if intensity >= 80:
            intensity_desc = "极强的"
        elif intensity >= 60:
            intensity_desc = "强烈的"
        elif intensity >= 40:
            intensity_desc = "中等的"
        elif intensity >= 20:
            intensity_desc = "轻微的"
        else:
            intensity_desc = "微弱的"
        
        # 基础解释
        explanation = f"角色表现出{intensity_desc}{emotion_name}情绪，"
        
        # 根据情绪类型添加具体描述
        if emotion == "happy":
            explanation += "表现出积极乐观的态度。"
        elif emotion == "sad":
            explanation += "流露出失落和悲伤的情绪。"
        elif emotion == "angry":
            explanation += "展现出明显的不满和怒意。"
        elif emotion == "afraid":
            explanation += "流露出担忧和不安的心理状态。"
        elif emotion == "surprised":
            explanation += "表现出意外和震惊的反应。"
        elif emotion == "disgusted":
            explanation += "表达了明显的厌恶和反感。"
        else:  # neutral
            explanation += "情绪比较平和，没有明显波动。"
        
        # 添加上下文分析信息
        if context_analysis:
            trend = context_analysis.get("emotion_trend", "")
            if trend == "improving":
                explanation += " 相比之前，情绪有所好转。"
            elif trend == "deteriorating":
                explanation += " 相比之前，情绪有所恶化。"
            elif trend == "stable" and len(context_analysis.get("previous_emotions", [])) > 0:
                explanation += " 情绪状态相对稳定。"
        
        return explanation
    
    def _get_emotion_chinese_name(self, emotion: str) -> str:
        """获取情绪的中文名称"""
        emotion_names = {
            "angry": "愤怒",
            "sad": "悲伤",
            "afraid": "恐惧",
            "happy": "喜悦", 
            "surprised": "惊讶",
            "disgusted": "厌恶",
            "neutral": "中性"
        }
        return emotion_names.get(emotion, emotion)
    
    def _find_closest_emotion(self, emotion: str) -> str:
        """
        找到最接近的标准情绪类型
        
        Args:
            emotion: 非标准情绪文本
            
        Returns:
            最接近的标准情绪类型
        """
        # 这个方法保持不变
        emotion = emotion.lower()
        
        # 精确匹配
        if emotion in self.primary_emotions:
            return emotion
            
        # 部分匹配
        for primary in self.primary_emotions:
            if primary in emotion or emotion in primary:
                return primary
                
        # 情绪组映射
        emotion_groups = {
            "angry": ["anger", "mad", "furious", "enraged", "irritated", "annoyed", "frustrated"],
            "sad": ["sadness", "depressed", "miserable", "unhappy", "grief", "gloomy", "melancholy"],
            "afraid": ["fear", "scared", "frightened", "terrified", "anxious", "worried", "nervous"],
            "happy": ["happiness", "joy", "delighted", "pleased", "content", "cheerful", "excited"],
            "surprised": ["surprise", "astonished", "amazed", "shocked", "startled", "stunned"],
            "disgusted": ["disgust", "hate", "dislike", "repulsed", "revolted", "appalled"],
            "neutral": ["indifferent", "ambivalent", "detached", "impartial", "balanced", "normal"]
        }
        
        for primary, synonyms in emotion_groups.items():
            if emotion in synonyms:
                return primary
                
        # 默认返回中性
        return "neutral"
    
    def should_stop_dialogue(self) -> Tuple[bool, str]:
        """
        判断是否应该停止对话
        
        Returns:
            (是否停止, 停止原因)的元组
        """
        if not self.emotion_history:
            return False, ""
        
        # 检查最近的情绪记录
        recent_emotions = self.emotion_history[-3:] if len(self.emotion_history) >= 3 else self.emotion_history
        
        # 检查是否达到极端情绪
        latest = self.emotion_history[-1]
        if latest["emotion_intensity"] >= self.emotion_intensity_threshold["positive"]:
            return True, f"角色情绪已达到积极阈值 ({latest['emotion_intensity']} >= {self.emotion_intensity_threshold['positive']})"
        
        if latest["emotion_intensity"] <= self.emotion_intensity_threshold["negative"]:
            return True, f"角色情绪已达到消极阈值 ({latest['emotion_intensity']} <= {self.emotion_intensity_threshold['negative']})"
        
        # 检查连续情绪趋势
        if len(recent_emotions) >= 3:
            # 检查是否连续上升到积极区间
            is_rising = all(recent_emotions[i]["emotion_intensity"] < recent_emotions[i+1]["emotion_intensity"] 
                           for i in range(len(recent_emotions)-1))
            if is_rising and recent_emotions[-1]["emotion_intensity"] > 70:
                return True, "角色情绪连续上升并达到较高水平"
            
            # 检查是否连续下降到消极区间
            is_falling = all(recent_emotions[i]["emotion_intensity"] > recent_emotions[i+1]["emotion_intensity"] 
                            for i in range(len(recent_emotions)-1))
            if is_falling and recent_emotions[-1]["emotion_intensity"] < 30:
                return True, "角色情绪连续下降并达到较低水平"
        
        return False, ""
    
    def get_emotion_trajectory(self) -> List[Dict]:
        """
        获取情绪变化轨迹
        
        Returns:
            情绪历史记录列表
        """
        return self.emotion_history
    
    def get_emotion_summary(self) -> Dict:
        """
        获取情绪分析摘要
        
        Returns:
            情绪摘要字典
        """
        if not self.emotion_history:
            return {
                "avg_intensity": 50,
                "start_intensity": 50,
                "end_intensity": 50,
                "intensity_change": 0,
                "max_intensity": 50,
                "min_intensity": 50,
                "dominant_emotion": "neutral",
                "emotion_counts": {"neutral": 1}
            }
        
        # 计算基本统计数据
        intensities = [e["emotion_intensity"] for e in self.emotion_history]
        emotions = [e["primary_emotion"] for e in self.emotion_history]
        
        # 情绪计数
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # 找出出现最多的情绪
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        
        return {
            "avg_intensity": sum(intensities) / len(intensities),
            "start_intensity": self.emotion_history[0]["emotion_intensity"],
            "end_intensity": self.emotion_history[-1]["emotion_intensity"],
            "intensity_change": self.emotion_history[-1]["emotion_intensity"] - self.emotion_history[0]["emotion_intensity"],
            "max_intensity": max(intensities),
            "min_intensity": min(intensities),
            "dominant_emotion": dominant_emotion,
            "emotion_counts": emotion_counts
        }

    async def async_analyze_emotions(self, content: str) -> Dict:
        """
        异步分析文本情绪
        
        Args:
            content: 待分析的文本
            
        Returns:
            情绪分析结果
        """
        # 使用asyncio.to_thread将同步方法转换为异步执行
        try:
            turn_number = len(self.emotion_history) + 1
            return await asyncio.to_thread(
                self.analyze_emotion,
                content,
                None,
                turn_number
            )
        except Exception as e:
            self.logger.error(f"异步情绪分析失败: {e}")
            default_result = {
                "primary_emotion": "neutral",
                "emotion_intensity": 50,
                "explanation": f"情绪分析失败: {str(e)}，使用默认中性情绪。",
                "error": True,
                "turn": turn_number
            }
            self.emotion_history.append(default_result)
            return default_result

    async def analyze_emotions(self, content: str, sender: str) -> Dict:
        """
        分析对话消息中的情绪（DialogueManager所需的接口方法）
        
        Args:
            content: 消息内容
            sender: 发送者（"character"或"partner"）
            
        Returns:
            情绪分析结果
        """
        # 只分析角色的消息
        if sender != "character":
            return {}
            
        try:
            self.logger.info(f"准备分析情绪: sender={sender}, content_length={len(content)}")
            return await self.async_analyze_emotions(content)
                
        except Exception as e:
            self.logger.error(f"情绪分析失败: {e}, sender={sender}, content_length={len(content) if content else 0}")
            # 返回默认情绪结果防止程序崩溃
            default_result = {
                "primary_emotion": "neutral",
                "emotion_intensity": 50,
                "explanation": "情绪分析失败，使用默认中性情绪。",
                "error": True
            }
            
            # 添加到情绪历史以保持连续性
            self.emotion_history.append(default_result)
            return default_result

    async def evaluate_emotions(self, dialogue_history: List[Dict]) -> Dict:
        """
        评估整个对话中的情绪变化（DialogueManager所需的接口方法）
        
        Args:
            dialogue_history: 对话历史
            
        Returns:
            情绪变化评估结果
        """
        # 如果没有足够的情绪历史记录，返回空结果
        if len(self.emotion_history) < 2:
            return {
                "emotion_trend": "insufficient_data",
                "intensity_change": 0,
                "summary": "对话轮次不足，无法评估情绪变化"
            }
            
        try:
            # 计算情绪变化
            first_emotion = self.emotion_history[0]
            last_emotion = self.emotion_history[-1]
            
            intensity_change = last_emotion["emotion_intensity"] - first_emotion["emotion_intensity"]
            
            # 确定情绪趋势
            if abs(intensity_change) < 10:
                trend = "stable"
                trend_desc = "情绪基本稳定"
            elif intensity_change > 0:
                trend = "improving"
                trend_desc = "情绪明显改善"
            else:
                trend = "deteriorating"
                trend_desc = "情绪明显恶化"
                
            # 计算主要情绪分布
            emotion_counts = {}
            for entry in self.emotion_history:
                emotion = entry["primary_emotion"]
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                
            dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
            
            # 添加对话分析
            character_messages_count = 0
            for msg in dialogue_history:
                speaker_value = msg.get("sender") or msg.get("speaker") or msg.get("role")
                if speaker_value == "character":
                    character_messages_count += 1
            
            return {
                "initial_emotion": first_emotion["primary_emotion"],
                "initial_intensity": first_emotion["emotion_intensity"],
                "final_emotion": last_emotion["primary_emotion"],
                "final_intensity": last_emotion["emotion_intensity"],
                "emotion_trend": trend,
                "intensity_change": intensity_change,
                "dominant_emotion": dominant_emotion,
                "character_messages": character_messages_count,
                "summary": f"对话过程中情绪{trend_desc}，强度变化{intensity_change}点，主要表现为{self._get_emotion_chinese_name(dominant_emotion)}情绪"
            }
        except Exception as e:
            self.logger.error(f"评估情绪变化失败: {e}")
            return {
                "emotion_trend": "error",
                "error": str(e),
                "summary": "评估情绪变化时出错"
            }
    
    async def generate_report(self, dialogue_history: List[Dict]) -> Dict:
        """
        生成情绪分析报告
        
        Args:
            dialogue_history: 对话历史
            
        Returns:
            情绪分析报告
        """
        # 如果情绪历史不足，返回简单评估
        if len(self.emotion_history) < 2:
            return await self.evaluate_emotions(dialogue_history)
        
        try:
            # 情绪轨迹
            emotion_trajectory = []
            for i, emotion in enumerate(self.emotion_history):
                emotion_trajectory.append({
                    "turn": emotion.get("turn", i+1),
                    "emotion": emotion["primary_emotion"],
                    "intensity": emotion["emotion_intensity"],
                    "explanation": emotion.get("explanation", "")
                })
            
            # 情绪变化
            evaluation = await self.evaluate_emotions(dialogue_history)
            
            # 情绪分析摘要
            summary = {
                "overall_trend": evaluation["emotion_trend"],
                "starting_state": f"{self._get_emotion_chinese_name(evaluation['initial_emotion'])} (强度: {evaluation['initial_intensity']})",
                "ending_state": f"{self._get_emotion_chinese_name(evaluation['final_emotion'])} (强度: {evaluation['final_intensity']})",
                "emotional_journey": evaluation["summary"],
                "key_emotions": [self._get_emotion_chinese_name(k) for k, v in sorted(evaluation.get("emotion_counts", {}).items(), key=lambda x: x[1], reverse=True)][:3]
            }
            
            return {
                "summary": summary,
                "evaluation": evaluation,
                "trajectory": emotion_trajectory,
            }
            
        except Exception as e:
            self.logger.error(f"生成情绪报告失败: {e}")
            return {
                "error": str(e),
                "summary": {"overall_trend": "error", "error_message": f"生成报告时出错: {str(e)}"}
            }


# 简单测试用例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 加载测试场景
        base_dir = Path(__file__).resolve().parent.parent.parent
        scenario_path = base_dir / "data" / "scenarios" / "templates" / "scenario_005.json"
        with open(scenario_path, 'r', encoding='utf-8') as f:
            scenario = json.load(f)
        
        # 加载角色信息
        character_path = base_dir / "data" / "characters" / "templates" / "char_001.json"
        with open(character_path, 'r', encoding='utf-8') as f:
            character = json.load(f)
        
        # 创建情绪监测Agent
        agent = EmotionAgent()
        
        # 设置场景和角色
        agent.set_scenario(scenario)
        agent.set_character_info(character)
        
        # 分析初始对话
        initial_message = scenario["initial_dialogue"]
        print(f"角色消息: {initial_message}")
        
        result = agent.analyze_emotion(initial_message, turn_number=1)
        print(f"情绪分析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 分析第二条消息
        second_message = "你总是这样，每次都说工作忙，我感觉自己一点都不重要。"
        print(f"\n角色消息: {second_message}")
        
        # 模拟对话历史
        dialogue_history = [
            {"role": "character", "content": initial_message},
            {"role": "partner", "content": "我刚刚开完会，手机调成静音了，没看到你的消息，抱歉让你担心了。"},
            {"role": "character", "content": second_message}
        ]
        
        result = agent.analyze_emotion(second_message, dialogue_history, turn_number=2)
        print(f"情绪分析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 检查是否应该停止对话
        should_stop, reason = agent.should_stop_dialogue()
        print(f"\n是否应停止对话: {should_stop}")
        if should_stop:
            print(f"停止原因: {reason}")
        
        # 打印情绪轨迹摘要
        summary = agent.get_emotion_summary()
        print(f"\n情绪摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        logging.error(f"测试失败: {e}") 