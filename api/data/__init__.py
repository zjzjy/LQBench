"""
数据模块，包含虚拟人物定义和提示词模板
"""

# 导出数据模块中的所有类型
from LQBench.api.data.personality_types import personality_types
from LQBench.api.data.relationship_beliefs import relationship_beliefs
from LQBench.api.data.communication_types import communication_types
from LQBench.api.data.attachment_styles import attachment_styles
from LQBench.api.data.emotions import emotions, emotion_scoring
from LQBench.api.data.conflict_scenarios import conflict_scenarios
from LQBench.api.data.character_profiles import character_template, sample_characters, create_character_profile
from LQBench.api.data.prompt_templates import (
    character_prompt_template, 
    partner_prompt_template, 
    dialogue_analysis_template,
    emotion_assessment_template
) 