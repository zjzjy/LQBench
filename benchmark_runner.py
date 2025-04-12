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
    ):
        """
        初始化基准测试运行器
        
        参数:
            output_dir (str): 输出目录
            log_dir (str): 日志目录
            max_turns (int): 最大对话轮次
            character_api (str): 虚拟人物使用的API类型
            partner_api (str): 对话伴侣使用的API类型
        """
        self.output_dir = output_dir
        self.log_dir = log_dir
        self.max_turns = max_turns
        self.character_api = character_api
        self.partner_api = partner_api
        
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
            max_turns=self.max_turns,
            log_dir=self.log_dir
        )
        
        # 运行模拟
        try:
            result = simulator.run_simulation()
            
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
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "success": False,
                "error": str(e)
            }
            
            return summary
    
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
            "successful_tests": sum(1 for r in results if r.get("success", False)),
            "failed_tests": sum(1 for r in results if not r.get("success", False)),
            "total_runtime_seconds": total_time,
            "average_runtime_per_test": total_time / len(test_cases) if test_cases else 0,
            "results": results
        }
        
        # 保存结果报告
        report_file = os.path.join(
            self.output_dir, 
            f"benchmark_report_{int(time.time())}.json"
        )
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n基准测试完成")
        print(f"总测试用例: {report['total_test_cases']}")
        print(f"成功: {report['successful_tests']}")
        print(f"失败: {report['failed_tests']}")
        print(f"总运行时间: {report['total_runtime_seconds']:.2f} 秒")
        print(f"结果已保存到: {report_file}")
        
        # 分析结果
        self.analyze_results(results, os.path.splitext(report_file)[0])
        
        return report
    
    def analyze_results(self, results: List[Dict[str, Any]], output_prefix: str):
        """
        分析测试结果并生成报告和图表
        
        参数:
            results (List[Dict[str, Any]]): 测试结果列表
            output_prefix (str): 输出文件前缀
        """
        # 过滤出成功的测试
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            print("没有成功的测试结果可供分析")
            return
        
        # 转换为DataFrame
        df = pd.DataFrame(successful_results)
        
        # 保存CSV格式结果
        csv_file = f"{output_prefix}_results.csv"
        df.to_csv(csv_file, index=False)
        print(f"已保存CSV结果到: {csv_file}")
        
        # 生成图表
        self._generate_charts(df, output_prefix)
    
    def _generate_charts(self, df: pd.DataFrame, output_prefix: str):
        """生成结果分析图表"""
        # 1. 不同性格类型的情绪变化对比
        plt.figure(figsize=(10, 6))
        personality_avg = df.groupby("personality_type")["emotion_change"].mean().sort_values()
        plt.bar(personality_avg.index, personality_avg.values)
        plt.xlabel("性格类型", fontproperties=self.chinese_font)
        plt.ylabel("平均情绪变化", fontproperties=self.chinese_font)
        plt.title("不同性格类型的情绪变化对比", fontproperties=self.chinese_font)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_personality_comparison.png")
        
        # 2. 不同依恋类型的情绪变化对比
        plt.figure(figsize=(10, 6))
        attachment_avg = df.groupby("attachment_style")["emotion_change"].mean().sort_values()
        plt.bar(attachment_avg.index, attachment_avg.values)
        plt.xlabel("依恋类型", fontproperties=self.chinese_font)
        plt.ylabel("平均情绪变化", fontproperties=self.chinese_font)
        plt.title("不同依恋类型的情绪变化对比", fontproperties=self.chinese_font)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_attachment_comparison.png")
        
        # 3. 不同沟通方式的情绪变化对比
        plt.figure(figsize=(10, 6))
        communication_avg = df.groupby("communication_type")["emotion_change"].mean().sort_values()
        plt.bar(communication_avg.index, communication_avg.values)
        plt.xlabel("沟通方式", fontproperties=self.chinese_font)
        plt.ylabel("平均情绪变化", fontproperties=self.chinese_font)
        plt.title("不同沟通方式的情绪变化对比", fontproperties=self.chinese_font)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_communication_comparison.png")
        
        # 4. 不同关系信念的情绪变化对比
        plt.figure(figsize=(10, 6))
        belief_avg = df.groupby("relationship_belief")["emotion_change"].mean().sort_values()
        plt.bar(belief_avg.index, belief_avg.values)
        plt.xlabel("关系信念", fontproperties=self.chinese_font)
        plt.ylabel("平均情绪变化", fontproperties=self.chinese_font)
        plt.title("不同关系信念的情绪变化对比", fontproperties=self.chinese_font)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_belief_comparison.png")
        
        # 5. 不同冲突场景的情绪变化对比
        plt.figure(figsize=(12, 6))
        scenario_avg = df.groupby("scenario_id")["emotion_change"].mean().sort_values()
        plt.bar(scenario_avg.index, scenario_avg.values)
        plt.xlabel("冲突场景", fontproperties=self.chinese_font)
        plt.ylabel("平均情绪变化", fontproperties=self.chinese_font)
        plt.title("不同冲突场景的情绪变化对比", fontproperties=self.chinese_font)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_scenario_comparison.png")
        
        print(f"已生成分析图表到: {output_prefix}_*.png")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行情侣对话模拟基准测试")
    parser.add_argument("--num_characters", type=int, default=5, help="要生成的随机虚拟人物数量")
    parser.add_argument("--max_turns", type=int, default=10, help="每次对话的最大轮次")
    parser.add_argument("--output_dir", type=str, default="benchmark_results", help="输出目录")
    parser.add_argument("--log_dir", type=str, default="logs", help="日志目录")
    parser.add_argument("--character_api", type=str, default="deepseek", help="虚拟人物使用的API类型")
    parser.add_argument("--partner_api", type=str, default="openrouter", help="对话伴侣使用的API类型")
    parser.add_argument("--parallel", action="store_true", help="是否并行运行测试")
    parser.add_argument("--max_workers", type=int, default=4, help="并行运行时的最大工作线程数")
    parser.add_argument("--scenarios", type=str, nargs="+", help="要测试的场景ID列表")
    
    args = parser.parse_args()
    
    # 创建基准测试运行器
    benchmark = BenchmarkRunner(
        output_dir=args.output_dir,
        log_dir=args.log_dir,
        max_turns=args.max_turns,
        character_api=args.character_api,
        partner_api=args.partner_api
    )
    
    # 运行基准测试
    benchmark.run_benchmark(
        num_characters=args.num_characters,
        scenario_ids=args.scenarios,
        parallel=args.parallel,
        max_workers=args.max_workers
    )

if __name__ == "__main__":
    main() 