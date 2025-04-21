import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import asyncio

from ..api.openrouter_api import OpenRouterAPI

class CharacterAgent:
    """
    角色扮演Agent，基于角色定义扮演虚拟人物
    """
    
    def __init__(self, character_id: str, api: Optional[OpenRouterAPI] = None):
        """
        初始化角色扮演Agent
        
        Args:
            character_id: 角色ID
            api: OpenRouter API实例，如果为None则创建新实例
        """
        self.logger = logging.getLogger(__name__)
        self.character_id = character_id
        self.api = api if api else OpenRouterAPI()
        self.character = None
        self.current_scenario = None
        self.dialogue_history = []
        self.emotional_state = {
            "current_emotion": "neutral",
            "emotion_intensity": 50,  # 0-100，50为中性
            "emotion_trajectory": []
        }
        
        # 只有在character为None时尝试加载
        try:
            self._load_character(character_id)
        except Exception as e:
            self.logger.warning(f"自动加载角色失败: {e}，需要手动设置角色数据")
            
    def _load_character(self, character_id: str) -> None:
        """
        加载角色信息
        
        Args:
            character_id: 角色ID
        """
        # 如果已经设置了角色数据，则不再加载
        if self.character is not None:
            return
            
        try:
            # 获取项目根目录
            base_dir = Path(__file__).resolve().parent.parent.parent
            
            # 尝试从templates目录加载
            character_path = base_dir / "data" / "characters" / "templates" / f"{character_id}.json"
            if not character_path.exists():
                # 尝试从主目录加载
                character_path = base_dir / "data" / "characters" / f"{character_id}.json"
                if not character_path.exists():
                    self.logger.error(f"找不到角色文件: {character_id}")
                    raise FileNotFoundError(f"找不到角色文件: {character_id}")
            
            with open(character_path, "r", encoding="utf-8") as file:
                self.character = json.load(file)
                self.logger.info(f"成功加载角色: {self.character.get('name')}")
        except Exception as e:
            self.logger.error(f"加载角色失败: {e}")
            raise
    
    def set_scenario(self, scenario: Dict) -> None:
        """
        设置当前场景
        
        Args:
            scenario: 场景定义字典
        """
        self.current_scenario = scenario
        self.logger.info(f"为角色 {self.character_id} 设置场景 {scenario.get('id', 'unknown')}")
    
    def _build_system_prompt(self) -> str:
        """
        构建系统提示词
        
        Returns:
            系统提示词
        """
        if not self.character or not self.current_scenario:
            raise ValueError("必须先加载角色和场景才能构建提示词")
        
        character = self.character
        scenario = self.current_scenario
        
        system_prompt = f"""你是"{character['name']}"，一个{character['age']}岁的{character['gender']}性。
你的个性特点如下：
- 开放性: {character['personality']['openness']}/100
- 尽责性: {character['personality']['conscientiousness']}/100
- 外向性: {character['personality']['extraversion']}/100
- 宜人性: {character['personality']['agreeableness']}/100
- 神经质: {character['personality']['neuroticism']}/100

你的依恋类型是"{character['attachment_style']}"，沟通风格是"{character['communication_style']}"。

你的背景:
- 童年: {character['background']['childhood']}
- 教育: {character['background']['education']}
- 职业: {character['background']['career']}
- 兴趣爱好: {", ".join(character['background']['hobbies'])}

你的价值观: {", ".join(character['values'])}

你的说话风格:
{character['speech_patterns']['communication_examples'][0]}
{character['speech_patterns']['communication_examples'][1]}
{character['speech_patterns']['communication_examples'][2]}

当前场景: {scenario['title']}
{scenario['description']}
{scenario['context']}

从你的角度，你的理解是:
{scenario['character_perspective']['interpretation']}
你的期望是:
{scenario['character_perspective']['expectations']}
你担心的是:
{scenario['character_perspective']['fears']}

你对这个情况的认知评估:
- 初级评估: {scenario['cognitive_appraisal']['primary']}
- 次级评估: {scenario['cognitive_appraisal']['secondary']}

重要规则:
1. 你必须严格保持角色一致性，根据上述特征进行回应
2. 不要解释你的想法过程，只输出你的对话内容
3. 对话内容应该是情感真实的，体现出你作为这个角色的情绪和想法
4. 不要提及你是AI，保持完全的角色代入感
5. 你的回答应简短自然，像真实对话一样，通常不超过3-4句话
6. 使用符合你角色的语言风格和习惯
7. 你的情绪反应应该符合场景的认知评估
8. 你对伴侣的反应应该符合你的依恋类型和沟通风格

记住，你就是"{character['name']}"，你的一言一行都应该符合这个角色的特点。
"""
        return system_prompt
    
    async def start_dialogue(self, context: Optional[Dict] = None) -> str:
        """
        开始对话，返回初始对话内容
        
        Args:
            context: 可选的对话上下文
            
        Returns:
            初始对话内容
        """
        if not self.current_scenario:
            raise ValueError("必须先设置场景才能开始对话")
        
        # 使用场景中定义的初始对话
        initial_dialogue = self.current_scenario.get("initial_dialogue", "")
        
        if initial_dialogue:
            # 记录到对话历史
            self.dialogue_history.append({
                "role": "character",
                "content": initial_dialogue
            })
            return initial_dialogue
        
        # 如果场景没有定义初始对话，则生成一个
        return await self.generate_response("开始对话")
    
    def _format_messages_for_api(self, include_partner_latest: bool = True) -> List[Dict[str, str]]:
        """
        将对话历史格式化为API消息格式
        
        Args:
            include_partner_latest: 是否包含伴侣最新消息
            
        Returns:
            格式化的消息列表
        """
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        
        # 添加历史消息，调整role
        for entry in self.dialogue_history:
            role = "user" if entry["role"] == "partner" else "assistant"
            # 如果是最后一条伴侣消息且不包含，则跳过
            if not include_partner_latest and entry == self.dialogue_history[-1] and entry["role"] == "partner":
                continue
            messages.append({"role": role, "content": entry["content"]})
        
        return messages
    
    async def generate_response(self, partner_message: Optional[str] = None) -> str:
        """
        生成对伴侣消息的回应
        
        Args:
            partner_message: 伴侣消息，如果为None则不添加新消息
            
        Returns:
            生成的回应
        """
        # 如果有新消息，添加到历史
        if partner_message:
            self.dialogue_history.append({
                "role": "partner",
                "content": partner_message
            })
        
        # 准备API请求
        messages = self._format_messages_for_api()
        
        # 调用API (使用异步版本)
        response = await self.api.async_chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            agent_type="character"
        )
        
        # 提取回应文本
        response_text = self.api.extract_response_text(response)
        
        # 添加到对话历史
        self.dialogue_history.append({
            "role": "character",
            "content": response_text
        })
        
        return response_text
    
    def update_emotional_state(self, emotion: str, intensity: int) -> None:
        """
        更新角色的情绪状态
        
        Args:
            emotion: 情绪类型
            intensity: 情绪强度（0-100）
        """
        self.emotional_state["current_emotion"] = emotion
        self.emotional_state["emotion_intensity"] = intensity
        self.emotional_state["emotion_trajectory"].append({
            "turn": len(self.dialogue_history),
            "emotion": emotion,
            "intensity": intensity
        })
        
        self.logger.info(f"角色 {self.character['name']} 当前情绪: {emotion}, 强度: {intensity}")
    
    def get_dialogue_summary(self) -> Dict:
        """
        获取对话摘要
        
        Returns:
            对话摘要字典
        """
        return {
            "character": self.character["name"],
            "scenario": self.current_scenario["title"] if self.current_scenario else "未知",
            "turns": len(self.dialogue_history) // 2,  # 每回合包含伴侣和角色各一条消息
            "current_emotion": self.emotional_state["current_emotion"],
            "emotion_intensity": self.emotional_state["emotion_intensity"],
            "dialogue_history": self.dialogue_history
        }

    async def respond(self, message: str, context: Optional[Dict] = None) -> str:
        """
        响应伙伴的消息（DialogueManager所需的接口方法）
        
        Args:
            message: 伙伴的消息内容
            context: 可选的上下文信息
            
        Returns:
            角色的回应内容
        """
        response = await self.generate_response(message)
        return response
        
    def get_character_info(self) -> Dict:
        """
        获取角色信息（DialogueManager所需的接口方法）
        
        Returns:
            角色的基本信息
        """
        return {
            "id": self.character_id,
            "name": self.character.get("name", ""),
            "profile": self.character.get("profile", {}),
            "emotional_state": self.emotional_state
        }
        
    def get_dialogue_history(self) -> List[Dict]:
        """
        获取对话历史（DialogueManager所需的接口方法）
        
        Returns:
            对话历史记录列表
        """
        return self.dialogue_history
        
    def set_api(self, api: Any) -> None:
        """
        设置API实例（DialogueManager所需的接口方法）
        
        Args:
            api: OpenRouterAPI实例
        """
        self.api = api

    def get_scenario_info(self) -> Dict:
        """
        获取当前场景信息（DialogueManager所需的接口方法）
        
        Returns:
            场景的基本信息
        """
        if not self.current_scenario:
            self.logger.warning("尚未设置场景，返回空场景信息")
            return {}
            
        return self.current_scenario


