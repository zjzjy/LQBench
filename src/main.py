#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# 将项目根目录添加到路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.agents.character_agent import CharacterAgent
from src.agents.partner_agent import PartnerAgent
from src.agents.emotion_agent import EmotionAgent
from src.dialogue.dialogue_manager import DialogueManager
from src.utils.data_loader import DataLoader
from src.visualization.dialogue_visualizer import DialogueVisualizer

# 配置日志
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(filename=LOG_DIR / f"love_{datetime.now().strftime('%Y%m%d%H%M%S')}.log", mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger("main")

class LOVESystem:
    """
    LOVE系统主类，用于协调各组件的运行
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化LOVE系统
        
        Args:
            config_path: 配置文件路径，默认为None（使用默认配置）
        """
        self.logger = logging.getLogger("LOVE")
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化数据加载器
        self.data_loader = DataLoader()
        
        # 设置结果目录
        self.result_dir = ROOT_DIR / "results" / "dialogues"
        self.result_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化可视化工具
        self.visualizer = DialogueVisualizer()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置数据
        """
        default_config = {
            "max_turns": 10,
            "save_results": True,
            "generate_report": True,
            "api_settings": {
                "timeout": 30,
                "max_retries": 3
            }
        }
        
        if not config_path:
            self.logger.info("使用默认配置")
            return default_config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                
            # 合并配置
            for key, value in user_config.items():
                if isinstance(value, dict) and key in default_config and isinstance(default_config[key], dict):
                    default_config[key].update(value)
                else:
                    default_config[key] = value
                    
            self.logger.info(f"已加载配置文件: {config_path}")
            return default_config
        
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return default_config
    
    async def run_dialogue(self, character_id: Optional[str] = None, scenario_id: Optional[str] = None) -> Dict:
        """
        运行单次对话
        
        Args:
            character_id: 角色ID，如果为None则随机选择
            scenario_id: 场景ID，如果为None则随机选择
            
        Returns:
            对话结果
        """
        # 加载角色和场景
        if character_id and scenario_id:
            self.logger.info(f"使用指定的角色和场景: {character_id}, {scenario_id}")
            character = self.data_loader.load_character(character_id)
            scenario = self.data_loader.load_scenario(scenario_id)
            
            if not character:
                self.logger.error(f"无法加载指定角色: {character_id}")
                return {}
                
            if not scenario:
                self.logger.error(f"无法加载指定场景: {scenario_id}")
                return {}
        else:
            self.logger.info("随机选择角色和场景")
            character, scenario = self.data_loader.match_character_scenario(character_id, scenario_id)
        
        # 创建代理
        character_agent = CharacterAgent(character.get("id", "char_001"))
        character_agent.character = character
        character_agent.set_scenario(scenario)
        
        partner_agent = PartnerAgent()
        partner_agent.set_character_info(character)
        partner_agent.set_scenario(scenario)
        
        emotion_agent = EmotionAgent()
        
        # 设置代理的初始数据
        emotion_agent.set_character_info(character)
        
        # 创建对话管理器
        dialogue_manager = DialogueManager(
            character_agent=character_agent,
            partner_agent=partner_agent,
            emotion_agent=emotion_agent,
            max_turns=self.config.get("max_turns", 10),
            save_dir=str(self.result_dir) if self.config.get("save_results", True) else None
        )
        
        # 开始对话
        self.logger.info(f"开始对话: 角色 {character.get('name')} - 场景 {scenario.get('title')}")
        await dialogue_manager.start_dialogue()
        
        # 进行多轮对话
        for turn in range(self.config.get("max_turns", 10)):
            self.logger.info(f"进行第 {turn + 1} 轮对话")
            continue_dialogue = await dialogue_manager.next_turn()
            if not continue_dialogue:
                self.logger.info("对话提前结束")
                break
        
        # 结束对话并获取结果
        result = await dialogue_manager.end_dialogue()
        self.logger.info(f"对话完成: {result.get('dialogue_id')}")
        
        # 如果需要生成报告，则调用可视化工具
        if self.config.get("generate_report", True) and dialogue_manager.save_dir:
            self.logger.info("生成对话可视化报告")
            report = self.visualizer.generate_dialogue_report(dialogue_manager.save_dir)
            if report:
                result["visualization_report"] = report
        
        return result
    
    async def run_batch_dialogues(self, batch_config: List[Dict]) -> List[Dict]:
        """
        运行批量对话
        
        Args:
            batch_config: 批量对话配置列表，每项包含character_id和scenario_id
            
        Returns:
            对话结果列表
        """
        results = []
        
        for i, config in enumerate(batch_config):
            self.logger.info(f"开始批量对话 {i+1}/{len(batch_config)}")
            character_id = config.get("character_id")
            scenario_id = config.get("scenario_id")
            
            result = await self.run_dialogue(character_id, scenario_id)
            if result:
                results.append(result)
            
            # 批量运行时可以添加延迟，防止API限流
            if i < len(batch_config) - 1:
                await asyncio.sleep(2)
        
        return results
    
    async def run_evaluation(self, character_ids: Optional[List[str]] = None, scenario_ids: Optional[List[str]] = None) -> Dict:
        """
        运行评估模式
        
        Args:
            character_ids: 角色ID列表，如果为None则使用所有角色
            scenario_ids: 场景ID列表，如果为None则使用所有场景
            
        Returns:
            评估结果
        """
        # 获取所有角色和场景
        if not character_ids:
            character_ids = self.data_loader.get_character_ids()
        
        if not scenario_ids:
            scenario_ids = self.data_loader.get_scenario_ids()
        
        self.logger.info(f"开始评估模式: {len(character_ids)} 个角色, {len(scenario_ids)} 个场景")
        
        # 构建批量配置
        batch_config = []
        for char_id in character_ids:
            character = self.data_loader.load_character(char_id)
            if not character:
                continue
                
            # 对每个角色，选择兼容的场景
            compatible_scenarios = character.get("conflict_scenarios", [])
            
            # 如果没有指定兼容场景，或者指定的场景不在可用场景中，则使用所有可用场景
            if not compatible_scenarios or not set(compatible_scenarios).intersection(set(scenario_ids)):
                for scenario_id in scenario_ids:
                    batch_config.append({"character_id": char_id, "scenario_id": scenario_id})
            else:
                # 只使用兼容场景中的可用场景
                for scenario_id in set(compatible_scenarios).intersection(set(scenario_ids)):
                    batch_config.append({"character_id": char_id, "scenario_id": scenario_id})
        
        # 运行批量对话
        results = await self.run_batch_dialogues(batch_config)
        
        # 汇总结果
        evaluation_result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_dialogues": len(results),
            "characters_evaluated": len(character_ids),
            "scenarios_evaluated": len(scenario_ids),
            "dialogue_results": results,
            "summary": self._generate_evaluation_summary(results)
        }
        
        # 保存评估结果
        if self.config.get("save_results", True):
            result_path = ROOT_DIR / "results" / f"evaluation_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation_result, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"评估结果已保存到: {result_path}")
        
        return evaluation_result
    
    def _generate_evaluation_summary(self, results: List[Dict]) -> Dict:
        """
        生成评估摘要
        
        Args:
            results: 对话结果列表
            
        Returns:
            评估摘要
        """
        if not results:
            return {"error": "无评估结果"}
        
        # 统计情绪变化
        emotion_changes = {}
        dialogue_lengths = []
        character_stats = {}
        scenario_stats = {}
        
        for result in results:
            # 对话长度
            dialogue_lengths.append(result.get("total_turns", 0))
            
            # 角色和场景统计
            summary = result.get("summary", {})
            char_name = summary.get("character_name", "未知")
            scenario_title = summary.get("scenario_title", "未知")
            
            if char_name not in character_stats:
                character_stats[char_name] = {"count": 0, "total_messages": 0}
            character_stats[char_name]["count"] += 1
            character_stats[char_name]["total_messages"] = character_stats[char_name].get("total_messages", 0) + summary.get("total_messages", 0)
            
            if scenario_title not in scenario_stats:
                scenario_stats[scenario_title] = {"count": 0, "total_messages": 0}
            scenario_stats[scenario_title]["count"] += 1
            scenario_stats[scenario_title]["total_messages"] = scenario_stats[scenario_title].get("total_messages", 0) + summary.get("total_messages", 0)
            
            # 情绪变化
            evaluation = result.get("evaluation", {})
            emotion_eval = evaluation.get("emotion_evaluation", {})
            
            for emotion, change in emotion_eval.items():
                if emotion not in emotion_changes:
                    emotion_changes[emotion] = []
                emotion_changes[emotion].append(change)
        
        # 计算平均值
        avg_dialogue_length = sum(dialogue_lengths) / len(dialogue_lengths) if dialogue_lengths else 0
        
        # 计算每个角色的平均消息数
        for char in character_stats:
            if character_stats[char]["count"] > 0:
                character_stats[char]["avg_messages"] = character_stats[char]["total_messages"] / character_stats[char]["count"]
            else:
                character_stats[char]["avg_messages"] = 0
        
        # 计算每个场景的平均消息数
        for scenario in scenario_stats:
            if scenario_stats[scenario]["count"] > 0:
                scenario_stats[scenario]["avg_messages"] = scenario_stats[scenario]["total_messages"] / scenario_stats[scenario]["count"]
            else:
                scenario_stats[scenario]["avg_messages"] = 0
        
        # 计算情绪变化平均值
        avg_emotion_changes = {}
        for emotion, changes in emotion_changes.items():
            avg_emotion_changes[emotion] = sum(changes) / len(changes) if changes else 0
        
        return {
            "avg_dialogue_length": avg_dialogue_length,
            "character_stats": character_stats,
            "scenario_stats": scenario_stats,
            "avg_emotion_changes": avg_emotion_changes
        }


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LOVE - 情感智能评估系统")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--character", type=str, help="指定角色ID")
    parser.add_argument("--scenario", type=str, help="指定场景ID")
    parser.add_argument("--mode", type=str, default="single", choices=["single", "batch", "evaluation"], help="运行模式: single(单次对话), batch(批量对话), evaluation(评估模式)")
    parser.add_argument("--batch-config", type=str, help="批量对话配置文件路径")
    
    args = parser.parse_args()
    
    # 创建LOVE系统
    system = LOVESystem(args.config)
    
    # 根据模式运行
    if args.mode == "single":
        # 单次对话模式
        result = await system.run_dialogue(args.character, args.scenario)
        logger.info(f"对话完成: {result.get('dialogue_id')}")
        
    elif args.mode == "batch":
        # 批量对话模式
        if not args.batch_config:
            logger.error("批量模式需要指定批量配置文件")
            return
        
        try:
            with open(args.batch_config, 'r', encoding='utf-8') as f:
                batch_config = json.load(f)
            
            results = await system.run_batch_dialogues(batch_config)
            logger.info(f"批量对话完成，共 {len(results)} 个对话")
            
        except Exception as e:
            logger.error(f"批量对话失败: {e}")
            
    elif args.mode == "evaluation":
        # 评估模式
        character_ids = [args.character] if args.character else None
        scenario_ids = [args.scenario] if args.scenario else None
        
        result = await system.run_evaluation(character_ids, scenario_ids)
        logger.info(f"评估完成，共 {result.get('total_dialogues')} 个对话")


if __name__ == "__main__":
    asyncio.run(main()) 