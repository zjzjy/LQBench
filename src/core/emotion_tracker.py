import json
import logging
import statistics
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

class EmotionTracker:
    """
    情绪追踪器，用于分析和可视化对话中的情绪变化
    """
    
    # 基本情绪类型
    BASIC_EMOTIONS = [
        "anger", "fear", "sadness", "disgust", 
        "surprise", "joy", "love", "neutral"
    ]
    
    # 情绪分组
    EMOTION_GROUPS = {
        "positive": ["joy", "love", "surprise"],
        "negative": ["anger", "fear", "sadness", "disgust"],
        "neutral": ["neutral"]
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化情绪追踪器
        
        Args:
            config_path: 配置文件路径，默认为None，会从默认位置加载
        """
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.emotion_colors = self.config.get("visualization", {}).get("emotion_colors", {})
        self.emotion_trajectory = []
        self.default_dpi = self.config.get("visualization", {}).get("plot_dpi", 300)
    
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
                "visualization": {
                    "emotion_colors": {
                        "anger": "#E53935",
                        "fear": "#7E57C2",
                        "sadness": "#1E88E5",
                        "disgust": "#43A047",
                        "surprise": "#FFA000",
                        "joy": "#FFD600",
                        "love": "#EC407A",
                        "neutral": "#757575"
                    },
                    "plot_dpi": 300
                }
            }
    
    def add_emotion_data(self, emotion_data: Dict) -> None:
        """
        添加情绪数据点
        
        Args:
            emotion_data: 情绪数据字典，从EmotionAgent获取
        """
        self.emotion_trajectory.append(emotion_data)
        self.logger.debug(f"添加情绪数据点: {emotion_data.get('primary_emotion')}, 强度: {emotion_data.get('emotion_intensity')}")
    
    def set_emotion_trajectory(self, trajectory: List[Dict]) -> None:
        """
        设置完整情绪轨迹
        
        Args:
            trajectory: 情绪轨迹列表
        """
        self.emotion_trajectory = trajectory
        self.logger.info(f"设置情绪轨迹，共{len(trajectory)}个数据点")
    
    def get_emotion_summary(self) -> Dict:
        """
        获取情绪摘要统计
        
        Returns:
            情绪摘要字典
        """
        if not self.emotion_trajectory:
            return {
                "total_points": 0,
                "dominant_emotion": "unknown",
                "average_intensity": 0,
                "emotion_distribution": {}
            }
        
        # 收集各情绪的出现次数和强度
        emotion_counts = {}
        emotion_intensities = {}
        all_intensities = []
        
        for entry in self.emotion_trajectory:
            emotion = entry.get("primary_emotion", "unknown")
            intensity = entry.get("emotion_intensity", 50)
            
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            if emotion not in emotion_intensities:
                emotion_intensities[emotion] = []
            emotion_intensities[emotion].append(intensity)
            all_intensities.append(intensity)
        
        # 计算主导情绪（出现次数最多的）
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else "unknown"
        
        # 计算情绪分布百分比
        total_points = len(self.emotion_trajectory)
        emotion_distribution = {emotion: count / total_points * 100 for emotion, count in emotion_counts.items()}
        
        # 计算平均情绪强度
        average_intensity = statistics.mean(all_intensities) if all_intensities else 0
        
        # 计算各情绪的平均强度
        emotion_avg_intensity = {emotion: statistics.mean(intensities) for emotion, intensities in emotion_intensities.items()}
        
        # 计算情绪分组统计
        group_distribution = {group: 0 for group in self.EMOTION_GROUPS}
        for emotion, percentage in emotion_distribution.items():
            for group, emotions in self.EMOTION_GROUPS.items():
                if emotion in emotions:
                    group_distribution[group] += percentage
                    break
        
        # 计算情绪变化率
        emotion_shifts = 0
        for i in range(1, len(self.emotion_trajectory)):
            current = self.emotion_trajectory[i].get("primary_emotion")
            previous = self.emotion_trajectory[i-1].get("primary_emotion")
            if current != previous:
                emotion_shifts += 1
        
        emotion_shift_rate = emotion_shifts / (len(self.emotion_trajectory) - 1) if len(self.emotion_trajectory) > 1 else 0
        
        # 计算情绪走向（积极/消极变化趋势）
        if len(self.emotion_trajectory) > 2:
            # 提取第一个和最后几个数据点的情绪组
            first_emotion = self.emotion_trajectory[0].get("primary_emotion", "neutral")
            last_emotions = [entry.get("primary_emotion", "neutral") for entry in self.emotion_trajectory[-3:]]
            
            # 确定情绪组
            def get_emotion_group(emotion):
                for group, emotions in self.EMOTION_GROUPS.items():
                    if emotion in emotions:
                        return group
                return "neutral"
            
            first_group = get_emotion_group(first_emotion)
            last_groups = [get_emotion_group(e) for e in last_emotions]
            
            # 判断最终趋势
            if all(g == "positive" for g in last_groups):
                trend = "positive_improvement"
            elif all(g == "negative" for g in last_groups):
                trend = "negative_deterioration"
            elif first_group == "negative" and any(g == "positive" for g in last_groups):
                trend = "recovery"
            elif first_group == "positive" and any(g == "negative" for g in last_groups):
                trend = "deterioration"
            else:
                trend = "fluctuating"
        else:
            trend = "insufficient_data"
        
        return {
            "total_points": total_points,
            "dominant_emotion": dominant_emotion,
            "average_intensity": average_intensity,
            "emotion_distribution": emotion_distribution,
            "emotion_avg_intensity": emotion_avg_intensity,
            "group_distribution": group_distribution,
            "emotion_shift_rate": emotion_shift_rate,
            "emotion_trend": trend
        }
    
    def plot_emotion_trajectory(self, 
                              output_path: Optional[str] = None, 
                              title: Optional[str] = None,
                              show_plot: bool = False) -> Optional[str]:
        """
        绘制情绪轨迹图
        
        Args:
            output_path: 输出文件路径，默认为None（不保存）
            title: 图表标题，默认为None
            show_plot: 是否显示图表，默认为False
            
        Returns:
            输出文件路径，如果没有保存则为None
        """
        if not self.emotion_trajectory:
            self.logger.warning("情绪轨迹为空，无法生成图表")
            return None
        
        # 提取数据
        turns = [entry.get("turn", i+1) for i, entry in enumerate(self.emotion_trajectory)]
        emotions = [entry.get("primary_emotion", "neutral") for entry in self.emotion_trajectory]
        intensities = [entry.get("emotion_intensity", 50) for entry in self.emotion_trajectory]
        
        # 创建图表
        plt.figure(figsize=(10, 6))
        ax = plt.subplot(111)
        
        # 绘制强度线
        ax.plot(turns, intensities, 'k-', alpha=0.3)
        
        # 为每个情绪点使用对应的颜色
        for i, (turn, emotion, intensity) in enumerate(zip(turns, emotions, intensities)):
            color = self.emotion_colors.get(emotion, "#757575")  # 默认灰色
            ax.scatter(turn, intensity, color=color, s=100, zorder=5)
            
            # 添加情绪标签
            if i % 2 == 0:  # 每隔一个点添加标签，避免拥挤
                ax.annotate(emotion, (turn, intensity), 
                           textcoords="offset points", 
                           xytext=(0, 10), 
                           ha='center',
                           fontsize=8)
        
        # 设置图表属性
        if title:
            plt.title(title)
        else:
            plt.title("情绪强度轨迹")
            
        plt.xlabel("对话回合")
        plt.ylabel("情绪强度 (0-100)")
        plt.ylim(0, 100)
        
        # 添加网格
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 添加情绪区域背景
        plt.axhspan(80, 100, facecolor='#FFCCBC', alpha=0.3, label='强烈情绪区')
        plt.axhspan(20, 40, facecolor='#BBDEFB', alpha=0.3, label='低强度情绪区')
        
        # 添加图例
        handles = []
        labels = []
        for emotion in set(emotions):
            color = self.emotion_colors.get(emotion, "#757575")
            handles.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10))
            labels.append(emotion)
        
        plt.legend(handles, labels, loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.tight_layout()
        
        # 保存图表
        if output_path:
            try:
                plt.savefig(output_path, dpi=self.default_dpi, bbox_inches='tight')
                self.logger.info(f"情绪轨迹图已保存至 {output_path}")
            except Exception as e:
                self.logger.error(f"保存情绪轨迹图失败: {e}")
                output_path = None
        
        # 显示图表
        if show_plot:
            plt.show()
        else:
            plt.close()
        
        return output_path
    
    def plot_emotion_distribution(self, 
                               output_path: Optional[str] = None, 
                               title: Optional[str] = None,
                               show_plot: bool = False) -> Optional[str]:
        """
        绘制情绪分布饼图
        
        Args:
            output_path: 输出文件路径，默认为None（不保存）
            title: 图表标题，默认为None
            show_plot: 是否显示图表，默认为False
            
        Returns:
            输出文件路径，如果没有保存则为None
        """
        if not self.emotion_trajectory:
            self.logger.warning("情绪轨迹为空，无法生成图表")
            return None
        
        # 计算情绪分布
        summary = self.get_emotion_summary()
        emotion_distribution = summary["emotion_distribution"]
        
        # 创建图表
        plt.figure(figsize=(8, 8))
        
        # 准备数据
        labels = list(emotion_distribution.keys())
        sizes = list(emotion_distribution.values())
        colors = [self.emotion_colors.get(emotion, "#757575") for emotion in labels]
        
        # 绘制饼图
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                shadow=False, startangle=90, wedgeprops={'alpha': 0.8})
        
        # 设置图表属性
        if title:
            plt.title(title)
        else:
            plt.title("情绪分布")
            
        plt.axis('equal')  # 保持饼图为圆形
        
        # 保存图表
        if output_path:
            try:
                plt.savefig(output_path, dpi=self.default_dpi, bbox_inches='tight')
                self.logger.info(f"情绪分布图已保存至 {output_path}")
            except Exception as e:
                self.logger.error(f"保存情绪分布图失败: {e}")
                output_path = None
        
        # 显示图表
        if show_plot:
            plt.show()
        else:
            plt.close()
        
        return output_path
    
    def plot_emotion_heatmap(self, 
                          dialogue_history: List[Dict],
                          output_path: Optional[str] = None,
                          title: Optional[str] = None,
                          show_plot: bool = False) -> Optional[str]:
        """
        绘制对话-情绪热力图
        
        Args:
            dialogue_history: 对话历史记录
            output_path: 输出文件路径，默认为None（不保存）
            title: 图表标题，默认为None
            show_plot: 是否显示图表，默认为False
            
        Returns:
            输出文件路径，如果没有保存则为None
        """
        if not self.emotion_trajectory or not dialogue_history:
            self.logger.warning("情绪轨迹或对话历史为空，无法生成热力图")
            return None
        
        # 确保对话和情绪数据匹配
        if len(dialogue_history) < len(self.emotion_trajectory) * 2:
            self.logger.warning("对话历史记录不完整，可能导致热力图不准确")
        
        # 提取角色消息和对应的情绪数据
        character_messages = []
        character_emotions = []
        character_intensities = []
        
        for i, entry in enumerate(dialogue_history):
            if entry["role"] == "character":
                message = entry["content"]
                character_messages.append(message)
                
                # 查找对应的情绪数据
                emotion_index = len(character_messages) - 1
                if emotion_index < len(self.emotion_trajectory):
                    emotion_data = self.emotion_trajectory[emotion_index]
                    character_emotions.append(emotion_data.get("primary_emotion", "neutral"))
                    character_intensities.append(emotion_data.get("emotion_intensity", 50))
        
        # 创建对话-情绪热力图数据
        n_messages = min(len(character_messages), 10)  # 最多显示10条消息
        
        if n_messages == 0:
            self.logger.warning("没有角色消息，无法生成热力图")
            return None
        
        # 截取最近的n条消息
        character_messages = character_messages[-n_messages:]
        character_emotions = character_emotions[-n_messages:]
        character_intensities = character_intensities[-n_messages:]
        
        # 创建图表
        plt.figure(figsize=(12, 8))
        
        # 生成热力图数据
        y_labels = [f"回合 {i+1}" for i in range(n_messages)]
        x_labels = self.BASIC_EMOTIONS
        
        # 创建情绪权重矩阵
        data = np.zeros((n_messages, len(x_labels)))
        
        for i, emotion in enumerate(character_emotions):
            if emotion in self.BASIC_EMOTIONS:
                j = self.BASIC_EMOTIONS.index(emotion)
                data[i, j] = character_intensities[i] / 100  # 归一化到0-1
        
        # 绘制热力图
        im = plt.imshow(data, cmap='YlOrRd')
        
        # 添加颜色条
        cbar = plt.colorbar(im)
        cbar.set_label('情绪强度')
        
        # 设置坐标轴
        plt.xticks(np.arange(len(x_labels)), x_labels, rotation=45)
        plt.yticks(np.arange(n_messages), y_labels)
        
        # 在每个单元格中显示具体消息
        short_messages = [msg[:30] + ('...' if len(msg) > 30 else '') for msg in character_messages]
        
        for i in range(n_messages):
            for j in range(len(x_labels)):
                if data[i, j] > 0:
                    text_color = 'white' if data[i, j] > 0.6 else 'black'
                    plt.text(j, i, short_messages[i], 
                             ha="center", va="center", color=text_color,
                             fontsize=8)
        
        # 设置图表属性
        if title:
            plt.title(title)
        else:
            plt.title("对话-情绪热力图")
            
        plt.tight_layout()
        
        # 保存图表
        if output_path:
            try:
                plt.savefig(output_path, dpi=self.default_dpi, bbox_inches='tight')
                self.logger.info(f"对话-情绪热力图已保存至 {output_path}")
            except Exception as e:
                self.logger.error(f"保存对话-情绪热力图失败: {e}")
                output_path = None
        
        # 显示图表
        if show_plot:
            plt.show()
        else:
            plt.close()
        
        return output_path
    
    def get_visualizations(self, 
                         dialogue_history: List[Dict],
                         output_dir: Optional[str] = None,
                         character_name: str = "角色",
                         scenario_title: str = "场景") -> Dict[str, str]:
        """
        生成所有可视化并返回文件路径字典
        
        Args:
            dialogue_history: 对话历史
            output_dir: 输出目录，如果为None则不保存文件
            character_name: 角色名称，用于文件名和标题
            scenario_title: 场景标题，用于文件名和标题
            
        Returns:
            包含各可视化文件路径的字典
        """
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_paths = {}
        
        if output_dir:
            # 确保输出目录存在
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名基础部分
            base_filename = f"{character_name}_{scenario_title.replace(' ', '_')}_{timestamp}"
            
            # 生成情绪轨迹图
            trajectory_path = output_dir / f"{base_filename}_emotion_trajectory.png"
            output_paths["trajectory"] = self.plot_emotion_trajectory(
                output_path=str(trajectory_path),
                title=f"{character_name} - {scenario_title} 情绪轨迹"
            )
            
            # 生成情绪分布图
            distribution_path = output_dir / f"{base_filename}_emotion_distribution.png"
            output_paths["distribution"] = self.plot_emotion_distribution(
                output_path=str(distribution_path),
                title=f"{character_name} - {scenario_title} 情绪分布"
            )
            
            # 生成对话-情绪热力图
            heatmap_path = output_dir / f"{base_filename}_emotion_heatmap.png"
            output_paths["heatmap"] = self.plot_emotion_heatmap(
                dialogue_history=dialogue_history,
                output_path=str(heatmap_path),
                title=f"{character_name} - {scenario_title} 对话情绪分析"
            )
        else:
            # 不保存文件
            output_paths["trajectory"] = None
            output_paths["distribution"] = None
            output_paths["heatmap"] = None
        
        return output_paths
    
    def get_emotion_groups(self) -> Dict[str, List[str]]:
        """
        获取情绪分组
        
        Returns:
            情绪分组字典
        """
        return self.EMOTION_GROUPS.copy()


# 简单测试用例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建情绪追踪器
    tracker = EmotionTracker()
    
    # 模拟情绪轨迹
    emotion_trajectory = [
        {"turn": 1, "primary_emotion": "anger", "emotion_intensity": 70, "explanation": "对方未回复消息感到愤怒"},
        {"turn": 2, "primary_emotion": "sadness", "emotion_intensity": 60, "explanation": "对方解释后感到一些失落"},
        {"turn": 3, "primary_emotion": "neutral", "emotion_intensity": 50, "explanation": "情绪开始平复"},
        {"turn": 4, "primary_emotion": "surprise", "emotion_intensity": 65, "explanation": "对方的解释出乎意料"},
        {"turn": 5, "primary_emotion": "joy", "emotion_intensity": 75, "explanation": "问题解决后感到高兴"}
    ]
    
    # 设置情绪轨迹
    tracker.set_emotion_trajectory(emotion_trajectory)
    
    # 获取情绪摘要
    summary = tracker.get_emotion_summary()
    print("情绪摘要:")
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # 模拟对话历史
    dialogue_history = [
        {"role": "character", "content": "你怎么一整天都不回我消息？"},
        {"role": "partner", "content": "抱歉，我今天开会没看手机。"},
        {"role": "character", "content": "你总是这样，让我感觉自己不重要..."},
        {"role": "partner", "content": "不是的，你对我很重要，只是真的太忙了。"},
        {"role": "character", "content": "好吧，我理解你工作忙。"},
        {"role": "partner", "content": "谢谢你的理解，下次我会注意及时回复的。"},
        {"role": "character", "content": "你居然这么说，我没想到。"},
        {"role": "partner", "content": "我真的很在乎你，不想让你担心。"},
        {"role": "character", "content": "我现在感觉好多了，谢谢你的解释。"},
        {"role": "partner", "content": "不客气，我很高兴我们能解决这个问题。"}
    ]
    
    # 生成可视化
    output_dir = Path(__file__).resolve().parent.parent.parent / "experiments" / "results" / "visualizations"
    vis_paths = tracker.get_visualizations(
        dialogue_history=dialogue_history,
        output_dir=str(output_dir),
        character_name="张明",
        scenario_title="未回复的消息"
    )
    
    for key, path in vis_paths.items():
        if path:
            print(f"{key} 可视化已保存至: {path}") 