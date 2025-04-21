import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from src.agents.character_agent import CharacterAgent
from src.agents.partner_agent import PartnerAgent
from src.agents.emotion_agent import EmotionAgent
from src.utils.helper_functions import get_timestamp, get_uuid, ensure_dir_exists

logger = logging.getLogger(__name__)

class DialogueManager:
    """对话管理器，负责协调角色代理和伙伴代理之间的对话流程"""
    
    def __init__(
        self,
        character_agent: CharacterAgent,
        partner_agent: PartnerAgent,
        emotion_agent: Optional[EmotionAgent] = None,
        max_turns: int = 10,
        save_dir: Optional[str] = None,
        dialogue_id: Optional[str] = None,
    ):
        """
        初始化对话管理器
        
        Args:
            character_agent: 角色代理
            partner_agent: 伙伴代理
            emotion_agent: 情绪代理（可选）
            max_turns: 最大对话轮次
            save_dir: 对话保存目录
            dialogue_id: 对话ID，如果为None则自动生成
        """
        self.character_agent = character_agent
        self.partner_agent = partner_agent
        self.emotion_agent = emotion_agent
        self.max_turns = max_turns
        
        # 初始化对话状态
        self.dialogue_id = dialogue_id or f"dialogue_{get_uuid()[:8]}"
        self.dialogue_history = []
        self.current_turn = 0
        self.is_active = False
        self.start_time = None
        self.end_time = None
        
        # 设置保存目录
        if save_dir:
            self.save_dir = ensure_dir_exists(Path(save_dir) / self.dialogue_id)
        else:
            self.save_dir = None
    
    async def start_dialogue(self, initial_context: Optional[Dict] = None) -> None:
        """
        开始对话
        
        Args:
            initial_context: 初始上下文信息
        """
        if self.is_active:
            logger.warning("对话已经在进行中")
            return
        
        self.is_active = True
        self.start_time = get_timestamp()
        self.current_turn = 0
        self.dialogue_history = []
        
        logger.info(f"开始对话 {self.dialogue_id}")
        
        # 设置初始上下文
        context = initial_context or {}
        
        # 由角色代理发起对话
        first_message = await self.character_agent.start_dialogue(context)
        if first_message:
            self._add_to_history("character", first_message)
            logger.info(f"角色: {first_message}")
    
    async def next_turn(self) -> bool:
        """
        进行下一轮对话
        
        Returns:
            如果对话继续，返回True；如果对话结束，返回False
        """
        if not self.is_active:
            logger.warning("对话尚未开始")
            return False
        
        if self.current_turn >= self.max_turns:
            logger.info(f"对话达到最大轮次 ({self.max_turns})，结束对话")
            await self.end_dialogue()
            return False
        
        self.current_turn += 1
        logger.info(f"开始第 {self.current_turn} 轮对话")
        
        # 更新情感状态（如果有情绪代理）
        if self.emotion_agent and self.dialogue_history:
            await self._update_emotions()
        
        # 更新记忆的代码替换为提供空的上下文
        memory_context = {}
        
        # 获取最后一条消息
        last_message = self.dialogue_history[-1] if self.dialogue_history else None
        if not last_message:
            logger.warning("对话历史为空，无法继续对话")
            return False
        
        # 根据最后一条消息的发送者，确定下一步由谁回复
        if last_message["sender"] == "character":
            # 伙伴代理回复
            context = {
                "dialogue_history": self.dialogue_history,
                "memory_context": memory_context,
                "current_turn": self.current_turn,
            }
            response = await self.partner_agent.respond(last_message["content"], context)
            if response:
                self._add_to_history("partner", response)
                logger.info(f"伙伴: {response}")
        else:
            # 角色代理回复
            context = {
                "dialogue_history": self.dialogue_history,
                "memory_context": memory_context,
                "current_turn": self.current_turn,
            }
            response = await self.character_agent.respond(last_message["content"], context)
            if response:
                self._add_to_history("character", response)
                logger.info(f"角色: {response}")
        
        # 保存当前对话状态
        if self.save_dir:
            self._save_dialogue_state()
        
        return True
    
    async def end_dialogue(self) -> Dict:
        """
        结束对话，生成对话摘要和评估结果
        
        Returns:
            对话总结信息
        """
        if not self.is_active:
            logger.warning("对话尚未开始")
            return {}
        
        self.is_active = False
        self.end_time = get_timestamp()
        
        # 生成对话摘要
        summary = self._generate_dialogue_summary()
        
        # 评估对话效果（情感变化等）
        evaluation = await self._evaluate_dialogue()
        
        # 合并摘要和评估结果
        result = {
            "dialogue_id": self.dialogue_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_turns": self.current_turn,
            "summary": summary,
            "evaluation": evaluation,
        }
        
        # 保存最终结果
        if self.save_dir:
            self._save_dialogue_result(result)
        
        logger.info(f"对话 {self.dialogue_id} 已结束")
        return result
    
    def _add_to_history(self, sender: str, content: str) -> None:
        """
        添加消息到对话历史
        
        Args:
            sender: 发送者 ("character" 或 "partner")
            content: 消息内容
        """
        message = {
            "id": f"msg_{len(self.dialogue_history) + 1}",
            "timestamp": get_timestamp(),
            "sender": sender,
            "content": content,
            "emotions": {},  # 将由情绪代理更新
        }
        
        self.dialogue_history.append(message)
    
    async def _update_emotions(self) -> None:
        """更新最新消息的情绪状态"""
        if not self.emotion_agent or not self.dialogue_history:
            return
        
        # 获取最新的消息
        last_message = self.dialogue_history[-1]
        sender = last_message["sender"]
        content = last_message["content"]
        
        # 分析情绪
        emotions = await self.emotion_agent.analyze_emotions(content, sender)
        
        # 更新消息中的情绪
        if emotions:
            self.dialogue_history[-1]["emotions"] = emotions
    
    def _generate_dialogue_summary(self) -> Dict:
        """
        生成对话摘要
        
        Returns:
            摘要信息
        """
        if not self.dialogue_history:
            return {"summary": "无对话记录"}
        
        # 简单的对话摘要
        summary = {
            "total_messages": len(self.dialogue_history),
            "character_messages": sum(1 for msg in self.dialogue_history if msg["sender"] == "character"),
            "partner_messages": sum(1 for msg in self.dialogue_history if msg["sender"] == "partner"),
            "first_message": self.dialogue_history[0]["content"] if self.dialogue_history else "",
            "last_message": self.dialogue_history[-1]["content"] if self.dialogue_history else "",
        }
        
        return summary
    
    async def _evaluate_dialogue(self) -> Dict:
        """
        评估对话效果
        
        Returns:
            评估结果
        """
        evaluation = {
            "overall_score": 0,
            "emotion_changes": [],
            "key_points": []
        }
        
        # 如果有情绪代理，获取情绪变化
        if self.emotion_agent and len(self.dialogue_history) > 1:
            emotion_evaluation = await self.emotion_agent.evaluate_emotions(self.dialogue_history)
            if emotion_evaluation:
                evaluation.update(emotion_evaluation)
        
        return evaluation
    
    def _save_dialogue_state(self) -> None:
        """保存当前对话状态到文件"""
        if not self.save_dir:
            return
        
        state_file = self.save_dir / f"dialogue_state_{self.current_turn}.json"
        
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "dialogue_id": self.dialogue_id,
                    "current_turn": self.current_turn,
                    "start_time": self.start_time,
                    "dialogue_history": self.dialogue_history,
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存对话状态失败: {e}")
    
    def _save_dialogue_result(self, result: Dict) -> None:
        """
        保存对话最终结果到文件
        
        Args:
            result: 对话结果数据
        """
        if not self.save_dir:
            return
        
        result_file = self.save_dir / "dialogue_result.json"
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 保存完整对话历史
            history_file = self.save_dir / "dialogue_history.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.dialogue_history, f, ensure_ascii=False, indent=2)
            
            logger.info(f"对话结果已保存到 {self.save_dir}")
        except Exception as e:
            logger.error(f"保存对话结果失败: {e}")
    
    @property
    def dialogue_length(self) -> int:
        """获取当前对话长度"""
        return len(self.dialogue_history)
    
    def get_dialogue_history(self) -> List[Dict]:
        """
        获取对话历史
        
        Returns:
            对话历史列表
        """
        return self.dialogue_history
    
    def get_dialogue_summary(self) -> Dict:
        """
        获取当前对话摘要
        
        Returns:
            对话摘要
        """
        return self._generate_dialogue_summary()


