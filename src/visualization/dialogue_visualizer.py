import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class DialogueVisualizer:
    """Dialogue visualization tool for visualizing dialogue results"""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize dialogue visualization tool
        
        Args:
            output_dir: Output directory, use default if None
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            # Default save to project's visualizations directory
            self.output_dir = Path(__file__).parent.parent.parent / "visualizations"
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set default style
        plt.style.use('seaborn-v0_8-darkgrid')
        self.character_color = "#3498db"  # Blue
        self.partner_color = "#e74c3c"    # Red
    
    def load_dialogue(self, dialogue_file: Union[str, Path]) -> Dict:
        """
        Load dialogue data
        
        Args:
            dialogue_file: Dialogue history file path
            
        Returns:
            Dialogue history data
        """
        dialogue_path = Path(dialogue_file)
        try:
            with open(dialogue_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load dialogue file: {e}")
            return {}
    
    def visualize_message_distribution(self, dialogue_history: List[Dict], title: str = "Message Distribution") -> str:
        """
        Visualize message distribution
        
        Args:
            dialogue_history: Dialogue history data
            title: Chart title
            
        Returns:
            Generated image file path
        """
        # Count messages by different senders
        character_count = len([msg for msg in dialogue_history if msg.get("sender") == "character"])
        partner_count = len([msg for msg in dialogue_history if msg.get("sender") == "partner"])
        
        # Create pie chart
        labels = ['Character', 'Partner']
        sizes = [character_count, partner_count]
        colors = [self.character_color, self.partner_color]
        explode = (0.1, 0)  # Emphasize character part
        
        plt.figure(figsize=(8, 6))
        plt.pie(
            sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90
        )
        plt.axis('equal')  # Ensure pie is circular
        plt.title(title)
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = self.output_dir / f"message_distribution_{timestamp}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Message distribution chart saved to: {output_file}")
        return str(output_file)
    
    def visualize_emotion_flow(self, dialogue_history: List[Dict], emotion_keys: List[str] = None) -> str:
        """
        Visualize emotion flow
        
        Args:
            dialogue_history: Dialogue history data
            emotion_keys: List of emotion keywords to visualize, default is None (use all emotions)
            
        Returns:
            Generated image file path
        """
        # Extract time points and emotion data
        time_points = []
        emotion_data = {}
        
        for idx, msg in enumerate(dialogue_history):
            time_points.append(idx + 1)  # Message number as time point
            
            # Extract emotion data
            emotions = msg.get("emotions", {})
            
            if not emotions:
                continue
                
            # If specific emotion keys are provided, only extract those emotions
            if emotion_keys:
                for key in emotion_keys:
                    if key in emotions:
                        if key not in emotion_data:
                            emotion_data[key] = []
                        # Ensure value is float
                        emotion_value = emotions[key]
                        if isinstance(emotion_value, dict):
                            # If value is a dictionary, extract the numerical value
                            # Assume the dictionary has a 'value' or 'score' key
                            if 'value' in emotion_value:
                                emotion_value = emotion_value['value']
                            elif 'score' in emotion_value:
                                emotion_value = emotion_value['score']
                            else:
                                # If no value is found, default to 0
                                emotion_value = 0
                        try:
                            # Convert to float
                            emotion_data[key].append(float(emotion_value))
                        except (ValueError, TypeError):
                            # If conversion fails, use 0
                            emotion_data[key].append(0)
                    else:
                        if key not in emotion_data:
                            emotion_data[key] = []
                        emotion_data[key].append(0)  # If no emotion, set to 0
            else:
                # Otherwise extract all emotions
                for key, value in emotions.items():
                    if key not in emotion_data:
                        emotion_data[key] = [0] * (idx)  # Fill missing data points
                    
                    # Ensure value is float
                    if isinstance(value, dict):
                        # If value is a dictionary, extract the numerical value
                        if 'value' in value:
                            value = value['value']
                        elif 'score' in value:
                            value = value['score']
                        else:
                            # If no value is found, default to 0
                            value = 0
                    
                    try:
                        # Convert to float
                        emotion_data[key].append(float(value))
                    except (ValueError, TypeError):
                        # If conversion fails, use 0
                        emotion_data[key].append(0)
        
        # If no emotion data, return empty
        if not emotion_data:
            logger.warning("No emotion data found, cannot generate emotion flow chart")
            return ""
        
        # Fill missing data points
        max_len = len(time_points)
        for key in emotion_data:
            if len(emotion_data[key]) < max_len:
                emotion_data[key].extend([emotion_data[key][-1]] * (max_len - len(emotion_data[key])))
        
        # Create line chart
        plt.figure(figsize=(10, 6))
        
        # Use different colors
        colors = list(mcolors.TABLEAU_COLORS.values())
        
        for i, (emotion, values) in enumerate(emotion_data.items()):
            plt.plot(
                time_points[:len(values)], 
                values, 
                marker='o', 
                linestyle='-', 
                color=colors[i % len(colors)],
                label=emotion
            )
        
        plt.xlabel('Message Number')
        plt.ylabel('Emotion Intensity')
        plt.title('Emotion Flow in Dialogue')
        plt.legend()
        plt.grid(True)
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = self.output_dir / f"emotion_flow_{timestamp}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Emotion flow chart saved to: {output_file}")
        return str(output_file)
    
    def visualize_message_length(self, dialogue_history: List[Dict]) -> str:
        """
        Visualize message length distribution
        
        Args:
            dialogue_history: Dialogue history data
            
        Returns:
            Generated image file path
        """
        # Extract message length data
        character_lengths = [len(msg.get("content", "")) for msg in dialogue_history if msg.get("sender") == "character"]
        partner_lengths = [len(msg.get("content", "")) for msg in dialogue_history if msg.get("sender") == "partner"]
        
        # Create bar chart
        plt.figure(figsize=(12, 6))
        
        # Set X axis range
        x_character = np.arange(len(character_lengths))
        x_partner = np.arange(len(partner_lengths))
        
        # Draw bar chart
        plt.bar(
            x_character, 
            character_lengths, 
            width=0.4, 
            alpha=0.8, 
            color=self.character_color,
            label='Character'
        )
        
        plt.bar(
            x_partner + 0.4, 
            partner_lengths, 
            width=0.4, 
            alpha=0.8, 
            color=self.partner_color,
            label='Partner'
        )
        
        # Set chart properties
        plt.xlabel('Message Number')
        plt.ylabel('Message Length (characters)')
        plt.title('Message Length Distribution in Dialogue')
        plt.legend()
        plt.grid(True)
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = self.output_dir / f"message_length_{timestamp}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Message length distribution chart saved to: {output_file}")
        return str(output_file)
    
    def visualize_dialogue_summary(self, dialogue_result: Dict) -> str:
        """
        Visualize dialogue summary information
        
        Args:
            dialogue_result: Dialogue result data
            
        Returns:
            Generated image file path
        """
        # Extract summary data
        summary = dialogue_result.get("summary", {})
        
        # Create chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Set title and basic information
        fig.suptitle(f"Dialogue Summary: {summary.get('character_name')} - {summary.get('scenario_title')}", fontsize=16)
        
        # Add text information
        text_info = [
            f"Dialogue ID: {dialogue_result.get('dialogue_id', 'N/A')}",
            f"Start Time: {dialogue_result.get('start_time', 'N/A')}",
            f"End Time: {dialogue_result.get('end_time', 'N/A')}",
            f"Total Turns: {dialogue_result.get('total_turns', 0)}",
            f"Total Messages: {summary.get('total_messages', 0)}",
            f"Character Messages: {summary.get('character_messages', 0)}",
            f"Partner Messages: {summary.get('partner_messages', 0)}",
        ]
        
        # Hide axes
        ax.axis('off')
        
        # Add text
        y_position = 0.9
        for line in text_info:
            ax.text(0.1, y_position, line, fontsize=12, transform=ax.transAxes)
            y_position -= 0.1
        
        # Add memory summary
        memory_summary = summary.get('memory_summary', 'No memory summary')
        ax.text(0.1, y_position, "Memory Summary:", fontsize=12, fontweight='bold', transform=ax.transAxes)
        y_position -= 0.05
        
        # Display long text in segments
        words = memory_summary.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= 80:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        for line in lines:
            ax.text(0.1, y_position, line, fontsize=10, transform=ax.transAxes)
            y_position -= 0.05
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = self.output_dir / f"dialogue_summary_{timestamp}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Dialogue summary chart saved to: {output_file}")
        return str(output_file)
    
    def generate_dialogue_report(self, dialogue_dir: Union[str, Path]) -> Dict:
        """
        Generate complete report for dialogue in specified directory
        
        Args:
            dialogue_dir: Dialogue directory
            
        Returns:
            Report information, including paths to all generated charts
        """
        dialogue_dir = Path(dialogue_dir)
        
        # Find dialogue result files
        result_file = dialogue_dir / "dialogue_result.json"
        history_file = dialogue_dir / "dialogue_history.json"
        
        if not result_file.exists() or not history_file.exists():
            logger.error(f"Dialogue directory {dialogue_dir} missing result file or history file")
            return {}
        
        # Load dialogue data
        dialogue_result = self.load_dialogue(result_file)
        dialogue_history = self.load_dialogue(history_file)
        
        if not dialogue_result or not dialogue_history:
            logger.error("Failed to load dialogue data")
            return {}
        
        # Generate report directory
        report_dir = self.output_dir / f"report_{dialogue_result.get('dialogue_id', 'unknown')}"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate various visualization charts
        report = {
            "dialogue_id": dialogue_result.get("dialogue_id", "unknown"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "visualizations": {}
        }
        
        # Message distribution
        report["visualizations"]["message_distribution"] = self.visualize_message_distribution(
            dialogue_history,
            title=f"Message Distribution: {dialogue_result.get('summary', {}).get('character_name', '')}"
        )
        
        # Emotion flow
        report["visualizations"]["emotion_flow"] = self.visualize_emotion_flow(dialogue_history)
        
        # Message length
        report["visualizations"]["message_length"] = self.visualize_message_length(dialogue_history)
        
        # Dialogue summary
        report["visualizations"]["dialogue_summary"] = self.visualize_dialogue_summary(dialogue_result)
        
        # Save report information
        report_file = report_dir / "report_info.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Complete report generated: {report_dir}")
        return report


# Test case
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create visualization tool
    visualizer = DialogueVisualizer()
    
    # Test path
    result_dir = Path(__file__).parent.parent.parent / "results" / "dialogues"
    
    # Find the latest dialogue directory
    dialogue_dirs = [d for d in result_dir.iterdir() if d.is_dir()]
    
    if not dialogue_dirs:
        logger.error("No dialogue directory found")
    else:
        # Sort by modification time, get the latest directory
        latest_dir = max(dialogue_dirs, key=lambda d: d.stat().st_mtime)
        logger.info(f"Using latest dialogue directory: {latest_dir}")
        
        # Generate report
        report = visualizer.generate_dialogue_report(latest_dir)
        
        if report:
            logger.info("Visualization report generated successfully")
            for k, v in report["visualizations"].items():
                logger.info(f"{k}: {v}")
 