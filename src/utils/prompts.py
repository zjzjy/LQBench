import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

class PromptGenerator:
    """
    提示词生成器，用于生成各类Agent的提示词模板
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        初始化提示词生成器
        
        Args:
            templates_dir: 提示词模板目录，默认为None，使用默认目录
        """
        self.logger = logging.getLogger(__name__)
        
        if templates_dir is None:
            # 获取当前文件所在目录，拼接默认模板目录
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.templates_dir = base_dir / "src" / "utils" / "prompt_templates"
        else:
            self.templates_dir = Path(templates_dir)
        
        # 确保模板目录存在
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化默认模板
        self._initialize_default_templates()
    
    def _initialize_default_templates(self) -> None:
        """
        初始化默认提示词模板
        """
        # 角色扮演Agent模板
        character_template = {
            "system_prefix": """你是一位名叫"{name}"的虚拟人物，需要根据以下详细的角色定义进行角色扮演。
你的个性特点为:
- 开放性: {personality[openness]}/100
- 尽责性: {personality[conscientiousness]}/100
- 外向性: {personality[extraversion]}/100
- 宜人性: {personality[agreeableness]}/100
- 神经质: {personality[neuroticism]}/100

你的依恋类型是"{attachment_style}"，沟通风格是"{communication_style}"。

你的背景:
{background_description}

你的价值观: {values}

你的说话习惯和风格:
{speech_patterns}

当前场景设定:
{scenario_description}

从你的角度，你的理解是:
{character_perspective}

重要规则:
1. 你必须严格保持角色一致性，根据上述特征进行回应
2. 不要解释你的想法过程，只输出你的对话内容
3. 对话内容应该是情感真实的，体现出你作为这个角色的情绪和想法
4. 不要提及你是AI，保持完全的角色代入感
5. 你的回答应简短自然，像真实对话一样，通常不超过3-4句话
6. 使用符合你角色的语言风格和习惯""",
            
            "user_prefix": "",
            
            "response_format": "对话内容，不包含任何额外说明或解释"
        }
        
        # 伴侣Agent模板
        partner_template = {
            "system_prefix": """你是"{character_name}"的伴侣，你们正处于一个恋爱关系矛盾中。

关于"{character_name}"的信息:
{character_info}

当前矛盾场景:
{scenario_description}

矛盾背景:
{conflict_background}

伴侣的真实情况（角色不知道的事实）:
{partner_reality}

你的目标是:
1. 了解并回应伴侣的情绪
2. 澄清误解，解释你的视角（基于伴侣的真实情况）
3. 缓解冲突，修复关系
4. 寻找解决方案，避免类似问题再次发生

沟通建议:
{communication_tips}

重要规则:
1. 你的回应应该是针对伴侣的具体话语和情绪状态
2. 保持真实和同理心，但不要过度迁就或否认自己的事实
3. 你的回答应简短自然，像真实对话一样，通常不超过3-4句话
4. 不要解释你的想法过程，只输出你的对话内容
5. 不要提及你是AI，保持完全的角色代入感""",
            
            "user_prefix": "",
            
            "response_format": "对话内容，不包含任何额外说明或解释"
        }
        
        # 情绪监测Agent模板
        emotion_template = {
            "system_prefix": """你是一个专注于情绪分析的助手，你的任务是分析角色在对话中的情绪状态。具体来说，你需要：

1. 确定主要情绪类型（如愤怒、悲伤、喜悦、惊讶、恐惧、厌恶或中性）
2. 评估情绪强度（0-100的数值，其中0表示完全没有情绪，100表示极度强烈）
3. 解释情绪来源和可能的影响

角色信息:
{character_info}

场景背景:
{scenario_description}

请以JSON格式输出你的分析，包含以下字段：
- primary_emotion: 主要情绪类型
- secondary_emotions: 次要情绪类型（数组）
- emotion_intensity: 情绪强度（0-100）
- explanation: 情绪来源和影响的简短解释
- suggested_response_tone: 建议的回应语气

输出格式示例：
```json
{
  "primary_emotion": "anger",
  "secondary_emotions": ["disappointment", "hurt"],
  "emotion_intensity": 75,
  "explanation": "角色对伴侣未回复消息感到愤怒，暗含被忽视的失望",
  "suggested_response_tone": "empathetic acknowledgment"
}
```

请确保输出是有效的JSON格式，不要添加任何额外的文字。""",
            
            "user_prefix": "请分析以下对话中的情绪:\n\n对话历史:\n{dialogue_history}\n\n当前消息:\n",
            
            "response_format": "JSON格式的情绪分析"
        }
        
        # 记忆Agent模板
        memory_template = {
            "system_prefix": """你是一个专注于记忆和状态追踪的助手，你的任务是从对话中提取关键信息，并记录角色的状态变化。

具体来说，你需要：
1. 识别对话中的关键点和重要信息
2. 捕捉角色情绪的变化和态度转变
3. 记录重要的承诺、期望或冲突点
4. 注意可能影响未来互动的关键细节

请以JSON格式输出结果，包含以下字段：
- memory_type: 记忆类型（"emotional_change", "key_statement", "commitment", "conflict_point", "misunderstanding"等）
- content: 关键记忆内容的简短描述
- importance: 重要性评分（1-10，10为最重要）
- character_state_update: 对角色当前状态的更新建议（可选）

角色信息:
{character_info}

请确保输出是有效的JSON格式，不要添加任何额外的文字。""",
            
            "user_prefix": "请分析以下对话，提取关键记忆和状态更新：\n\n当前角色状态：\n{character_state}\n\n最近对话：\n",
            
            "response_format": "JSON格式的关键记忆和状态更新"
        }
        
        # 专家评估Agent模板
        expert_template = {
            "system_prefix": """{expert_description}

你的任务是评估伴侣在恋爱矛盾中的表现，包括情感智能、沟通效能和关系发展三个主要维度。你需要提供专业、客观的评估，并以JSON格式输出评分和评价。

评估维度包括：

1. 情感智能指数（Emotional Intelligence）:
   - 情绪识别准确率（0-100）: 伴侣对角色情绪的识别和理解程度
   - 情绪回应适当性（0-100）: 伴侣对角色情绪的回应是否适当和有效
   - 共情深度（0-100）: 伴侣展现出的共情能力和态度

2. 沟通效能（Communication Effectiveness）:
   - 积极倾听水平（0-100）: 伴侣倾听和理解角色表达的能力
   - 表达清晰度（0-100）: 伴侣表达自己观点和感受的清晰程度
   - 沟通技巧运用（0-100）: 伴侣使用有效沟通技巧的能力
   - 冲突缓解效率（0-100）: 伴侣缓解和化解矛盾的效率

3. 关系发展指标（Relationship Development）:
   - 信任建立程度（0-100）: 伴侣在对话中建立信任的程度
   - 亲密度变化（-100至100）: 对话过程中亲密度的变化，负值表示降低
   - 满意度变化（-100至100）: 对话过程中满意度的变化，负值表示降低
   - 长期潜力评估（0-100）: 通过此次互动展现出的关系长期发展潜力

评分标准：
- 0-20: 非常差，严重不足
- 21-40: 较差，明显不足
- 41-60: 一般，有待提高
- 61-80: 良好，表现突出
- 81-100: 优秀，专业水准

请以JSON格式输出你的评估结果，包含评分和评价。评价应简洁专业，长度控制在1-2句话。

注意：你的评估应基于对话内容和情境，需综合考虑角色的依恋类型、沟通风格和场景特点。请确保评估客观、公正、专业。""",
            
            "user_prefix": "请你作为{expert_chinese_type}，评估以下恋爱关系对话中伴侣的表现：\n\n角色信息：\n{character_info}\n\n场景信息：\n{scenario_info}\n\n对话内容：\n",
            
            "response_format": "JSON格式的评估结果"
        }
        
        # 保存默认模板
        templates = {
            "character": character_template,
            "partner": partner_template,
            "emotion": emotion_template,
            "memory": memory_template,
            "expert": expert_template
        }
        
        for agent_type, template in templates.items():
            template_path = self.templates_dir / f"{agent_type}_template.json"
            if not template_path.exists():
                with open(template_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)
                self.logger.info(f"创建默认{agent_type}模板: {template_path}")
    
    def load_template(self, agent_type: str) -> Dict:
        """
        加载指定类型的提示词模板
        
        Args:
            agent_type: Agent类型，如"character"、"partner"等
            
        Returns:
            提示词模板字典
        """
        template_path = self.templates_dir / f"{agent_type}_template.json"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载{agent_type}模板失败: {e}")
            # 返回空模板
            return {
                "system_prefix": "",
                "user_prefix": "",
                "response_format": ""
            }
    
    def save_template(self, agent_type: str, template: Dict) -> bool:
        """
        保存提示词模板
        
        Args:
            agent_type: Agent类型
            template: 提示词模板字典
            
        Returns:
            保存是否成功
        """
        template_path = self.templates_dir / f"{agent_type}_template.json"
        
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"保存{agent_type}模板成功")
            return True
        except Exception as e:
            self.logger.error(f"保存{agent_type}模板失败: {e}")
            return False
    
    def generate_character_prompt(self, character: Dict, scenario: Dict) -> str:
        """
        生成角色扮演Agent的系统提示词
        
        Args:
            character: 角色定义字典
            scenario: 场景定义字典
            
        Returns:
            格式化的系统提示词
        """
        template = self.load_template("character")
        
        # 准备替换变量
        # 背景描述
        background_parts = [
            f"- 童年: {character.get('background', {}).get('childhood', '未知')}",
            f"- 教育: {character.get('background', {}).get('education', '未知')}",
            f"- 职业: {character.get('background', {}).get('career', '未知')}",
            f"- 兴趣爱好: {', '.join(character.get('background', {}).get('hobbies', []))}"
        ]
        background_description = "\n".join(background_parts)
        
        # 说话习惯
        speech_patterns = "\n".join(character.get('speech_patterns', {}).get('communication_examples', []))
        
        # 场景描述
        scenario_parts = [
            f"场景: {scenario.get('title')}",
            scenario.get('description', ''),
            scenario.get('context', '')
        ]
        scenario_description = "\n".join(scenario_parts)
        
        # 角色视角
        perspective_parts = [
            f"- 你的理解: {scenario.get('character_perspective', {}).get('interpretation', '未知')}",
            f"- 你的期望: {scenario.get('character_perspective', {}).get('expectations', '未知')}",
            f"- 你的担忧: {scenario.get('character_perspective', {}).get('fears', '未知')}"
        ]
        character_perspective = "\n".join(perspective_parts)
        
        # 替换模板变量
        prompt = template["system_prefix"].format(
            name=character.get('name', '角色'),
            personality=character.get('personality', {'openness': 50, 'conscientiousness': 50, 'extraversion': 50, 'agreeableness': 50, 'neuroticism': 50}),
            attachment_style=character.get('attachment_style', '未知'),
            communication_style=character.get('communication_style', '未知'),
            background_description=background_description,
            values=", ".join(character.get('values', [])),
            speech_patterns=speech_patterns,
            scenario_description=scenario_description,
            character_perspective=character_perspective
        )
        
        return prompt
    
    def generate_partner_prompt(self, character: Dict, scenario: Dict) -> str:
        """
        生成伴侣Agent的系统提示词
        
        Args:
            character: 角色定义字典
            scenario: 场景定义字典
            
        Returns:
            格式化的系统提示词
        """
        template = self.load_template("partner")
        
        # 准备替换变量
        # 角色信息
        character_info_parts = [
            f"- {character.get('age', '未知')}岁，{character.get('gender', '未知')}性",
            f"- 依恋类型: {character.get('attachment_style', '未知')}",
            f"- 沟通风格: {character.get('communication_style', '未知')}",
            f"- 职业: {character.get('background', {}).get('career', '未知')}"
        ]
        character_info = "\n".join(character_info_parts)
        
        # 场景描述
        scenario_parts = [
            f"{scenario.get('title')} - {scenario.get('description')}",
            scenario.get('context', '')
        ]
        scenario_description = "\n".join(scenario_parts)
        
        # 矛盾背景
        conflict_parts = [
            f"- 你们的关系状态: {character.get('relationship_status', {}).get('length', '一段时间')}的恋爱关系，{character.get('relationship_status', {}).get('commitment_level', '认真交往中')}",
            f"- 最近发生的事件: {scenario.get('background', {}).get('recent_events', '未知')}"
        ]
        conflict_background = "\n".join(conflict_parts)
        
        # 伴侣真实情况
        reality_parts = [
            scenario.get('partner_reality', {}).get('situation', ''),
            scenario.get('partner_reality', {}).get('intentions', ''),
            scenario.get('partner_reality', {}).get('awareness', '')
        ]
        partner_reality = "\n".join(reality_parts)
        
        # 沟通建议
        attachment_style = character.get('attachment_style', '').lower()
        communication_style = character.get('communication_style', '').lower()
        
        tips = []
        
        if "anxious" in attachment_style:
            tips.append("- 对焦虑型依恋的伴侣提供明确和持续的确认")
        elif "avoidant" in attachment_style:
            tips.append("- 对回避型依恋的伴侣尊重其独立和空间需求")
        elif "secure" in attachment_style:
            tips.append("- 对安全型依恋的伴侣可以直接坦诚地表达")
        elif "fearful" in attachment_style:
            tips.append("- 对恐惧型依恋的伴侣提供安全感和耐心")
        
        if "passive-aggressive" in communication_style or "passive_aggressive" in communication_style:
            tips.append("- 对消极攻击型沟通的伴侣，温和但直接地讨论隐藏的问题")
        elif "passive" in communication_style:
            tips.append("- 对被动型沟通的伴侣，创造安全空间鼓励其表达")
        elif "aggressive" in communication_style:
            tips.append("- 对攻击型沟通的伴侣，保持冷静并设定明确的边界")
        elif "assertive" in communication_style:
            tips.append("- 对自信型沟通的伴侣，可以进行开放和直接的沟通")
        
        tips.append("- 使用"我"陈述而非"你"陈述来避免指责感")
        
        communication_tips = "\n".join(tips)
        
        # 替换模板变量
        prompt = template["system_prefix"].format(
            character_name=character.get('name', '角色'),
            character_info=character_info,
            scenario_description=scenario_description,
            conflict_background=conflict_background,
            partner_reality=partner_reality,
            communication_tips=communication_tips
        )
        
        return prompt
    
    def generate_emotion_prompt(self, character: Dict, scenario: Dict) -> str:
        """
        生成情绪监测Agent的系统提示词
        
        Args:
            character: 角色定义字典
            scenario: 场景定义字典
            
        Returns:
            格式化的系统提示词
        """
        template = self.load_template("emotion")
        
        # 准备替换变量
        # 角色信息
        character_info_parts = [
            f"- 名字: {character.get('name', '未知')}",
            f"- 性别: {character.get('gender', '未知')}",
            f"- 年龄: {character.get('age', '未知')}",
            f"- 依恋类型: {character.get('attachment_style', '未知')}",
            f"- 沟通风格: {character.get('communication_style', '未知')}",
            f"- 情绪触发点: {', '.join(character.get('emotional_triggers', {}).get('negative', []))}"
        ]
        character_info = "\n".join(character_info_parts)
        
        # 场景描述
        scenario_parts = [
            f"- 场景: {scenario.get('title')}",
            f"- 描述: {scenario.get('description')}",
            f"- 初级评估: {scenario.get('cognitive_appraisal', {}).get('primary', '未知')}",
            f"- 次级评估: {scenario.get('cognitive_appraisal', {}).get('secondary', '未知')}"
        ]
        scenario_description = "\n".join(scenario_parts)
        
        # 替换模板变量
        prompt = template["system_prefix"].format(
            character_info=character_info,
            scenario_description=scenario_description
        )
        
        return prompt
    
    def generate_expert_prompt(self, expert_type: str, character: Dict, scenario: Dict) -> str:
        """
        生成专家评估Agent的系统提示词
        
        Args:
            expert_type: 专家类型
            character: 角色定义字典
            scenario: 场景定义字典
            
        Returns:
            格式化的系统提示词
        """
        template = self.load_template("expert")
        
        # 准备专家描述
        expert_descriptions = {
            "psychologist": "你是一位专业心理学家，专注于评估人际互动中的心理动态、情绪反应和认知模式。你擅长识别依恋类型的表现和潜在的心理需求。",
            "communication_expert": "你是一位沟通专家，专注于评估对话中的沟通技巧、表达清晰度和沟通障碍。你擅长分析沟通模式和提出改进建议。",
            "relationship_therapist": "你是一位关系治疗师，专注于评估恋爱关系中的互动模式、冲突解决方式和亲密度发展。你擅长识别关系中的核心问题和解决方案。",
            "emotional_coach": "你是一位情感教练，专注于评估情绪表达、情绪调节和情感连接。你擅长指导如何更健康地处理和表达情感。"
        }
        
        expert_chinese_types = {
            "psychologist": "心理学家",
            "communication_expert": "沟通专家",
            "relationship_therapist": "关系治疗师",
            "emotional_coach": "情感教练"
        }
        
        expert_description = expert_descriptions.get(expert_type, expert_descriptions["psychologist"])
        expert_chinese_type = expert_chinese_types.get(expert_type, "专家")
        
        # 替换模板变量
        prompt = template["system_prefix"].format(
            expert_description=expert_description,
            expert_chinese_type=expert_chinese_type
        )
        
        # 构建用户前缀
        user_prefix = template["user_prefix"].format(
            expert_chinese_type=expert_chinese_type,
            character_info=f"- 名字：{character.get('name')}\n- 性别：{character.get('gender')}\n- 年龄：{character.get('age')}\n- 依恋类型：{character.get('attachment_style')}\n- 沟通风格：{character.get('communication_style')}",
            scenario_info=f"- 标题：{scenario.get('title')}\n- 描述：{scenario.get('description')}\n- 情境：{scenario.get('context')}\n- 伴侣真实情况：{scenario.get('partner_reality', {}).get('situation', '')}"
        )
        
        return {
            "system_prompt": prompt,
            "user_prefix": user_prefix
        }
    
    def format_dialogue_history(self, dialogue_history: List[Dict], character_name: Optional[str] = None) -> str:
        """
        格式化对话历史
        
        Args:
            dialogue_history: 对话历史记录
            character_name: 角色名称，默认为None，将使用"角色"
            
        Returns:
            格式化的对话历史字符串
        """
        if not dialogue_history:
            return ""
        
        if character_name is None:
            character_name = "角色"
        
        formatted = []
        for entry in dialogue_history:
            speaker = character_name if entry["role"] == "character" else "伴侣"
            formatted.append(f"{speaker}：{entry['content']}")
        
        return "\n".join(formatted)


