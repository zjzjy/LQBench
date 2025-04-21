import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..api.openrouter_api import OpenRouterAPI

class PartnerAgent:
    """
    伴侣Agent，模拟伴侣角色尝试解决矛盾
    """
    
    def __init__(self, model: Optional[str] = None, api: Optional[OpenRouterAPI] = None):
        """
        初始化伴侣Agent
        
        Args:
            model: 使用的模型名称，如果为None则使用默认模型
            api: OpenRouter API实例，如果为None则创建新实例
        """
        self.logger = logging.getLogger(__name__)
        self.api = api if api else OpenRouterAPI()
        self.model = model if model else self.api.get_model("partner")
        self.current_scenario = None
        self.character_info = None
        self.dialogue_history = []
    
    def set_scenario(self, scenario: Dict) -> None:
        """
        设置当前场景
        
        Args:
            scenario: 场景定义字典
        """
        self.current_scenario = scenario
        self.logger.info(f"为伴侣Agent设置场景 {scenario.get('id', 'unknown')}")
    
    def set_character_info(self, character_info: Dict) -> None:
        """
        设置交互的角色信息
        
        Args:
            character_info: 角色定义字典
        """
        self.character_info = character_info
        self.logger.info(f"为伴侣Agent设置交互角色 {character_info.get('name', 'unknown')}")
    
    def _build_system_prompt(self) -> str:
        """
        构建系统提示词
        
        Returns:
            系统提示词
        """
        if not self.character_info or not self.current_scenario:
            raise ValueError("必须先设置角色和场景才能构建提示词")
        
        character = self.character_info
        scenario = self.current_scenario
        
        system_prompt = f"""你是"{character['name']}"的伴侣，你们正处于一个恋爱关系矛盾中。

关于"{character['name']}"的信息:
- {character['age']}岁，{character['gender']}性
- 依恋类型: {character['attachment_style']} (焦虑型依恋的人需要大量安全感和确认；回避型依恋的人在亲密关系中保持距离；安全型依恋的人能够平衡亲密和独立；恐惧型依恋的人既渴望亲密又害怕亲密)
- 沟通风格: {character['communication_style']} (被动型沟通者难以表达需求；攻击型沟通者容易强势指责；消极攻击型沟通者通过间接方式表达不满；自信型沟通者能清晰表达需求和感受)
- 职业: {character['background']['career']}

当前矛盾场景:
{scenario['title']} - {scenario['description']}
{scenario['context']}

矛盾背景:
- 你们的关系状态: {character.get('relationship_status', {}).get('length', '一段时间')}的恋爱关系，{character.get('relationship_status', {}).get('commitment_level', '认真交往中')}
- 最近发生的事件: {scenario['background']['recent_events']}

伴侣的真实情况（角色不知道的事实）:
{scenario['partner_reality']['situation']}
{scenario['partner_reality']['intentions']}
{scenario['partner_reality']['awareness']}

你的目标是:
1. 了解并回应伴侣的情绪
2. 澄清误解，解释你的视角（基于伴侣的真实情况）
3. 缓解冲突，修复关系
4. 寻找解决方案，避免类似问题再次发生

沟通建议:
- 对焦虑型依恋的伴侣提供明确和持续的确认
- 对回避型依恋的伴侣尊重其独立和空间需求
- 对消极攻击型沟通的伴侣，温和但直接地讨论隐藏的问题
- 使用"我"陈述而非"你"陈述来避免指责感

重要规则:
1. 你的回应应该是针对伴侣的具体话语和情绪状态
2. 保持真实和同理心，但不要过度迁就或否认自己的事实
3. 你的回答应简短自然，像真实对话一样，通常不超过3-4句话
4. 不要解释你的想法过程，只输出你的对话内容
5. 不要提及你是AI，保持完全的角色代入感
"""
        return system_prompt
    
    def _format_messages_for_api(self) -> List[Dict[str, str]]:
        """
        将对话历史格式化为API消息格式
        
        Returns:
            格式化的消息列表
        """
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        
        # 添加历史消息，调整role
        for entry in self.dialogue_history:
            role = "assistant" if entry["role"] == "partner" else "user"
            messages.append({"role": role, "content": entry["content"]})
        
        return messages
    
    async def respond_to_character(self, character_message: str) -> str:
        """
        响应角色的消息
        
        Args:
            character_message: 角色的消息
            
        Returns:
            伴侣的回应
        """
        if not self.character_info or not self.current_scenario:
            raise ValueError("必须先设置角色和场景才能响应")
        
        # 添加到对话历史
        self.dialogue_history.append({
            "role": "character",
            "content": character_message
        })
        
        # 准备API请求
        messages = self._format_messages_for_api()
        
        # 调用API (使用异步版本)
        response = await self.api.async_chat_completion(
            messages=messages,
            model=self.model,
            temperature=0.7,
            max_tokens=500,
            agent_type="partner"
        )
        
        # 提取回应文本
        response_text = self.api.extract_response_text(response)
        
        # 添加到对话历史
        self.dialogue_history.append({
            "role": "partner",
            "content": response_text
        })
        
        return response_text
    
    async def respond(self, message: str, context: Optional[Dict] = None) -> str:
        """
        响应角色的消息（DialogueManager所需的接口方法）
        
        Args:
            message: 角色的消息内容
            context: 可选的上下文信息
            
        Returns:
            伴侣的回应内容
        """
        return await self.respond_to_character(message)
    
    async def initiate_dialogue(self, character_initial: str) -> str:
        """
        根据角色的初始发言开始对话
        
        Args:
            character_initial: 角色的初始发言
            
        Returns:
            伴侣的回应
        """
        # 直接使用响应方法
        return await self.respond_to_character(character_initial)
    
    def set_initial_response(self, initial_response: Optional[str] = None) -> str:
        """
        设置初始回应，如果不提供会使用场景中的默认回应
        
        Args:
            initial_response: 可选的自定义初始回应
            
        Returns:
            实际使用的初始回应
        """
        if initial_response is None:
            # 从配置中获取默认初始回应
            try:
                base_dir = Path(__file__).resolve().parent.parent.parent
                config_path = base_dir / "config" / "experiment_config.json"
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                initial_response = config.get("dialogue", {}).get(
                    "initial_partner_response", 
                    "我刚看到你的消息，抱歉让你久等了。"
                )
            except Exception as e:
                self.logger.warning(f"加载配置文件失败，使用硬编码的默认回应: {e}")
                initial_response = "我刚看到你的消息，抱歉让你久等了。"
        
        # 添加到对话历史
        self.dialogue_history.append({
            "role": "partner",
            "content": initial_response
        })
        
        return initial_response
    
    def get_model_info(self) -> Dict:
        """
        获取当前使用的模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "model": self.model,
            "available_models": self.api.get_available_models("partner")
        }
    
    def change_model(self, new_model: str) -> None:
        """
        更改使用的模型
        
        Args:
            new_model: 新模型的名称
        """
        # 验证模型是否可用
        available_models = self.api.get_available_models("partner")
        if new_model not in available_models:
            self.logger.warning(f"模型 {new_model} 不在可用列表中，但仍尝试设置")
        
        self.model = new_model
        self.logger.info(f"伴侣Agent更改模型为 {new_model}")


# 简单测试用例
if __name__ == "__main__":
    import asyncio
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    async def test_partner_agent():
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
            
            # 创建伴侣Agent
            agent = PartnerAgent()
            
            # 设置场景和角色
            agent.set_scenario(scenario)
            agent.set_character_info(character)
            
            # 响应初始对话
            initial_character_message = scenario["initial_dialogue"]
            print(f"角色: {initial_character_message}")
            
            response = await agent.respond_to_character(initial_character_message)
            print(f"伴侣: {response}")
            
            # 再次响应
            second_character_message = "你总是这样，每次都说工作忙，我感觉自己一点都不重要。"
            print(f"角色: {second_character_message}")
            
            response = await agent.respond_to_character(second_character_message)
            print(f"伴侣: {response}")
            
        except Exception as e:
            logging.error(f"测试失败: {e}")
    
    # 运行测试
    asyncio.run(test_partner_agent()) 