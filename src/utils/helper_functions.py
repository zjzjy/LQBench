import datetime
import os
import re
import uuid
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)

def get_timestamp(format_str: str = "%Y%m%d%H%M%S") -> str:
    """
    获取当前时间戳字符串
    
    Args:
        format_str: 时间格式字符串，默认为"%Y%m%d%H%M%S"
        
    Returns:
        格式化的时间戳字符串
    """
    return datetime.datetime.now().strftime(format_str)

def get_uuid() -> str:
    """
    生成UUID字符串（去除连字符）
    
    Returns:
        UUID字符串
    """
    return str(uuid.uuid4()).replace('-', '')

def get_short_uuid(length: int = 8) -> str:
    """
    生成短UUID字符串
    
    Args:
        length: UUID长度，默认为8
        
    Returns:
        短UUID字符串
    """
    return get_uuid()[:length]

def ensure_dir_exists(dir_path: Union[str, Path]) -> Path:
    """
    确保目录存在，不存在则创建
    
    Args:
        dir_path: 目录路径
        
    Returns:
        Path对象
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def clean_text(text: str) -> str:
    """
    清理文本，移除多余空白字符等
    
    Args:
        text: 输入文本
        
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 替换多个空白字符为单个空格
    text = re.sub(r'\s+', ' ', text)
    # 移除开头和结尾的空白
    text = text.strip()
    return text

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 输入文本
        max_length: 最大长度
        suffix: 截断后添加的后缀
        
    Returns:
        截断后的文本
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def extract_json_from_text(text: str) -> Optional[Dict]:
    """
    从文本中提取JSON数据
    
    Args:
        text: 输入文本
        
    Returns:
        提取的JSON数据，失败则返回None
    """
    try:
        # 尝试直接解析整个文本
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试查找文本中的JSON部分
        json_pattern = r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```|\{[\s\S]*\}'
        matches = re.findall(json_pattern, text)
        
        for match in matches:
            match_text = match[0] if match[0] else match[1] if len(match) > 1 else match
            match_text = match_text.strip()
            
            if not match_text:
                continue
            
            # 如果匹配文本不是以{开始，尝试找到第一个{
            if not match_text.startswith('{'):
                start_idx = match_text.find('{')
                if start_idx >= 0:
                    match_text = match_text[start_idx:]
            
            try:
                return json.loads(match_text)
            except json.JSONDecodeError:
                continue
        
        logger.warning("无法从文本中提取有效的JSON数据")
        return None

def merge_dicts(dict1: Dict, dict2: Dict, overwrite: bool = True) -> Dict:
    """
    合并两个字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        overwrite: 是否覆盖第一个字典中已存在的键
        
    Returns:
        合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # 递归合并嵌套字典
            result[key] = merge_dicts(result[key], value, overwrite)
        elif key not in result or overwrite:
            # 添加新键或覆盖现有键
            result[key] = value
    
    return result

def safe_get_nested(data: Dict, keys: List[str], default: Any = None) -> Any:
    """
    安全地从嵌套字典中获取值
    
    Args:
        data: 嵌套字典
        keys: 键路径列表
        default: 默认值
        
    Returns:
        获取的值，如不存在则返回默认值
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的简单相似度（使用Jaccard相似度）
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
        
    Returns:
        相似度分数（0-1）
    """
    if not text1 or not text2:
        return 0.0
    
    # 将文本分割为词集合
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    
    # 计算Jaccard相似度：交集大小/并集大小
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0.0
    
    return intersection / union

def format_emotion_score(score: float) -> str:
    """
    格式化情绪分数，转换为易读形式
    
    Args:
        score: 情绪分数（通常为-1到1之间）
        
    Returns:
        格式化后的情绪描述
    """
    if score > 0.7:
        return "非常积极"
    elif score > 0.3:
        return "积极"
    elif score > -0.3:
        return "中性"
    elif score > -0.7:
        return "消极"
    else:
        return "非常消极"

def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    从文本中提取关键词（简单实现，仅基于词频）
    
    Args:
        text: 输入文本
        max_keywords: 最大关键词数量
        
    Returns:
        关键词列表
    """
    if not text:
        return []
    
    # 将文本分割为单词
    words = re.findall(r'\w+', text.lower())
    
    # 过滤掉常见停用词
    stop_words = {'的', '了', '和', '是', '在', '有', '我', '你', '他', '她', '它', '这', '那', '都', '也', '就'}
    filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
    
    # 计算词频
    word_freq = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # 按频率排序并返回前N个
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, _ in sorted_words[:max_keywords]]
    
    return keywords

def parse_time_str(time_str: str) -> Optional[datetime.datetime]:
    """
    解析时间字符串为datetime对象
    
    Args:
        time_str: 时间字符串
        
    Returns:
        datetime对象，解析失败则返回None
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"无法解析时间字符串: {time_str}")
    return None

def safe_file_name(name: str) -> str:
    """
    将字符串转换为安全的文件名
    
    Args:
        name: 输入字符串
        
    Returns:
        安全的文件名
    """
    # 移除不合法字符
    safe_name = re.sub(r'[\\/*?:"<>|]', '', name)
    # 替换空格
    safe_name = safe_name.replace(' ', '_')
    # 确保不超过255个字符
    if len(safe_name) > 255:
        safe_name = safe_name[:255]
    return safe_name


# 简单测试用例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试时间戳函数
    timestamp = get_timestamp()
    print(f"当前时间戳: {timestamp}")
    
    # 测试UUID生成
    uuid_str = get_uuid()
    short_uuid = get_short_uuid()
    print(f"UUID: {uuid_str}")
    print(f"短UUID: {short_uuid}")
    
    # 测试文本处理函数
    text = "  这是一段   测试文本，用于演示  辅助函数的功能。  "
    cleaned_text = clean_text(text)
    truncated_text = truncate_text(cleaned_text, 10)
    print(f"清理后文本: {cleaned_text}")
    print(f"截断后文本: {truncated_text}")
    
    # 测试JSON提取
    json_text = '{"name": "张三", "age": 30}'
    extracted_json = extract_json_from_text(json_text)
    print(f"提取的JSON: {extracted_json}")
    
    # 测试嵌套字典访问
    nested_dict = {"user": {"profile": {"name": "李四", "age": 25}}}
    name = safe_get_nested(nested_dict, ["user", "profile", "name"])
    invalid_value = safe_get_nested(nested_dict, ["user", "settings", "theme"], "默认")
    print(f"嵌套值访问: {name}")
    print(f"无效路径访问: {invalid_value}")
    
    # 测试相似度计算
    text1 = "我喜欢吃苹果和香蕉"
    text2 = "我喜欢吃香蕉和橙子"
    similarity = calculate_similarity(text1, text2)
    print(f"文本相似度: {similarity:.2f}") 