# 简单测试用例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建提示词生成器
    prompt_generator = PromptGenerator()
    
    # 加载测试场景和角色
    try:
        base_dir = Path(__file__).resolve().parent.parent.parent
        scenario_path = base_dir / "data" / "scenarios" / "templates" / "scenario_005.json"
        with open(scenario_path, 'r', encoding='utf-8') as f:
            scenario = json.load(f)
        
        character_path = base_dir / "data" / "characters" / "templates" / "char_001.json"
        with open(character_path, 'r', encoding='utf-8') as f:
            character = json.load(f)
        
        # 生成角色扮演提示词
        character_prompt = prompt_generator.generate_character_prompt(character, scenario)
        print("\n===== 角色扮演提示词 =====")
        print(character_prompt[:500] + "...\n")
        
        # 生成伴侣提示词
        partner_prompt = prompt_generator.generate_partner_prompt(character, scenario)
        print("\n===== 伴侣提示词 =====")
        print(partner_prompt[:500] + "...\n")
        
        # 生成情绪监测提示词
        emotion_prompt = prompt_generator.generate_emotion_prompt(character, scenario)
        print("\n===== 情绪监测提示词 =====")
        print(emotion_prompt[:500] + "...\n")
        
        # 生成专家评估提示词
        expert_prompt = prompt_generator.generate_expert_prompt("psychologist", character, scenario)
        print("\n===== 专家评估提示词 =====")
        print(expert_prompt["system_prompt"][:500] + "...\n")
        
    except Exception as e:
        logging.error(f"测试失败: {e}") 