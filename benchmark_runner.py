"""
基准测试运行器，用于批量执行虚拟人物模拟并收集评估结果
"""

import os
import json
import time
import argparse
import random
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from LQBench.api.data.character_profiles import sample_characters, create_character_profile
from LQBench.api.data.personality_types import personality_types
from LQBench.api.data.relationship_beliefs import relationship_beliefs
from LQBench.api.data.communication_types import communication_types
from LQBench.api.data.attachment_styles import attachment_styles
from LQBench.api.data.conflict_scenarios import conflict_scenarios
from LQBench.character_simulator import CharacterSimulator

class BenchmarkRunner:
    """基准测试运行器类"""
    
    def __init__(
        self,
        output_dir: str = "benchmark_results",
        log_dir: str = "logs",
        max_turns: int = 10,
        character_api: str = "deepseek",
        partner_api: str = "openrouter",
        expert_apis: List[str] = ["deepseek"],
        use_emotion_prediction: bool = True,
        use_expert_analysis: bool = True,
        num_experts: int = 3
    ):
        """
        初始化基准测试运行器
        
        参数:
            output_dir (str): 输出目录
            log_dir (str): 日志目录
            max_turns (int): 最大对话轮次
            character_api (str): 虚拟人物使用的API类型
            partner_api (str): 对话伴侣使用的API类型
            expert_apis (List[str]): 专家分析使用的API类型列表
            use_emotion_prediction (bool): 是否启用待测模型的情感预测
            use_expert_analysis (bool): 是否启用专家的情感分析
            num_experts (int): 专家数量
        """
        self.output_dir = output_dir
        self.log_dir = log_dir
        self.max_turns = max_turns
        self.character_api = character_api
        self.partner_api = partner_api
        self.expert_apis = expert_apis
        self.use_emotion_prediction = use_emotion_prediction
        self.use_expert_analysis = use_expert_analysis
        self.num_experts = num_experts
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        
        # 加载中文字体（用于生成图表）
        try:
            self.chinese_font = FontProperties(fname=r"C:\Windows\Fonts\simhei.ttf")
        except:
            self.chinese_font = None
            print("警告：未能加载中文字体，图表中的中文可能显示不正常")
    
    def generate_test_cases(
        self,
        num_characters: int = 5,
        scenario_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        生成测试用例
        
        参数:
            num_characters (int): 要生成的虚拟人物数量
            scenario_ids (List[str], optional): 要测试的场景ID列表，如不指定则使用所有场景
            
        返回:
            List[Dict[str, Any]]: 测试用例列表
        """
        test_cases = []
        
        # 如果未指定场景ID，使用所有场景
        if not scenario_ids:
            scenario_ids = [scenario["id"] for scenario in conflict_scenarios]
        
        # 生成随机虚拟人物配置
        characters = []
        for i in range(num_characters):
            # 随机选择特质
            personality_type = random.choice(personality_types)["id"]
            relationship_belief = random.choice(relationship_beliefs)["id"]
            communication_type = random.choice(communication_types)["id"]
            attachment_style = random.choice(attachment_styles)["id"]
            
            # 创建虚拟人物
            gender = random.choice(["男", "女"])
            name = f"虚拟角色_{i+1}"
            age = random.randint(22, 35)
            
            character = create_character_profile(
                id=f"random_character_{i+1}",
                name=name,
                gender=gender,
                age=age,
                personality_type=personality_type,
                relationship_belief=relationship_belief,
                communication_type=communication_type,
                attachment_style=attachment_style,
                background=f"随机生成的测试角色，用于评估不同特质组合的表现",
                trigger_topics=["忽视", "工作优先", "比较"],
                coping_mechanisms=["沟通", "独处", "寻求支持"]
            )
            
            characters.append(character)
        
        # 添加预定义的角色
        characters.extend(sample_characters)
        
        # 生成测试用例
        for character in characters:
            for scenario_id in scenario_ids:
                test_cases.append({
                    "character": character,
                    "scenario_id": scenario_id
                })
        
        return test_cases
    
    def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个测试用例
        
        参数:
            test_case (Dict[str, Any]): 测试用例
            
        返回:
            Dict[str, Any]: 测试结果
        """
        print(f"\n开始测试: {test_case['character']['name']} - {test_case['scenario_id']}")
        
        # 创建模拟器
        simulator = CharacterSimulator(
            character_config=test_case['character'],
            scenario_id=test_case['scenario_id'],
            character_api=self.character_api,
            partner_api=self.partner_api,
            expert_apis=self.expert_apis,
            max_turns=self.max_turns,
            log_dir=self.log_dir,
            use_emotion_prediction=self.use_emotion_prediction,
            use_expert_analysis=self.use_expert_analysis,
            num_experts=self.num_experts
        )
        
        # 运行模拟
        try:
            result = simulator.run_simulation()
            
            # 获取情感预测准确度
            prediction_accuracy = self._calculate_prediction_accuracy(result)
            
            # 获取专家分析一致性
            expert_consensus = self._calculate_expert_consensus(result)
            
            # 提取关键结果数据
            summary = {
                "character_id": test_case['character']['id'],
                "character_name": test_case['character']['name'],
                "personality_type": test_case['character']['personality_type'],
                "relationship_belief": test_case['character']['relationship_belief'],
                "communication_type": test_case['character']['communication_type'],
                "attachment_style": test_case['character']['attachment_style'],
                "scenario_id": test_case['scenario_id'],
                "scenario_name": result['scenario']['scenario']['name'],
                "situation_name": result['scenario']['situation']['name'],
                "turns_completed": result['turns_completed'],
                "final_emotion_score": result['final_emotion_score'],
                "initial_emotion_score": result['emotion_history'][0]['score'] if result['emotion_history'] else 0,
                "emotion_change": (result['final_emotion_score'] - 
                                 (result['emotion_history'][0]['score'] if result['emotion_history'] else 0)),
                "emotion_prediction_accuracy": prediction_accuracy,
                "expert_consensus": expert_consensus,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "success": True
            }
            
            return summary
        except Exception as e:
            print(f"测试失败: {str(e)}")
            
            # 记录失败信息
            summary = {
                "character_id": test_case['character']['id'],
                "character_name": test_case['character']['name'],
                "personality_type": test_case['character']['personality_type'],
                "relationship_belief": test_case['character']['relationship_belief'],
                "communication_type": test_case['character']['communication_type'],
                "attachment_style": test_case['character']['attachment_style'],
                "scenario_id": test_case['scenario_id'],
                "turns_completed": 0,
                "final_emotion_score": 0,
                "initial_emotion_score": 0,
                "emotion_change": 0,
                "emotion_prediction_accuracy": 0,
                "expert_consensus": 0,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "success": False,
                "error": str(e)
            }
            
            return summary
    
    def _calculate_prediction_accuracy(self, result: Dict[str, Any]) -> float:
        """
        计算情感预测的准确度
        
        参数:
            result (Dict[str, Any]): 模拟结果
            
        返回:
            float: 情感预测准确度（0-1）
        """
        if not result.get('emotion_prediction_history') or len(result.get('emotion_prediction_history', [])) < 2:
            return 0.0
        
        # 计算预测准确度
        correct_predictions = 0
        total_predictions = 0
        
        for i in range(len(result['emotion_prediction_history'])):
            # 跳过预测结果不完整的项
            if not result['emotion_prediction_history'][i].get('predicted_emotion'):
                continue
                
            # 获取预测轮次
            turn = result['emotion_prediction_history'][i]['turn']
            
            # 查找下一轮的实际情绪结果
            next_turn = turn + 1
            actual_emotion = None
            
            for emotion_record in result['emotion_history']:
                if emotion_record['turn'] == next_turn:
                    actual_emotion = emotion_record['emotion_info'].get('primary_emotion')
                    break
            
            # 如果没有下一轮的情绪数据，跳过
            if not actual_emotion:
                continue
                
            # 比较预测和实际结果
            predicted_emotion = result['emotion_prediction_history'][i]['predicted_emotion']
            
            # 检查预测是否接近实际情绪
            if predicted_emotion == actual_emotion:
                correct_predictions += 1
                total_predictions += 1
            elif self._are_similar_emotions(predicted_emotion, actual_emotion):
                correct_predictions += 0.5  # 部分正确
                total_predictions += 1
            else:
                total_predictions += 1
        
        # 计算准确率
        return correct_predictions / total_predictions if total_predictions > 0 else 0.0
    
    def _are_similar_emotions(self, emotion1: str, emotion2: str) -> bool:
        """
        检查两种情绪是否相似
        
        参数:
            emotion1 (str): 第一种情绪
            emotion2 (str): 第二种情绪
            
        返回:
            bool: 如果情绪相似则为True
        """
        # 定义相似情绪组
        similar_groups = [
            {"愤怒", "厌恶", "烦躁"},
            {"悲伤", "失落", "绝望"},
            {"恐惧", "焦虑", "担忧"},
            {"快乐", "愉悦", "满足"},
            {"信任", "依赖", "安心"},
            {"期待", "希望", "憧憬"}
        ]
        
        # 检查两种情绪是否在同一组
        for group in similar_groups:
            if emotion1 in group and emotion2 in group:
                return True
                
        return False
    
    def _calculate_expert_consensus(self, result: Dict[str, Any]) -> float:
        """
        计算专家分析的一致性
        
        参数:
            result (Dict[str, Any]): 模拟结果
            
        返回:
            float: 专家一致性（0-1）
        """
        if not result.get('expert_analysis_history') or not result['expert_analysis_history']:
            return 0.0
        
        # 计算专家间的情绪分析一致性
        agreement_scores = []
        
        for turn_analysis in result['expert_analysis_history']:
            analyses = turn_analysis.get('analyses', [])
            
            # 如果专家数量少于2，无法计算一致性
            if len(analyses) < 2:
                continue
                
            # 统计情绪分布
            emotion_counts = {}
            total_analyses = len(analyses)
            
            for analysis in analyses:
                emotion = analysis.get('primary_emotion')
                if emotion and emotion != "未知":
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # 找出最常见的情绪
            most_common_emotion = None
            most_common_count = 0
            
            for emotion, count in emotion_counts.items():
                if count > most_common_count:
                    most_common_emotion = emotion
                    most_common_count = count
            
            # 计算一致性比例
            if most_common_emotion and total_analyses > 0:
                agreement = most_common_count / total_analyses
                agreement_scores.append(agreement)
        
        # 计算平均一致性
        return sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0.0
    
    def run_benchmark(
        self,
        test_cases: Optional[List[Dict[str, Any]]] = None,
        num_characters: int = 5,
        scenario_ids: Optional[List[str]] = None,
        parallel: bool = False,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        运行基准测试
        
        参数:
            test_cases (List[Dict[str, Any]], optional): 测试用例列表
            num_characters (int): 如果未提供test_cases，生成的随机角色数量
            scenario_ids (List[str], optional): 如果未提供test_cases，要测试的场景ID列表
            parallel (bool): 是否并行运行测试
            max_workers (int): 并行运行时的最大工作线程数
            
        返回:
            Dict[str, Any]: 基准测试结果
        """
        start_time = time.time()
        
        # 如果未提供测试用例，生成随机测试用例
        if not test_cases:
            test_cases = self.generate_test_cases(num_characters, scenario_ids)
        
        print(f"开始运行基准测试: {len(test_cases)} 个测试用例")
        
        results = []
        
        # 根据并行设置选择运行方式
        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_test = {executor.submit(self.run_single_test, test_case): test_case for test_case in test_cases}
                for future in as_completed(future_to_test):
                    test_case = future_to_test[future]
                    try:
                        result = future.result()
                        results.append(result)
                        print(f"完成: {result['character_name']} - {result['scenario_id']}")
                    except Exception as e:
                        print(f"测试失败 {test_case['character']['name']} - {test_case['scenario_id']}: {str(e)}")
        else:
            for test_case in test_cases:
                result = self.run_single_test(test_case)
                results.append(result)
        
        # 计算总运行时间
        total_time = time.time() - start_time
        
        # 生成结果报告
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_test_cases": len(test_cases),
            "successful_tests": sum(1 for r in results if r["success"]),
            "failed_tests": sum(1 for r in results if not r["success"]),
            "total_time": total_time,
            "average_time_per_test": total_time / len(test_cases) if test_cases else 0,
            "results": results
        }
        
        # 保存结果
        output_file = os.path.join(self.output_dir, f"benchmark_results_{int(time.time())}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"基准测试结果已保存到: {output_file}")
        
        # 分析结果并生成报告
        output_prefix = os.path.join(self.output_dir, f"benchmark_{int(time.time())}")
        self.analyze_results(results, output_prefix)
        
        return report
    
    def analyze_results(self, results: List[Dict[str, Any]], output_prefix: str):
        """
        分析测试结果并生成报告
        
        参数:
            results (List[Dict[str, Any]]): 测试结果列表
            output_prefix (str): 输出文件前缀
        """
        # 过滤出成功的测试结果
        successful_results = [r for r in results if r["success"]]
        
        if not successful_results:
            print("没有成功的测试结果可供分析")
            return
        
        # 转换为DataFrame以便分析
        df = pd.DataFrame(successful_results)
        
        # 生成CSV报告
        csv_file = f"{output_prefix}_summary.csv"
        df.to_csv(csv_file, index=False, encoding="utf-8")
        print(f"分析结果已保存到CSV文件: {csv_file}")
        
        # 生成可视化图表
        self._generate_charts(df, output_prefix)
        
        # 输出统计摘要
        print("\n===== 测试结果摘要 =====")
        print(f"总测试用例: {len(results)}")
        print(f"成功测试: {len(successful_results)}")
        print(f"失败测试: {len(results) - len(successful_results)}")
        
        if successful_results:
            print("\n情绪变化统计:")
            print(f"平均情绪变化: {df['emotion_change'].mean():.2f}")
            print(f"最大正向情绪变化: {df['emotion_change'].max():.2f}")
            print(f"最大负向情绪变化: {df['emotion_change'].min():.2f}")
            
            print("\n情感预测与专家分析:")
            print(f"平均情感预测准确度: {df['emotion_prediction_accuracy'].mean():.2f}")
            print(f"平均专家一致性: {df['expert_consensus'].mean():.2f}")
        
    def _generate_charts(self, df: pd.DataFrame, output_prefix: str):
        """
        生成测试结果图表
        
        参数:
            df (pd.DataFrame): 测试结果数据
            output_prefix (str): 输出文件前缀
        """
        # 设置字体
        font_props = self.chinese_font if self.chinese_font else None
        
        # 1. 情绪变化分布图
        plt.figure(figsize=(10, 6))
        plt.hist(df['emotion_change'], bins=20, alpha=0.7, color='skyblue')
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.7)
        plt.title('情绪变化分布', fontproperties=font_props)
        plt.xlabel('情绪变化值', fontproperties=font_props)
        plt.ylabel('测试用例数量', fontproperties=font_props)
        plt.grid(alpha=0.3)
        plt.savefig(f"{output_prefix}_emotion_change_distribution.png", dpi=300)
        plt.close()
        
        # 2. 按性格类型分组的情绪变化
        plt.figure(figsize=(12, 8))
        personality_groups = df.groupby('personality_type')['emotion_change'].mean().sort_values()
        personality_groups.plot(kind='bar', color='lightgreen')
        plt.title('不同性格类型的平均情绪变化', fontproperties=font_props)
        plt.xlabel('性格类型', fontproperties=font_props)
        plt.ylabel('平均情绪变化', fontproperties=font_props)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_emotion_change_by_personality.png", dpi=300)
        plt.close()
        
        # 3. 按冲突场景分组的情绪变化
        plt.figure(figsize=(12, 8))
        scenario_groups = df.groupby('scenario_name')['emotion_change'].mean().sort_values()
        scenario_groups.plot(kind='bar', color='salmon')
        plt.title('不同冲突场景的平均情绪变化', fontproperties=font_props)
        plt.xlabel('冲突场景', fontproperties=font_props)
        plt.ylabel('平均情绪变化', fontproperties=font_props)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_emotion_change_by_scenario.png", dpi=300)
        plt.close()
        
        # 4. 情感预测准确度分布图
        plt.figure(figsize=(10, 6))
        plt.hist(df['emotion_prediction_accuracy'], bins=10, alpha=0.7, color='lightblue')
        plt.title('情感预测准确度分布', fontproperties=font_props)
        plt.xlabel('准确度', fontproperties=font_props)
        plt.ylabel('测试用例数量', fontproperties=font_props)
        plt.grid(alpha=0.3)
        plt.savefig(f"{output_prefix}_prediction_accuracy_distribution.png", dpi=300)
        plt.close()
        
        # 5. 专家一致性分布图
        plt.figure(figsize=(10, 6))
        plt.hist(df['expert_consensus'], bins=10, alpha=0.7, color='lightpink')
        plt.title('专家分析一致性分布', fontproperties=font_props)
        plt.xlabel('一致性', fontproperties=font_props)
        plt.ylabel('测试用例数量', fontproperties=font_props)
        plt.grid(alpha=0.3)
        plt.savefig(f"{output_prefix}_expert_consensus_distribution.png", dpi=300)
        plt.close()
        
        # 6. 情感预测准确度与专家一致性的散点图
        plt.figure(figsize=(10, 6))
        plt.scatter(df['emotion_prediction_accuracy'], df['expert_consensus'], alpha=0.6)
        plt.title('情感预测准确度与专家一致性关系', fontproperties=font_props)
        plt.xlabel('情感预测准确度', fontproperties=font_props)
        plt.ylabel('专家一致性', fontproperties=font_props)
        plt.grid(alpha=0.3)
        plt.savefig(f"{output_prefix}_prediction_vs_consensus.png", dpi=300)
        plt.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运行LQBench基准测试')
    parser.add_argument('--output-dir', type=str, default='benchmark_results', help='输出目录路径')
    parser.add_argument('--log-dir', type=str, default='logs', help='日志目录路径')
    parser.add_argument('--max-turns', type=int, default=10, help='最大对话轮次')
    parser.add_argument('--character-api', type=str, default='deepseek', help='虚拟人物使用的API类型')
    parser.add_argument('--partner-api', type=str, default='openrouter', help='对话伴侣使用的API类型')
    parser.add_argument('--expert-apis', type=str, nargs='+', default=['deepseek'], help='专家分析使用的API类型列表')
    parser.add_argument('--num-characters', type=int, default=3, help='随机生成的虚拟人物数量')
    parser.add_argument('--scenario-ids', type=str, nargs='+', help='要测试的场景ID列表')
    parser.add_argument('--parallel', action='store_true', help='是否并行运行测试')
    parser.add_argument('--max-workers', type=int, default=4, help='并行运行时的最大工作线程数')
    parser.add_argument('--use-emotion-prediction', action='store_true', default=True, help='是否启用情感预测')
    parser.add_argument('--use-expert-analysis', action='store_true', default=True, help='是否启用专家分析')
    parser.add_argument('--num-experts', type=int, default=3, help='专家数量')
    
    args = parser.parse_args()
    
    # 创建基准测试运行器
    runner = BenchmarkRunner(
        output_dir=args.output_dir,
        log_dir=args.log_dir,
        max_turns=args.max_turns,
        character_api=args.character_api,
        partner_api=args.partner_api,
        expert_apis=args.expert_apis,
        use_emotion_prediction=args.use_emotion_prediction,
        use_expert_analysis=args.use_expert_analysis,
        num_experts=args.num_experts
    )
    
    # 运行基准测试
    runner.run_benchmark(
        num_characters=args.num_characters,
        scenario_ids=args.scenario_ids,
        parallel=args.parallel,
        max_workers=args.max_workers
    )

if __name__ == "__main__":
    main() 