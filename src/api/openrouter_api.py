import os
import json
import time
import aiohttp
import asyncio
import requests
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
import re

# 导入辅助函数
from src.utils.helper_functions import extract_json_from_text

class OpenRouterAPI:
    """OpenRouter API封装类，用于调用不同的大型语言模型"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化OpenRouter API客户端
        
        Args:
            config_path: API配置文件路径，默认为None，会从默认位置加载
        """
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.api_key = self.config["openrouter"]["api_key"]
        self.base_url = self.config["openrouter"]["base_url"]
        self.timeout = self.config["openrouter"]["timeout"]
        self.retry_attempts = self.config["openrouter"]["retry_attempts"]
        self.retry_delay = self.config["openrouter"]["retry_delay"]
        
        # 从环境变量加载API密钥（如果有）
        if os.environ.get("OPENROUTER_API_KEY"):
            self.api_key = os.environ.get("OPENROUTER_API_KEY")
        
        if self.api_key == "YOUR_OPENROUTER_API_KEY":
            self.logger.warning("使用默认API密钥。请在config/api_config.json中设置您的OpenRouter API密钥，或通过环境变量OPENROUTER_API_KEY设置。")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """
        加载API配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if config_path is None:
            # 获取当前文件所在目录的上两级目录，然后拼接config路径
            base_dir = Path(__file__).resolve().parent.parent.parent
            config_path = base_dir / "config" / "api_config.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            # 返回默认配置
            return {
                "openrouter": {
                    "api_key": "YOUR_OPENROUTER_API_KEY",
                    "base_url": "https://openrouter.ai/api/v1",
                    "timeout": 60,
                    "retry_attempts": 3,
                    "retry_delay": 2
                },
                "models": {
                    "character": {"default": "anthropic/claude-3-5-sonnet"},
                    "partner": {"default": "anthropic/claude-3-5-sonnet"},
                    "emotion": {"default": "anthropic/claude-3-haiku"},
                    "memory": {"default": "anthropic/claude-3-haiku"},
                    "expert": {"default": "anthropic/claude-3-5-sonnet"}
                }
            }
    
    def get_model(self, agent_type: str) -> str:
        """
        获取指定Agent类型的默认模型
        
        Args:
            agent_type: Agent类型，如"character"、"partner"等
            
        Returns:
            模型标识符
        """
        try:
            return self.config["models"][agent_type]["default"]
        except KeyError:
            self.logger.warning(f"未找到Agent类型 '{agent_type}' 的默认模型，使用通用默认模型")
            return "anthropic/claude-3-5-sonnet"
    
    def get_available_models(self, agent_type: str) -> List[str]:
        """
        获取指定Agent类型可用的所有模型
        
        Args:
            agent_type: Agent类型
            
        Returns:
            模型列表
        """
        try:
            default = self.config["models"][agent_type]["default"]
            alternatives = self.config["models"][agent_type].get("alternatives", [])
            return [default] + alternatives
        except KeyError:
            self.logger.warning(f"未找到Agent类型 '{agent_type}' 的模型列表")
            return ["anthropic/claude-3-5-sonnet"]
    
    def _build_headers(self) -> Dict[str, str]:
        """
        构建API请求头
        
        Returns:
            请求头字典
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://love.nlp.research.project", # 用于OpenRouter识别项目
            "X-Title": "LOVE Emotional Intelligence Benchmark"  # 项目标题
        }
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 1000,
                       agent_type: str = "character") -> Dict:
        """
        同步调用聊天完成API
        
        Args:
            messages: 消息列表
            model: 模型名称，如果为None则使用指定agent_type的默认模型
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            agent_type: Agent类型，用于选择默认模型
            
        Returns:
            API响应
        """
        if model is None:
            model = self.get_model(agent_type)
        
        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers()
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 重试机制
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"API调用失败 (尝试 {attempt+1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"API调用最终失败: {e}")
                    raise
    
    async def async_chat_completion(self,
                                  messages: List[Dict[str, str]],
                                  model: Optional[str] = None,
                                  temperature: float = 0.7,
                                  max_tokens: int = 1000,
                                  agent_type: str = "character") -> Dict:
        """
        异步调用聊天完成API
        
        Args:
            messages: 消息列表
            model: 模型名称，如果为None则使用指定agent_type的默认模型
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            agent_type: Agent类型，用于选择默认模型
            
        Returns:
            API响应
        """
        if model is None:
            model = self.get_model(agent_type)
        
        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers()
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 异步重试机制
        for attempt in range(self.retry_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=self.timeout
                    ) as response:
                        if response.status >= 400:
                            error_text = await response.text()
                            raise aiohttp.ClientResponseError(
                                response.request_info,
                                response.history,
                                status=response.status,
                                message=error_text
                            )
                        return await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.warning(f"异步API调用失败 (尝试 {attempt+1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error(f"异步API调用最终失败: {e}")
                    raise
    
    def extract_response_text(self, response: Dict) -> str:
        """
        从API响应中提取文本内容
        
        Args:
            response: API响应字典
            
        Returns:
            生成的文本内容
        """
        try:
            # 检查响应是否为None或空
            if not response:
                self.logger.error("API返回空响应")
                return ""
                
            # 记录完整响应以便调试
            self.logger.debug(f"API完整响应: {json.dumps(response, ensure_ascii=False)}")
            
            # 检查响应是否包含错误信息
            if "error" in response:
                error_msg = response.get("error", {}).get("message", "未知错误")
                self.logger.error(f"API返回错误: {error_msg}")
                return ""
                
            # 正常情况下提取文本内容
            if "choices" in response and response["choices"]:
                if "message" in response["choices"][0]:
                    content = response["choices"][0]["message"].get("content")
                    if content is None:
                        self.logger.warning("API响应的content字段为None")
                        return ""
                    return content
                else:
                    self.logger.error("API响应中没有message字段")
            else:
                self.logger.error("API响应中没有choices字段或choices为空")
                
            return ""
        except (KeyError, IndexError, TypeError) as e:
            self.logger.error(f"提取文本内容时出错: {type(e).__name__}: {e}")
            self.logger.debug(f"响应内容: {response}")
            return ""
    
    def extract_json_from_response(self, response: Dict) -> Tuple[bool, Dict[str, Any], str]:
        """
        从API响应中提取JSON数据
        
        Args:
            response: API响应字典
            
        Returns:
            元组: (是否成功提取, 提取的JSON数据, 错误信息)
        """
        # 首先提取文本内容
        response_text = self.extract_response_text(response)
        
        if not response_text:
            return False, {}, "无法从API响应中提取文本内容"
        
        # 使用helper_functions中的extract_json_from_text函数提取JSON
        json_data = extract_json_from_text(response_text)
        
        if json_data is not None:
            return True, json_data, ""
        
        # 如果extract_json_from_text失败，尝试自己实现一个简单的提取
        try:
            # 尝试直接解析
            data = json.loads(response_text)
            return True, data, ""
        except json.JSONDecodeError:
            # 尝试找到JSON块
            json_start = response_text.find("```json")
            if json_start != -1:
                json_end = response_text.find("```", json_start + 7)
                if json_end != -1:
                    json_text = response_text[json_start + 7:json_end].strip()
                    try:
                        data = json.loads(json_text)
                        return True, data, ""
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"JSON块解析失败: {e}")
                        return False, {}, f"JSON块解析失败: {str(e)}"
            
            # 最后尝试用正则表达式寻找可能的JSON
            pattern = r'(\{[\s\S]*\})'
            matches = re.findall(pattern, response_text)
            
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, dict) and len(data) > 0:
                        return True, data, ""
                except:
                    continue
            
            self.logger.warning(f"无法从响应中提取JSON: {response_text[:100]}...")
            return False, {}, "无法从响应中提取有效的JSON数据"
    
    def get_usage_info(self, response: Dict) -> Dict:
        """
        从API响应中提取使用信息
        
        Args:
            response: API响应字典
            
        Returns:
            使用信息字典
        """
        try:
            return response.get("usage", {})
        except Exception as e:
            self.logger.error(f"无法获取使用信息: {e}")
            return {}


# 简单测试用例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建API客户端
    api = OpenRouterAPI()
    
    # 测试消息
    messages = [
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "你好，今天天气怎么样？"}
    ]
    
    # 同步调用测试
    response = api.chat_completion(messages)
    print("同步调用结果:")
    print(api.extract_response_text(response))
    
    # 异步调用测试
    async def test_async():
        response = await api.async_chat_completion(messages)
        print("\n异步调用结果:")
        print(api.extract_response_text(response))
    
    # 运行异步测试
    asyncio.run(test_async()) 