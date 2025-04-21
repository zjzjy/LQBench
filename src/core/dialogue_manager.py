import json
import logging
import time
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from ..agents.character_agent import CharacterAgent
from ..agents.partner_agent import PartnerAgent
from ..agents.emotion_agent import EmotionAgent
from ..api.openrouter_api import OpenRouterAPI
from ..utils.helper_functions import get_timestamp, get_uuid, ensure_dir_exists

class DialogueManager:
    """
    对话管理器，协调多个Agent之间的交互，管理对话流程
    """
    
    def __init__(self, 
                 character_id: str,
                 scenario_id: str,
                 output_dir: Optional[str] = None,
                 save_dialogue: bool = True,
                 config_path: str = "config/api_config.json"):
        """
        初始化对话管理器
        
        Args:
            character_id: 角色ID
            scenario_id: 场景ID
            output_dir: 对话输出保存目录
            save_dialogue: 是否保存对话
            config_path: API配置文件路径
        """
        self.logger = logging.getLogger(__name__)
        self.character_id = character_id
        self.scenario_id = scenario_id
        self.save_dialogue = save_dialogue
        self.session_id = get_uuid()
        
        # 输出目录
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("output/dialogues")
        
        ensure_dir_exists(self.output_dir)
        
        # 初始化API客户端
        self.api_client = OpenRouterAPI(config_path)
        
        # 初始化代理
        self.character_agent = CharacterAgent(character_id, config_path=config_path)
        self.partner_agent = PartnerAgent(config_path=config_path)
        self.emotion_agent = EmotionAgent(config_path=config_path)
        
        # 对话历史
        self.dialogue_history = []
        self.turn_count = 0
        
        # 记录当前状态
        self.active = False
        self.error = None
        
    async def initialize_session(self):
        """初始化会话，设置角色和场景信息"""
        try:
            # 初始化场景
            await self.character_agent.load_character(self.character_id)
            await self.character_agent.load_scenario(self.scenario_id)
            
            # 初始化记忆代理
            character_info = self.character_agent.character_info
            scenario_info = self.character_agent.scenario_info
            
            # 设置伴侣代理信息
            self.partner_agent.set_character_info(character_info)
            self.partner_agent.set_scenario_info(scenario_info)
            
            # 设置情绪代理信息
            self.emotion_agent.set_character_info(character_info)
            self.emotion_agent.set_scenario_info(scenario_info)
            
            self.active = True
            self.logger.info(f"初始化会话成功: {self.session_id}, 角色: {self.character_id}, 场景: {self.scenario_id}")
            
            # 返回初始会话信息
            return {
                "session_id": self.session_id,
                "character": character_info,
                "scenario": scenario_info,
                "status": "initialized"
            }
            
        except Exception as e:
            self.error = str(e)
            self.active = False
            self.logger.error(f"初始化会话失败: {str(e)}")
            return {
                "session_id": self.session_id,
                "status": "error",
                "error": str(e)
            }
    
    async def start_dialogue(self, initial_message: Optional[str] = None) -> Dict:
        """
        开始对话，生成冲突场景的第一个回合
        
        Args:
            initial_message: 用户可选的初始消息
            
        Returns:
            对话回合信息
        """
        if not self.active:
            await self.initialize_session()
            
        try:
            # 获取场景信息
            scenario = self.character_agent.scenario_info
            
            # 如果用户没有提供初始消息，使用场景提供的开场白
            if not initial_message and 'initial_message' in scenario:
                initial_message = scenario['initial_message']
            elif not initial_message:
                # 让伴侣代理生成开场白
                initial_context = {
                    "task": "generate_initial_message",
                    "character_info": self.character_agent.character_info,
                    "scenario_info": self.character_agent.scenario_info
                }
                initial_message = await self.partner_agent.generate_message(initial_context)
            
            # 记录第一条消息
            first_message = {
                "id": get_uuid(),
                "speaker": "partner",
                "content": initial_message,
                "timestamp": get_timestamp(),
                "turn": 0
            }
            
            # 更新对话历史
            self.dialogue_history.append(first_message)
            
            # 分析情绪状态
            emotion_data = await self.emotion_agent.async_analyze_emotions(first_message["content"])
            
            # 获取角色回复
            memory_context = {"key_memories": [], "context_summary": ""}
            
            response_context = {
                "dialogue_history": self.dialogue_history,
                "memory_context": memory_context,
                "emotion_data": emotion_data
            }
            
            character_response = await self.character_agent.generate_response(response_context)
            
            # 记录角色回复
            character_message = {
                "id": get_uuid(),
                "speaker": "character",
                "content": character_response,
                "timestamp": get_timestamp(),
                "turn": 0,
                "emotion_data": emotion_data
            }
            
            # 更新对话历史
            self.dialogue_history.append(character_message)
            
            # 分析角色回复的情绪状态
            character_emotion = await self.emotion_agent.async_analyze_emotions(character_response)
            character_message["emotion_data"] = character_emotion
            
            # 更新回合计数
            self.turn_count += 1
            
            # 如果启用了保存功能，保存当前对话
            if self.save_dialogue:
                await self.save_dialogue_history()
                
            return {
                "session_id": self.session_id,
                "turn": self.turn_count,
                "messages": self.dialogue_history[-2:],
                "memory_context": memory_context,
                "emotion_data": {
                    "partner": emotion_data,
                    "character": character_emotion
                }
            }
            
        except Exception as e:
            self.error = str(e)
            self.logger.error(f"开始对话失败: {str(e)}")
            return {
                "session_id": self.session_id,
                "status": "error",
                "error": str(e)
            }
    
    async def process_user_message(self, message: str) -> Dict:
        """
        处理用户输入的消息，生成角色回复
        
        Args:
            message: 用户消息内容
            
        Returns:
            对话回合信息
        """
        if not self.active:
            await self.initialize_session()
            
        try:
            # 记录用户消息
            user_message = {
                "id": get_uuid(),
                "speaker": "partner",
                "content": message,
                "timestamp": get_timestamp(),
                "turn": self.turn_count + 1
            }
            
            # 更新对话历史
            self.dialogue_history.append(user_message)
            
            # 分析情绪状态
            emotion_data = await self.emotion_agent.async_analyze_emotions(message)
            user_message["emotion_data"] = emotion_data
            
            # 获取角色回复
            memory_context = {"key_memories": [], "context_summary": ""}
            
            response_context = {
                "dialogue_history": self.dialogue_history,
                "memory_context": memory_context,
                "emotion_data": emotion_data
            }
            
            character_response = await self.character_agent.generate_response(response_context)
            
            # 记录角色回复
            character_message = {
                "id": get_uuid(),
                "speaker": "character",
                "content": character_response,
                "timestamp": get_timestamp(),
                "turn": self.turn_count + 1,
                "emotion_data": None
            }
            
            # 更新对话历史
            self.dialogue_history.append(character_message)
            
            # 分析角色回复的情绪状态
            character_emotion = await self.emotion_agent.async_analyze_emotions(character_response)
            character_message["emotion_data"] = character_emotion
            
            # 更新回合计数
            self.turn_count += 1
            
            # 如果启用了保存功能，保存当前对话
            if self.save_dialogue:
                await self.save_dialogue_history()
                
            return {
                "session_id": self.session_id,
                "turn": self.turn_count,
                "messages": self.dialogue_history[-2:],
                "memory_context": memory_context,
                "emotion_data": {
                    "partner": emotion_data,
                    "character": character_emotion
                }
            }
            
        except Exception as e:
            self.error = str(e)
            self.logger.error(f"处理用户消息失败: {str(e)}")
            return {
                "session_id": self.session_id,
                "status": "error",
                "error": str(e)
            }
    
    async def generate_partner_message(self) -> Dict:
        """
        自动生成伴侣消息，用于自动对话模式
        
        Returns:
            对话回合信息
        """
        if not self.active:
            await self.initialize_session()
            
        try:
            # 获取最新的记忆上下文
            memory_context = {"key_memories": [], "context_summary": ""}
            
            # 获取伴侣回复
            partner_context = {
                "dialogue_history": self.dialogue_history,
                "memory_context": memory_context,
                "character_info": self.character_agent.character_info,
                "scenario_info": self.character_agent.scenario_info
            }
            
            partner_message_content = await self.partner_agent.generate_message(partner_context)
            
            # 记录伴侣消息
            partner_message = {
                "id": get_uuid(),
                "speaker": "partner",
                "content": partner_message_content,
                "timestamp": get_timestamp(),
                "turn": self.turn_count + 1
            }
            
            # 处理伴侣消息，生成角色回复
            return await self.process_user_message(partner_message_content)
            
        except Exception as e:
            self.error = str(e)
            self.logger.error(f"生成伴侣消息失败: {str(e)}")
            return {
                "session_id": self.session_id,
                "status": "error",
                "error": str(e)
            }
    
    async def run_auto_dialogue(self, turns: int = 5) -> List[Dict]:
        """
        运行自动对话模式，生成指定回合数的对话
        
        Args:
            turns: 要生成的对话回合数
            
        Returns:
            所有对话回合信息列表
        """
        if not self.active:
            await self.initialize_session()
            
        results = []
        
        try:
            # 先开始对话
            first_turn = await self.start_dialogue()
            results.append(first_turn)
            
            # 生成剩余回合
            for _ in range(turns - 1):
                turn_result = await self.generate_partner_message()
                results.append(turn_result)
                
                # 检查是否有错误
                if "error" in turn_result:
                    break
                    
            return results
            
        except Exception as e:
            self.error = str(e)
            self.logger.error(f"运行自动对话失败: {str(e)}")
            return results + [{
                "session_id": self.session_id,
                "status": "error",
                "error": str(e)
            }]
    
    async def save_dialogue_history(self) -> str:
        """
        保存当前对话历史到文件
        
        Returns:
            保存的文件路径
        """
        if not self.save_dialogue:
            return ""
            
        try:
            # 创建输出文件名
            timestamp = get_timestamp("%Y%m%d_%H%M%S")
            filename = f"{self.character_id}_{self.scenario_id}_{timestamp}.json"
            filepath = self.output_dir / filename
            
            # 创建输出数据
            output_data = {
                "session_id": self.session_id,
                "character_id": self.character_id,
                "scenario_id": self.scenario_id,
                "timestamp": get_timestamp(),
                "turns": self.turn_count,
                "dialogue_history": self.dialogue_history,
                "character_info": self.character_agent.character_info,
                "scenario_info": self.character_agent.scenario_info,
                "memory_summary": "记忆功能已禁用"
            }
            
            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"对话已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"保存对话失败: {str(e)}")
            return ""
    
    async def end_session(self) -> Dict:
        """
        结束对话会话，生成总结报告
        
        Returns:
            会话总结信息
        """
        if not self.active:
            return {
                "session_id": self.session_id,
                "status": "inactive",
                "message": "会话未激活"
            }
            
        try:
            # 生成情绪分析报告
            emotion_summary = await self.emotion_agent.generate_report(self.dialogue_history)
            
            # 生成记忆摘要 - 替换为空的记忆摘要
            memory_summary = "记忆功能已禁用"
            
            # 保存最终报告
            final_report = {
                "session_id": self.session_id,
                "character_id": self.character_id,
                "scenario_id": self.scenario_id,
                "turns": self.turn_count,
                "start_time": self.dialogue_history[0]["timestamp"] if self.dialogue_history else get_timestamp(),
                "end_time": get_timestamp(),
                "dialogue_history": self.dialogue_history,
                "emotion_summary": emotion_summary,
                "memory_summary": memory_summary
            }
            
            # 保存报告
            if self.save_dialogue:
                report_path = self.output_dir / f"{self.session_id}_report.json"
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(final_report, f, ensure_ascii=False, indent=2)
                    
                self.logger.info(f"对话报告已保存: {report_path}")
            
            # 标记会话为非活动
            self.active = False
            
            return final_report
            
        except Exception as e:
            self.error = str(e)
            self.logger.error(f"结束会话失败: {str(e)}")
            return {
                "session_id": self.session_id,
                "status": "error",
                "error": str(e)
            }


# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def run_test():
        # 创建对话管理器
        manager = DialogueManager(
            character_id="char_001",
            scenario_id="scenario_005",
            save_dialogue=True
        )
        
        # 初始化会话
        init_result = await manager.initialize_session()
        print(f"初始化结果: {json.dumps(init_result, ensure_ascii=False, indent=2)}")
        
        # 运行自动对话
        dialogue_results = await manager.run_auto_dialogue(turns=3)
        
        # 打印结果
        print(f"\n生成了 {len(dialogue_results)} 个回合的对话:")
        for i, result in enumerate(dialogue_results):
            print(f"\n--- 回合 {i+1} ---")
            if "messages" in result:
                for msg in result["messages"]:
                    speaker = "角色" if msg["speaker"] == "character" else "伴侣"
                    print(f"{speaker}: {msg['content']}")
                    if "emotion_data" in msg:
                        print(f"情绪状态: {json.dumps(msg['emotion_data'], ensure_ascii=False)}")
            elif "error" in result:
                print(f"错误: {result['error']}")
        
        # 结束会话
        end_result = await manager.end_session()
        print(f"\n会话结束状态: {json.dumps(end_result, ensure_ascii=False, indent=2)}")
    
    # 运行测试
    asyncio.run(run_test()) 