"""
LLM模型API客户端，用于调用DeepSeek和OpenRouter的API
"""

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional, Union, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置常量
DEEPSEEK_API_BASE = "https://api.deepseek.com"
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
<<<<<<< Updated upstream
=======

import os

os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'
>>>>>>> Stashed changes

# 可用模型配置
MODELS = {
    "deepseek": {
        "default": "deepseek-chat",
        "available": ["deepseek-chat", "deepseek-coder"]
    },
    "openrouter": {
        "default": "openai/gpt-3.5-turbo-0125:free",
        "available": [
            "openai/gpt-3.5-turbo-0125:free",
            "openai/gpt-4-turbo-preview:free",
            "openai/gpt-4.1",
            "openai/gpt-4",
            "anthropic/claude-3-opus:free",
            "anthropic/claude-3-sonnet:free",
            "anthropic/claude-3-haiku:free",
            "anthropic/claude-instant-1.2:free",
            "google/gemini-pro:free",
            "google/gemini-1.5-pro:free",
            "meta-llama/llama-3-70b-instruct:free",
            "meta-llama/llama-3-8b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "mistralai/mistral-large:free",
            "01-ai/yi-34b:free",
            "cohere/command-r:free",
            "cohere/command-r-plus:free"
        ]
    }
}

def create_session_with_retries(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    """创建带有重试机制的会话"""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

class LLMClient:
    """大模型API客户端类"""
    
    def __init__(self, api_type: str = "deepseek", model_name: Optional[str] = None):
        """
        初始化LLM客户端
        
        参数:
            api_type (str): API类型，支持 "deepseek" 或 "openrouter"
            model_name (str, optional): 指定使用的模型名称，如果不指定则使用默认模型
        """
        self.api_type = api_type
        
        # 加载API密钥
        self.api_keys = self._load_api_keys()
        
        # 选择API基础URL
        if api_type == "deepseek":
            self.api_base = DEEPSEEK_API_BASE
            self.default_model = model_name or MODELS["deepseek"]["default"]
        elif api_type == "openrouter":
            self.api_base = OPENROUTER_API_BASE
            self.default_model = model_name or MODELS["openrouter"]["default"]
        else:
            raise ValueError(f"不支持的API类型: {api_type}，支持的类型有: deepseek, openrouter")
            
    def _load_api_keys(self) -> Dict[str, str]:
        """
        从环境变量或配置文件加载API密钥
        
        返回:
            Dict[str, str]: 包含不同服务的API密钥
        """
        keys = {}
        
        # 尝试从环境变量读取
        keys["deepseek"] = os.environ.get("DEEPSEEK_API_KEY", "")
        keys["openrouter"] = os.environ.get("OPENROUTER_API_KEY", "")
        
        # 如果环境变量中没有，尝试从配置文件读取
        if not keys["deepseek"] or not keys["openrouter"]:
            # 尝试多个可能的配置文件路径
            possible_paths = [
                "config.json",  # 当前工作目录
                "LQBench/config.json",  # LQBench目录下的config.json
                os.path.join("LQBench", "config.json"),  # 同上，使用os.path.join
                os.path.join(os.path.dirname(__file__), "../../config.json"),  # 相对于本文件的项目根目录
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../config.json"),  # 绝对路径
                os.path.abspath("config.json"),  # 绝对路径的当前工作目录
                os.path.abspath("LQBench/config.json"),  # 绝对路径的LQBench目录
            ]
            
            for config_path in possible_paths:
                try:
                    with open(config_path, "r") as f:
                        config = json.load(f)
                        keys["deepseek"] = config.get("DEEPSEEK_API_KEY", "")
                        keys["openrouter"] = config.get("OPENROUTER_API_KEY", "")
                        
                        if keys["deepseek"] or keys["openrouter"]:
                            break
                except FileNotFoundError:
                    continue
                except json.JSONDecodeError as e:
                    print(f"配置文件格式错误: {config_path}, 错误: {str(e)}")
                    continue
                except Exception as e:
                    print(f"读取配置文件时出现未知错误: {config_path}, 错误: {str(e)}")
                    continue
        
        # 硬编码API密钥作为最后的备选方案（仅在调试环境中使用）
        if not keys["deepseek"] and not keys["openrouter"]:
            print("警告：未能从任何来源找到API密钥，尝试使用hardcoded备选方案")
            # 从LQBench/config.json中直接获取密钥
            try:
                hardcoded_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.json")
                with open(hardcoded_path, "r") as f:
                    config = json.load(f)
                    keys["deepseek"] = config.get("DEEPSEEK_API_KEY", "")
                    keys["openrouter"] = config.get("OPENROUTER_API_KEY", "")
            except Exception as e:
                print(f"硬编码路径读取失败: {str(e)}")
            
        return keys
    
    def call(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        调用LLM API
        
        参数:
            prompt (str): 用户提示词
            model (str, optional): 模型名称，如不指定则使用默认模型
            temperature (float): 温度参数，控制生成多样性
            max_tokens (int): 最大生成令牌数
            system_prompt (str, optional): 系统提示词
            messages (List[Dict[str, str]], optional): 历史消息列表
            
        返回:
            Tuple[str, Dict[str, Any]]: (生成的回复文本, 完整的响应信息)
        """
        if self.api_type == "deepseek":
            return self._call_deepseek(prompt, model, temperature, max_tokens, system_prompt, messages)
        elif self.api_type == "openrouter":
            return self._call_openrouter(prompt, model, temperature, max_tokens, system_prompt, messages)
        else:
            raise ValueError(f"不支持的API类型: {self.api_type}")
    
    def _call_deepseek(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """调用DeepSeek API"""
        if not self.api_keys["deepseek"]:
            raise ValueError("未找到DeepSeek API密钥")
            
        # 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_keys['deepseek']}"
        }
        
        # 准备消息体
        if not messages:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
        
        # 准备请求体
        data = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 发送请求
        try:
            session = create_session_with_retries()
            response = session.post(
                f"{self.api_base}/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60  # 设置60秒超时
            )
            response.raise_for_status()
            result = response.json()
            
            # 提取生成的内容
            content = result["choices"][0]["message"]["content"]
            return content, result
        except Exception as e:
            print(f"调用DeepSeek API出错: {str(e)}")
            fallback_info = {"error": str(e), "fallback": True}
            return f"API调用失败: {str(e)}", fallback_info
    
    def _call_openrouter(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """调用OpenRouter API"""
        if not self.api_keys["openrouter"]:
            raise ValueError("未找到OpenRouter API密钥")
            
        # 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_keys['openrouter']}",
            "HTTP-Referer": "https://lqbench.example.com",  # 必须提供一个引用网址
            "X-Title": "LQBench",  # 应用程序标题
        }
        
        # 准备消息体
        if not messages:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
        
        # 准备请求体
        data = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        # 发送请求
        try:
            print(f"正在调用OpenRouter API，使用模型: {model or self.default_model}")
            
            # 使用普通的requests而不是带重试的会话，以避免可能的问题
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=30  # 减少超时时间以避免长时间挂起
            )
            
            # 检查响应状态码
            if response.status_code != 200:
                print(f"OpenRouter API返回错误状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                raise ValueError(f"OpenRouter API返回错误状态码: {response.status_code}")
                
            result = response.json()
            
            # 提取生成的内容
            content = result["choices"][0]["message"]["content"]
            print(f"模型 {model or self.default_model} 响应成功")
            return content, result
        except requests.exceptions.RequestException as e:
            print(f"OpenRouter API请求异常: {str(e)}")
            # 尝试回退到DeepSeek
            print("回退到DeepSeek API...")
            return self._fallback_to_deepseek(prompt, temperature, max_tokens, system_prompt, messages)
        except Exception as e:
            print(f"调用OpenRouter API时出现其他错误: {str(e)}")
            # 尝试回退到DeepSeek
            return self._fallback_to_deepseek(prompt, temperature, max_tokens, system_prompt, messages)
    
    def _fallback_to_deepseek(
        self, 
        prompt: str, 
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str],
        messages: Optional[List[Dict[str, str]]]
    ) -> Tuple[str, Dict[str, Any]]:
        """回退到DeepSeek API"""
        try:
            print("尝试回退到DeepSeek API...")
            # 临时保存当前API类型
            original_api_type = self.api_type
            original_default_model = self.default_model
            
            # 切换到DeepSeek
            self.api_type = "deepseek"
            self.api_base = DEEPSEEK_API_BASE
            self.default_model = MODELS["deepseek"]["default"]
            
            result = self._call_deepseek(prompt, None, temperature, max_tokens, system_prompt, messages)
            
            # 恢复原始API类型
            self.api_type = original_api_type
            self.api_base = OPENROUTER_API_BASE if original_api_type == "openrouter" else DEEPSEEK_API_BASE
            self.default_model = original_default_model
            
            return result
        except Exception as fallback_error:
            print(f"回退到DeepSeek API也失败: {str(fallback_error)}")
            fallback_info = {"error": "API调用失败，回退也失败", "fallback": False}
            return f"API调用失败，回退也失败", fallback_info
    
    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Tuple[str, Dict[str, Any]]:
        """
        创建聊天完成（更符合OpenAI API格式的接口）
        
        参数:
            messages (List[Dict[str, str]]): 消息列表
            model (str, optional): 模型名称
            temperature (float): 温度参数
            max_tokens (int): 最大生成令牌数
            
        返回:
            Tuple[str, Dict[str, Any]]: (生成的回复文本, 完整的响应信息)
        """
        # 提取用户最后一条消息作为prompt
        user_messages = [m for m in messages if m["role"] == "user"]
        if user_messages:
            prompt = user_messages[-1]["content"]
        else:
            prompt = ""
            
        # 提取系统消息作为system_prompt
        system_messages = [m for m in messages if m["role"] == "system"]
        system_prompt = system_messages[0]["content"] if system_messages else None
        
        return self.call(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            messages=messages
        ) 