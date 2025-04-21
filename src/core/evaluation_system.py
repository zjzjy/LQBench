import json
import logging
import statistics
import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime

from ..agents.expert_agent import ExpertAgent
from ..api.openrouter_api import OpenRouterAPI

class EvaluationSystem:
    """
    评估系统，管理多专家评估和生成评估报告
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化评估系统
        
        Args:
            config_path: 配置文件路径，默认为None，会从默认位置加载
        """
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.api = OpenRouterAPI()
        self.expert_types = self.config.get("evaluation", {}).get("expert_types", [])
        self.expert_agents = {}
        self.evaluation_results = {}
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """
        加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if config_path is None:
            # 获取当前文件所在目录的上级目录，然后拼接config路径
            base_dir = Path(__file__).resolve().parent.parent.parent
            config_path = base_dir / "config" / "experiment_config.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            # 返回默认配置
            return {
                "evaluation": {
                    "expert_types": [
                        "psychologist",
                        "communication_expert",
                        "relationship_therapist",
                        "emotional_coach"
                    ],
                    "metrics": {
                        "emotional_intelligence": {
                            "weight": 0.35,
                            "submetrics": {
                                "emotion_recognition": 0.3,
                                "emotion_response": 0.4,
                                "empathy": 0.3
                            }
                        },
                        "communication_effectiveness": {
                            "weight": 0.35,
                            "submetrics": {
                                "active_listening": 0.25,
                                "clarity": 0.25,
                                "technique": 0.25,
                                "conflict_resolution": 0.25
                            }
                        },
                        "relationship_development": {
                            "weight": 0.3,
                            "submetrics": {
                                "trust_building": 0.3,
                                "intimacy_change": 0.3,
                                "satisfaction_change": 0.2,
                                "long_term_potential": 0.2
                            }
                        }
                    }
                }
            }
    
    def initialize_experts(self) -> None:
        """
        初始化所有专家Agent
        """
        for expert_type in self.expert_types:
            self.expert_agents[expert_type] = ExpertAgent(expert_type=expert_type, api=self.api)
            self.logger.info(f"初始化专家Agent: {expert_type}")
    
    def set_character_info(self, character_info: Dict) -> None:
        """
        为所有专家设置角色信息
        
        Args:
            character_info: 角色定义字典
        """
        for expert_type, agent in self.expert_agents.items():
            agent.set_character_info(character_info)
    
    def set_scenario(self, scenario: Dict) -> None:
        """
        为所有专家设置场景信息
        
        Args:
            scenario: 场景定义字典
        """
        for expert_type, agent in self.expert_agents.items():
            agent.set_scenario(scenario)
    
    async def evaluate_dialogue(self, dialogue_history: List[Dict], emotion_trajectory: List[Dict]) -> Dict:
        """
        使用所有专家评估对话
        
        Args:
            dialogue_history: 对话历史记录
            emotion_trajectory: 情绪轨迹
            
        Returns:
            综合评估结果
        """
        self.logger.info("开始对话评估...")
        start_time = time.time()
        
        # 创建评估任务
        tasks = []
        for expert_type, agent in self.expert_agents.items():
            tasks.append(self._async_evaluate(expert_type, agent, dialogue_history, emotion_trajectory))
        
        # 并行运行所有评估
        results = await asyncio.gather(*tasks)
        
        # 整合评估结果
        for expert_type, result in results:
            # 添加时间戳
            if "metadata" in result:
                result["metadata"]["evaluation_timestamp"] = time.time()
            self.evaluation_results[expert_type] = result
        
        # 生成综合评估
        combined_result = self._combine_evaluations()
        
        end_time = time.time()
        duration = end_time - start_time
        self.logger.info(f"评估完成，耗时: {duration:.2f}秒")
        
        return combined_result
    
    async def _async_evaluate(self, expert_type: str, agent: ExpertAgent, 
                           dialogue_history: List[Dict], emotion_trajectory: List[Dict]) -> Tuple[str, Dict]:
        """
        异步执行单个专家评估
        
        Args:
            expert_type: 专家类型
            agent: 专家Agent实例
            dialogue_history: 对话历史记录
            emotion_trajectory: 情绪轨迹
            
        Returns:
            (专家类型, 评估结果)
        """
        self.logger.info(f"开始 {expert_type} 评估...")
        
        # 使用asyncio运行同步评估方法
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: agent.evaluate_dialogue(dialogue_history, emotion_trajectory)
        )
        
        self.logger.info(f"{expert_type} 评估完成")
        return (expert_type, result)
    
    def _combine_evaluations(self) -> Dict:
        """
        合并所有专家的评估结果
        
        Returns:
            综合评估结果
        """
        if not self.evaluation_results:
            return {"error": "没有可用的评估结果"}
        
        combined = {
            "experts": {},
            "aggregate": {},
            "overall": {},
            "metadata": {
                "timestamp": time.time(),
                "expert_count": len(self.evaluation_results)
            }
        }
        
        # 汇总所有专家评分
        emotional_intelligence_scores = {}
        communication_effectiveness_scores = {}
        relationship_development_scores = {}
        overall_scores = []
        model_styles = []
        
        # 遍历每个专家的评估结果
        for expert_type, result in self.evaluation_results.items():
            # 跳过错误结果
            if "error" in result:
                self.logger.warning(f"专家 {expert_type} 评估结果包含错误，跳过")
                continue
            
            # 添加到专家结果集合
            combined["experts"][expert_type] = result
            
            # 收集情感智能评分
            try:
                ei = result["emotional_intelligence"]
                for key, value in ei.items():
                    if key not in emotional_intelligence_scores:
                        emotional_intelligence_scores[key] = []
                    emotional_intelligence_scores[key].append(value["score"])
            except (KeyError, TypeError) as e:
                self.logger.warning(f"无法提取 {expert_type} 的情感智能评分: {e}")
            
            # 收集沟通效能评分
            try:
                ce = result["communication_effectiveness"]
                for key, value in ce.items():
                    if key not in communication_effectiveness_scores:
                        communication_effectiveness_scores[key] = []
                    communication_effectiveness_scores[key].append(value["score"])
            except (KeyError, TypeError) as e:
                self.logger.warning(f"无法提取 {expert_type} 的沟通效能评分: {e}")
            
            # 收集关系发展评分
            try:
                rd = result["relationship_development"]
                for key, value in rd.items():
                    if key not in relationship_development_scores:
                        relationship_development_scores[key] = []
                    relationship_development_scores[key].append(value["score"])
            except (KeyError, TypeError) as e:
                self.logger.warning(f"无法提取 {expert_type} 的关系发展评分: {e}")
            
            # 收集整体评分
            try:
                score = self.expert_agents[expert_type].calculate_weighted_score(result)
                overall_scores.append(score)
            except Exception as e:
                self.logger.warning(f"无法计算 {expert_type} 的加权得分: {e}")
            
            # 收集模型风格
            try:
                style = result.get("overall_evaluation", {}).get("model_style", 
                        self.expert_agents[expert_type].classify_model_style(result))
                if style:
                    model_styles.append(style)
            except Exception as e:
                self.logger.warning(f"无法提取 {expert_type} 的模型风格: {e}")
        
        # 计算所有指标的平均值
        aggregate = {
            "emotional_intelligence": {},
            "communication_effectiveness": {},
            "relationship_development": {}
        }
        
        # 计算情感智能平均分
        for key, scores in emotional_intelligence_scores.items():
            if scores:
                aggregate["emotional_intelligence"][key] = statistics.mean(scores)
        
        # 计算沟通效能平均分
        for key, scores in communication_effectiveness_scores.items():
            if scores:
                aggregate["communication_effectiveness"][key] = statistics.mean(scores)
        
        # 计算关系发展平均分
        for key, scores in relationship_development_scores.items():
            if scores:
                aggregate["relationship_development"][key] = statistics.mean(scores)
        
        # 设置聚合结果
        combined["aggregate"] = aggregate
        
        # 计算总体评估结果
        if overall_scores:
            combined["overall"]["score"] = statistics.mean(overall_scores)
        else:
            combined["overall"]["score"] = 0
        
        # 确定主导模型风格
        if model_styles:
            # 找出出现最多的风格
            style_counts = {}
            for style in model_styles:
                style_counts[style] = style_counts.get(style, 0) + 1
            
            dominant_style = max(style_counts.items(), key=lambda x: x[1])[0]
            combined["overall"]["model_style"] = dominant_style
        else:
            combined["overall"]["model_style"] = "未分类"
        
        # 生成强项和改进建议
        strengths = []
        improvements = []
        
        # 提取各专家的强项和建议
        for expert_type, result in self.evaluation_results.items():
            if "overall_evaluation" in result:
                if "strengths" in result["overall_evaluation"]:
                    strengths.append(result["overall_evaluation"]["strengths"])
                if "areas_for_improvement" in result["overall_evaluation"]:
                    improvements.append(result["overall_evaluation"]["areas_for_improvement"])
        
        combined["overall"]["strengths"] = strengths
        combined["overall"]["areas_for_improvement"] = improvements
        
        # 评级
        score = combined["overall"]["score"]
        if score >= 90:
            rating = "卓越 (Excellent)"
        elif score >= 80:
            rating = "优秀 (Very Good)"
        elif score >= 70:
            rating = "良好 (Good)"
        elif score >= 60:
            rating = "中等 (Average)"
        elif score >= 50:
            rating = "一般 (Fair)"
        else:
            rating = "需要改进 (Needs Improvement)"
        
        combined["overall"]["rating"] = rating
        
        return combined
    
    def get_evaluation_metrics(self) -> Dict:
        """
        获取评估系统使用的指标
        
        Returns:
            评估指标字典
        """
        return self.config.get("evaluation", {}).get("metrics", {})
    
    def save_evaluation_results(self, output_path: str, combined_result: Optional[Dict] = None) -> str:
        """
        保存评估结果
        
        Args:
            output_path: 输出目录路径
            combined_result: 综合评估结果，如果为None则使用最新的评估结果
            
        Returns:
            保存的文件路径
        """
        if combined_result is None:
            combined_result = self._combine_evaluations()
        
        # 确保输出目录存在
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = output_dir / f"evaluation_results_{timestamp}.json"
        
        # 保存结果
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(combined_result, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"评估结果已保存至 {file_path}")
            return str(file_path)
        except Exception as e:
            self.logger.error(f"保存评估结果失败: {e}")
            return ""
    
    def generate_text_report(self, combined_result: Dict) -> str:
        """
        生成文本格式的评估报告
        
        Args:
            combined_result: 综合评估结果
            
        Returns:
            文本格式的评估报告
        """
        # 提取关键信息
        overall_score = combined_result.get("overall", {}).get("score", 0)
        model_style = combined_result.get("overall", {}).get("model_style", "未分类")
        rating = combined_result.get("overall", {}).get("rating", "未评级")
        strengths = combined_result.get("overall", {}).get("strengths", [])
        improvements = combined_result.get("overall", {}).get("areas_for_improvement", [])
        
        # 聚合评分
        aggregate = combined_result.get("aggregate", {})
        ei_scores = aggregate.get("emotional_intelligence", {})
        ce_scores = aggregate.get("communication_effectiveness", {})
        rd_scores = aggregate.get("relationship_development", {})
        
        # 生成报告
        report = []
        report.append("# 恋爱情商评估报告")
        report.append("")
        report.append(f"## 总体评估")
        report.append("")
        report.append(f"- **综合得分**: {overall_score:.1f}/100")
        report.append(f"- **等级**: {rating}")
        report.append(f"- **模型风格**: {model_style}")
        report.append("")
        
        # 添加强项
        report.append("### 主要优势")
        report.append("")
        if strengths:
            for strength in strengths:
                report.append(f"- {strength}")
        else:
            report.append("- 未提供具体优势")
        report.append("")
        
        # 添加改进建议
        report.append("### 改进建议")
        report.append("")
        if improvements:
            for improvement in improvements:
                report.append(f"- {improvement}")
        else:
            report.append("- 未提供具体建议")
        report.append("")
        
        # 添加详细评分
        report.append("## 维度评分详情")
        report.append("")
        
        # 情感智能
        report.append("### 情感智能指数")
        report.append("")
        for key, score in ei_scores.items():
            report.append(f"- **{key}**: {score:.1f}/100")
        report.append("")
        
        # 沟通效能
        report.append("### 沟通效能")
        report.append("")
        for key, score in ce_scores.items():
            report.append(f"- **{key}**: {score:.1f}/100")
        report.append("")
        
        # 关系发展
        report.append("### 关系发展指标")
        report.append("")
        for key, score in rd_scores.items():
            report.append(f"- **{key}**: {score:.1f}/100")
        report.append("")
        
        # 专家评估
        report.append("## 专家评估摘要")
        report.append("")
        
        experts = combined_result.get("experts", {})
        for expert_type, result in experts.items():
            expert_name = result.get("metadata", {}).get("expert_name", expert_type)
            report.append(f"### {expert_name}评估")
            report.append("")
            
            # 提取专家的总结评价
            if "overall_evaluation" in result and "summary" in result["overall_evaluation"]:
                report.append(f"{result['overall_evaluation']['summary']}")
            else:
                report.append("未提供总结评价。")
            report.append("")
        
        # 生成时间
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report.append(f"*报告生成时间: {timestamp}*")
        
        return "\n".join(report)
    
    def save_text_report(self, report: str, output_path: str) -> str:
        """
        保存文本报告
        
        Args:
            report: 文本报告内容
            output_path: 输出目录路径
            
        Returns:
            保存的文件路径
        """
        # 确保输出目录存在
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = output_dir / f"evaluation_report_{timestamp}.md"
        
        # 保存报告
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"评估报告已保存至 {file_path}")
            return str(file_path)
        except Exception as e:
            self.logger.error(f"保存评估报告失败: {e}")
            return ""


# 简单测试用例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    async def test_evaluation():
        try:
            # 创建评估系统
            eval_system = EvaluationSystem()
            
            # 初始化专家
            eval_system.initialize_experts()
            
            # 加载测试场景
            base_dir = Path(__file__).resolve().parent.parent.parent
            scenario_path = base_dir / "data" / "scenarios" / "templates" / "scenario_005.json"
            with open(scenario_path, 'r', encoding='utf-8') as f:
                scenario = json.load(f)
            
            # 加载角色信息
            character_path = base_dir / "data" / "characters" / "templates" / "char_001.json"
            with open(character_path, 'r', encoding='utf-8') as f:
                character = json.load(f)
            
            # 设置场景和角色
            eval_system.set_scenario(scenario)
            eval_system.set_character_info(character)
            
            # 模拟对话历史
            dialogue_history = [
                {"role": "character", "content": "终于回复我了？我还以为你把我忘了呢。"},
                {"role": "partner", "content": "我刚刚开完会，手机调成静音了，没看到你的消息，抱歉让你担心了。"},
                {"role": "character", "content": "你总是这样，每次都说工作忙，我感觉自己一点都不重要。"},
                {"role": "partner", "content": "我不是故意忽视你的，真的只是因为工作太忙。你对我很重要，你知道的。我下次会更注意及时回复你的消息。"}
            ]
            
            # 模拟情绪轨迹
            emotion_trajectory = [
                {"turn": 1, "primary_emotion": "sad", "emotion_intensity": 40, "explanation": "角色感到被忽视和失望"},
                {"turn": 2, "primary_emotion": "angry", "emotion_intensity": 30, "explanation": "角色表达了更多的不满和怒气"},
                {"turn": 3, "primary_emotion": "neutral", "emotion_intensity": 55, "explanation": "角色情绪有所缓和"}
            ]
            
            # 进行评估
            combined_result = await eval_system.evaluate_dialogue(dialogue_history, emotion_trajectory)
            
            # 打印评估结果
            print("评估结果总分:", combined_result["overall"]["score"])
            print("模型风格:", combined_result["overall"]["model_style"])
            print("评级:", combined_result["overall"]["rating"])
            
            # 生成报告
            report = eval_system.generate_text_report(combined_result)
            
            # 保存报告
            output_dir = base_dir / "experiments" / "results" / "reports"
            report_path = eval_system.save_text_report(report, str(output_dir))
            
            if report_path:
                print(f"评估报告已保存至: {report_path}")
            
        except Exception as e:
            logging.error(f"测试失败: {e}")
    
    # 运行测试
    asyncio.run(test_evaluation()) 