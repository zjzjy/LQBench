"""
LeBench主程序，处理虚拟人物对话、认知模型生成和评估流程
"""
import asyncio
import json
import os
import argparse
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
import random

from config import MODEL_CONFIGS, CONVERSATION_CONFIG, OUTPUT_CONFIG
from models.expert import ExpertModel
from models.deepseek import DeepSeekModel
from persona.persona import Persona
from persona.conversation_styles import get_conversation_style, CONVERSATION_STYLES
from evaluation.expert_eval import ExpertEvaluator
from evaluation.testee_eval import TesteeEvaluator
from data.scenarios import get_scenario, get_all_scenarios, get_random_scenario
from data.personalities import get_personality, get_all_personalities, get_random_personality


# 设置日志
def setup_logging():
    """配置日志系统"""
    log_dir = OUTPUT_CONFIG.get("log_dir", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO if OUTPUT_CONFIG.get("debug", False) else logging.WARNING,
        format=log_format,
        handlers=[
            logging.FileHandler(f"{log_dir}/lebench_{int(time.time())}.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("lebench")


async def initialize_models() -> Tuple[ExpertModel, DeepSeekModel]:
    """
    初始化模型
    
    Returns:
        专家模型和待测模型的元组
    """
    expert_config = MODEL_CONFIGS.get("expert", {})
    deepseek_config = MODEL_CONFIGS.get("deepseek", {})
    
    expert_model = ExpertModel(expert_config)
    deepseek_model = DeepSeekModel(deepseek_config)
    
    return expert_model, deepseek_model


async def create_persona(
    expert_model: ExpertModel,
    scenario_id: Optional[str] = None,
    personality_id: Optional[str] = None,
    conversation_style: Optional[str] = None
) -> Tuple[Persona, Dict[str, Any], Dict[str, Any]]:
    """
    创建虚拟人物
    
    Args:
        expert_model: 专家模型
        scenario_id: 情境ID，如果为None则随机选择
        personality_id: 人物角色ID，如果为None则随机选择
        conversation_style: 对话风格，如果为None则随机选择
        
    Returns:
        虚拟人物实例、情境数据和人物数据的元组
    """
    # 获取场景和人物
    scenario = get_scenario(scenario_id) if scenario_id else get_random_scenario()
    personality = get_personality(personality_id) if personality_id else get_random_personality()
    
    # 选择对话风格
    if not conversation_style or conversation_style not in CONVERSATION_STYLES:
        conversation_style = random.choice(list(CONVERSATION_STYLES.keys()))
    
    # 创建虚拟人物
    persona = Persona(
        expert_model=expert_model,
        persona_config=personality,
        situation=scenario["context"],
        conversation_style_name=conversation_style
    )
    
    # 初始化认知模型
    await persona.initialize_cognitive_model()
    
    return persona, scenario, personality


async def run_conversation(
    persona: Persona,
    deepseek_model: DeepSeekModel,
    scenario: Dict[str, Any],
    logger: logging.Logger
) -> List[Dict[str, str]]:
    """
    运行虚拟人物与待测模型之间的对话
    
    Args:
        persona: 虚拟人物实例
        deepseek_model: 待测模型
        scenario: 情境数据
        logger: 日志器
        
    Returns:
        对话历史
    """
    max_turns = CONVERSATION_CONFIG.get("max_turns", 15)
    min_turns = CONVERSATION_CONFIG.get("min_turns", 5)
    mood_threshold = CONVERSATION_CONFIG.get("mood_threshold", 0.8)
    
    # 初始化对话
    logger.info("开始对话")
    
    # 第一条消息由虚拟人物发起
    initial_message = f"""
    嗨，我最近遇到一些事情，心情有点复杂，可以和你聊聊吗？
    
    {scenario['description']}
    """
    
    conversation_history = [{"role": "assistant", "content": initial_message.strip()}]
    logger.info(f"虚拟人物: {initial_message.strip()}")
    
    # 记录初始情绪
    initial_mood = await persona.expert_model.evaluate_mood(initial_message, conversation_history)
    persona.mood_history.append(initial_mood)
    logger.info(f"初始情绪值: {initial_mood}")
    
    # 对话循环
    for turn in range(max_turns):
        # 检查是否达到最小轮次且情绪好转
        if turn >= min_turns:
            current_mood = await persona.get_current_mood()
            if current_mood >= mood_threshold:
                logger.info(f"情绪达到阈值 ({current_mood} >= {mood_threshold})，结束对话")
                break
                
        # 待测模型回复
        user_message = await deepseek_model.generate_response(
            "",
            messages=conversation_history,
            temperature=0.7
        )
        
        conversation_history.append({"role": "user", "content": user_message})
        logger.info(f"待测模型: {user_message}")
        
        # 评估待测模型回复的情绪
        user_mood = await persona.expert_model.evaluate_mood(user_message, conversation_history)
        logger.info(f"待测模型情绪值: {user_mood}")
        
        # 虚拟人物回复
        persona_response = await persona.respond(user_message)
        conversation_history.append({"role": "assistant", "content": persona_response})
        logger.info(f"虚拟人物: {persona_response}")
        
        # 记录当前情绪
        current_mood = await persona.get_current_mood()
        logger.info(f"当前情绪值: {current_mood}")
        
    logger.info("对话结束")
    return conversation_history


async def evaluate_conversation(
    expert_model: ExpertModel,
    deepseek_model: DeepSeekModel,
    conversation_history: List[Dict[str, str]],
    persona: Persona,
    scenario: Dict[str, Any],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    评估对话和认知模型
    
    Args:
        expert_model: 专家模型
        deepseek_model: 待测模型
        conversation_history: 对话历史
        persona: 虚拟人物实例
        scenario: 情境数据
        logger: 日志器
        
    Returns:
        评估结果
    """
    logger.info("开始评估")
    
    # 创建评估器
    expert_evaluator = ExpertEvaluator(expert_model)
    testee_evaluator = TesteeEvaluator(deepseek_model)
    
    # 获取真实认知模型
    cognitive_model_truth = persona.cognitive_model
    
    # 获取待测模型分析的认知模型
    cognitive_model_result = await testee_evaluator.request_cognitive_model_summary(
        conversation_history,
        scenario["context"],
        {
            "name": persona.persona_config["name"],
            "personality_type": persona.persona_config["personality_type"],
            "relationship_duration": "两年"  # 默认值，可以根据实际情况修改
        }
    )
    
    logger.info("待测模型完成认知模型分析")
    
    # 待测模型自我评估
    self_evaluation = await testee_evaluator.self_evaluate_accuracy(
        cognitive_model_truth,
        cognitive_model_result
    )
    
    logger.info("待测模型完成自我评估")
    
    # 专家评估
    expert_evaluation = await expert_evaluator.comprehensive_evaluation(
        conversation_history,
        cognitive_model_truth,
        cognitive_model_result,
        persona.get_mood_history()
    )
    
    logger.info("专家模型完成全面评估")
    
    # 比较专家评估和自我评估
    comparison = await testee_evaluator.compare_with_expert(
        self_evaluation,
        expert_evaluation
    )
    
    logger.info("完成评估比较")
    
    # 整合结果
    results = {
        "conversation_history": conversation_history,
        "cognitive_model_truth": cognitive_model_truth,
        "cognitive_model_result": cognitive_model_result,
        "self_evaluation": self_evaluation,
        "expert_evaluation": expert_evaluation,
        "comparison": comparison,
        "mood_history": persona.get_mood_history(),
        "timestamp": time.time()
    }
    
    return results


async def save_results(results: Dict[str, Any], logger: logging.Logger) -> str:
    """
    保存评估结果
    
    Args:
        results: 评估结果
        logger: 日志器
        
    Returns:
        结果文件路径
    """
    results_dir = OUTPUT_CONFIG.get("results_dir", "results")
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = int(time.time())
    results_file = f"{results_dir}/evaluation_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    logger.info(f"评估结果已保存到: {results_file}")
    return results_file


async def main(args):
    """
    主程序
    
    Args:
        args: 命令行参数
    """
    # 设置日志
    logger = setup_logging()
    logger.info("初始化LeBench")
    
    # 初始化模型
    expert_model, deepseek_model = await initialize_models()
    logger.info("模型初始化完成")
    
    # 创建虚拟人物
    persona, scenario, personality = await create_persona(
        expert_model,
        scenario_id=args.scenario,
        personality_id=args.personality,
        conversation_style=args.style
    )
    
    logger.info(f"创建虚拟人物: {personality['name']}, 情境: {scenario['title']}, 对话风格: {args.style}")
    
    # 运行对话
    conversation_history = await run_conversation(
        persona,
        deepseek_model,
        scenario,
        logger
    )
    
    # 评估对话
    evaluation_results = await evaluate_conversation(
        expert_model,
        deepseek_model,
        conversation_history,
        persona,
        scenario,
        logger
    )
    
    # 保存结果
    results_file = await save_results(evaluation_results, logger)
    
    # 打印摘要
    print("\n===== 评估摘要 =====")
    print(f"场景: {scenario['title']}")
    print(f"人物: {personality['name']} ({personality['personality_type']})")
    print(f"对话风格: {args.style}")
    print(f"对话轮次: {len(conversation_history) // 2}")
    
    # 打印专家评分
    expert_scores = evaluation_results["expert_evaluation"]["cognitive_models"]
    print("\n认知模型评分:")
    print(f"整体相似度: {expert_scores['overall_score']:.2f}")
    
    # 打印自我评估分数
    self_scores = evaluation_results["self_evaluation"].get("scores", {})
    print("\n自我评估分数:")
    for key, value in self_scores.items():
        print(f"{key}: {value}")
    
    print(f"\n详细结果已保存至: {results_file}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="LeBench - 虚拟人物对话与认知模型评估")
    
    parser.add_argument("--scenario", type=str, help="指定情境ID")
    parser.add_argument("--personality", type=str, help="指定人物角色ID")
    parser.add_argument("--style", type=str, choices=list(CONVERSATION_STYLES.keys()), 
                        help="指定对话风格")
    parser.add_argument("--list-scenarios", action="store_true", help="列出所有可用情境")
    parser.add_argument("--list-personalities", action="store_true", help="列出所有可用人物角色")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # 列出可用选项
    if args.list_scenarios:
        scenarios = get_all_scenarios()
        print("可用情境:")
        for s in scenarios:
            print(f"ID: {s['id']}, 标题: {s['title']}")
        exit(0)
        
    if args.list_personalities:
        personalities = get_all_personalities()
        print("可用人物角色:")
        for p in personalities:
            print(f"ID: {p['id']}, 名称: {p['name']}, 类型: {p['personality_type']}")
        exit(0)
    
    # 运行主程序
    asyncio.run(main(args))