# 测试用例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建异步测试函数
    async def test_dialogue_manager():
        from src.utils.data_loader import DataLoader
        
        # 加载数据
        data_loader = DataLoader()
        characters = data_loader.load_all_characters()
        scenarios = data_loader.load_all_scenarios()
        
        if not characters or not scenarios:
            logger.error("无法加载角色或情境数据")
            return
        
        # 选择一个角色和情境
        character = list(characters.values())[0]
        scenario = list(scenarios.values())[0]
        
        # 创建代理
        character_agent = CharacterAgent(character.get("id", "char_001"))
        character_agent.character = character
        character_agent.set_scenario(scenario)
        
        partner_agent = PartnerAgent()
        partner_agent.set_character_info(character)
        partner_agent.set_scenario(scenario)
        
        emotion_agent = EmotionAgent()
        emotion_agent.set_character_info(character)
        emotion_agent.set_scenario(scenario)
        
        # 创建对话管理器
        manager = DialogueManager(
            character_agent=character_agent,
            partner_agent=partner_agent,
            emotion_agent=emotion_agent,
            max_turns=5,
            save_dir="./data/dialogues"
        )
        
        # 开始对话
        await manager.start_dialogue()
        
        # 进行多轮对话
        for _ in range(5):
            continue_dialogue = await manager.next_turn()
            if not continue_dialogue:
                break
        
        # 结束对话
        result = await manager.end_dialogue()
        
        # 打印结果摘要
        print("\n对话结果摘要:")
        print(f"对话ID: {result.get('dialogue_id')}")
        print(f"总轮次: {result.get('total_turns')}")
        print(f"开始时间: {result.get('start_time')}")
        print(f"结束时间: {result.get('end_time')}")
        
        summary = result.get('summary', {})
        print(f"\n角色: {summary.get('character_name')}")
        print(f"情境: {summary.get('scenario_title')}")
        print(f"消息总数: {summary.get('total_messages')}")
        print(f"角色消息数: {summary.get('character_messages')}")
        print(f"伙伴消息数: {summary.get('partner_messages')}")
        print(f"记忆摘要: {summary.get('memory_summary')}")
    
    # 运行测试
    asyncio.run(test_dialogue_manager()) 