# 简单测试用例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    async def test_character_agent():
        try:
            # 加载测试场景
            base_dir = Path(__file__).resolve().parent.parent.parent
            scenario_path = base_dir / "data" / "scenarios" / "templates" / "scenario_005.json"
            with open(scenario_path, 'r', encoding='utf-8') as f:
                scenario = json.load(f)
            
            # 创建角色Agent
            agent = CharacterAgent("char_001")
            
            # 设置场景
            agent.set_scenario(scenario)
            
            # 开始对话
            initial = await agent.start_dialogue()
            print(f"{agent.character['name']}: {initial}")
            
            # 模拟伴侣回应
            response = await agent.generate_response("我刚刚开完会，手机调成静音了，没看到你的消息，抱歉让你担心了。")
            print(f"{agent.character['name']}: {response}")
            
            # 再次回应
            response = await agent.generate_response("我不是故意忽视你的，真的只是因为工作太忙。你还好吗？")
            print(f"{agent.character['name']}: {response}")
            
            # 打印对话摘要
            print("\n对话摘要:")
            summary = agent.get_dialogue_summary()
            print(f"角色: {summary['character']}")
            print(f"场景: {summary['scenario']}")
            print(f"回合数: {summary['turns']}")
            print(f"当前情绪: {summary['current_emotion']}")
            print(f"情绪强度: {summary['emotion_intensity']}")
            
        except Exception as e:
            logging.error(f"测试失败: {e}")
    
    # 运行测试
    asyncio.run(test_character_agent()) 