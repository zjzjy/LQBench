#!/usr/bin/env python3

"""
Visualization script for emotion trajectories in dialogue logs
"""

import os
import json
import matplotlib.pyplot as plt
import numpy as np

def load_log_file(file_path):
    """Load a single log file and extract emotion data"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract emotion trajectory
    emotion_history = data.get("emotion_history", [])
    emotion_scores = []
    emotion_labels = []
    
    for entry in emotion_history:
        if "score" in entry:
            emotion_scores.append(entry["score"])
            
            # Get primary emotion
            emotions = entry.get("emotions", [])
            if emotions and isinstance(emotions, list):
                emotion_labels.append(emotions[0])
            else:
                emotion_labels.append("unknown")
    
    # Get character info
    character = data.get("character", {})
    character_name = character.get("name", "Unknown")
    character_id = character.get("id", "unknown")
    
    # Get scenario info
    scenario = data.get("scenario", {})
    situation = None
    
    if isinstance(scenario.get("situation"), dict):
        situation = scenario.get("situation", {}).get("name", "Unknown")
    else:
        situation = "Unknown"
    
    return {
        "emotion_scores": emotion_scores,
        "emotion_labels": emotion_labels,
        "character_id": character_id,
        "character_name": character_name,
        "situation": situation,
        "file_name": os.path.basename(file_path)
    }

def visualize_emotion_trajectories(log_dir):
    """Visualize emotion trajectories from all log files in directory"""
    # Get all JSON files (excluding prompts)
    log_files = []
    for file in os.listdir(log_dir):
        if file.endswith('.json') and 'prompts' not in file:
            log_files.append(os.path.join(log_dir, file))
    
    if not log_files:
        print(f"No log files found in {log_dir}")
        return
    
    # Load data from all files
    log_data = []
    for file_path in log_files:
        try:
            data = load_log_file(file_path)
            log_data.append(data)
        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
    
    # Create first figure for emotion trajectories
    plt.figure(figsize=(12, 6))
    
    # Plot each emotion trajectory
    for data in log_data:
        emotion_scores = data["emotion_scores"]
        turns = range(1, len(emotion_scores) + 1)
        situation = data["situation"]
        
        # Use different line styles for different character types
        if "high_emotional_needs" in data["character_id"]:
            line_style = 'o-'
            label = f"高情感需求 ({situation})"
        else:
            line_style = 's--'
            label = f"低情感需求 ({situation})"
        
        plt.plot(turns, emotion_scores, line_style, linewidth=2, label=label)
        
        # Add emotion labels
        for i, (turn, score, emotion) in enumerate(zip(turns, emotion_scores, data["emotion_labels"])):
            plt.annotate(emotion, (turn, score), 
                         textcoords="offset points", 
                         xytext=(0, 10), 
                         ha='center',
                         fontsize=8)
    
    # Add plot labels and legend
    plt.title("对话过程中的情绪轨迹分析", fontsize=16)
    plt.xlabel("对话轮次", fontsize=14)
    plt.ylabel("情绪分数", fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best')
    
    # Set y-axis limits with some padding
    all_scores = [score for data in log_data for score in data["emotion_scores"]]
    if all_scores:
        min_score = min(all_scores) - 1
        max_score = max(all_scores) + 1
        plt.ylim(min_score, max_score)
    
    # Add horizontal line at y=0
    plt.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    
    # Save figure
    output_path = os.path.join(log_dir, "emotion_trajectories.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Trajectory visualization saved to {output_path}")
    
    # Close the first figure
    plt.close()
    
    # Create second figure for emotional metrics comparison
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Prepare data for bar chart
    labels = []
    start_emotions = []
    final_emotions = []
    avg_emotions = []
    emotion_changes = []
    variances = []
    volatilities = []
    
    for data in log_data:
        if "high_emotional_needs" in data["character_id"]:
            label = f"高情感需求 ({data['situation']})"
        else:
            label = f"低情感需求 ({data['situation']})"
        
        # Calculate emotional metrics
        scores = data["emotion_scores"]
        if scores:
            start_emotion = scores[0]
            final_emotion = scores[-1]
            emotion_change = final_emotion - start_emotion
            avg_emotion = np.mean(scores)
            variance = np.var(scores) if len(scores) > 1 else 0
            
            # Calculate emotion volatility (average absolute change between turns)
            changes = [abs(scores[i] - scores[i-1]) for i in range(1, len(scores))]
            volatility = np.mean(changes) if changes else 0
        else:
            start_emotion = final_emotion = emotion_change = avg_emotion = variance = volatility = 0
        
        labels.append(label)
        start_emotions.append(start_emotion)
        final_emotions.append(final_emotion)
        avg_emotions.append(avg_emotion)
        emotion_changes.append(emotion_change)
        variances.append(variance)
        volatilities.append(volatility)
    
    # Set up positions for grouped bars
    x = np.arange(len(labels))
    width = 0.15
    
    # Plot emotional values
    ax1.bar(x - width*1.5, start_emotions, width, label='起始情绪', color='skyblue')
    ax1.bar(x - width*0.5, final_emotions, width, label='结束情绪', color='lightgreen')
    ax1.bar(x + width*0.5, avg_emotions, width, label='平均情绪', color='salmon')
    
    # Add labels and legend
    ax1.set_title('情绪值比较', fontsize=16)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.3)
    ax1.set_ylabel('情绪分数', fontsize=14)
    
    # Add a horizontal line at y=0
    ax1.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    
    # Plot emotional changes and variability metrics
    ax2.bar(x - width, emotion_changes, width, label='情绪变化 (结束-开始)', color='lightblue')
    ax2.bar(x, variances, width, label='情绪方差', color='lightcoral')
    ax2.bar(x + width, volatilities, width, label='情绪波动性', color='khaki')
    
    # Add labels and legend
    ax2.set_title('情绪变化指标', fontsize=16)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.3)
    ax2.set_ylabel('变化指标值', fontsize=14)
    
    # Save figure
    plt.tight_layout()
    metrics_output_path = os.path.join(log_dir, "emotion_metrics.png")
    plt.savefig(metrics_output_path, dpi=300, bbox_inches='tight')
    print(f"Metrics visualization saved to {metrics_output_path}")
    
    # Display the plots
    plt.show()

if __name__ == "__main__":
    import sys
    
    # Use logs_test directory by default
    log_dir = "logs_test"
    
    # Allow command line override
    if len(sys.argv) > 1:
        log_dir = sys.argv[1]
    
    visualize_emotion_trajectories(log_dir) 