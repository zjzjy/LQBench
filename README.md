# LQBench代码结构与交互方法详解

## 项目概述

LQBench是一个情侣对话模拟基准测试框架，用于模拟具有不同性格特质、关系信念、沟通方式和依恋类型的虚拟人物在各种冲突场景下的交互过程和情绪变化。该框架通过大型语言模型(LLM)实现角色扮演，支持多种对话场景测试和结果分析。

## 系统架构

### 目录结构

```
LQBench/
├── __init__.py             # 包初始化文件
├── benchmark_runner.py     # 基准测试运行器
├── character_simulator.py  # 虚拟人物模拟器
├── config.json             # 配置文件
├── api/                    # API相关模块
│   ├── __init__.py
│   ├── llm.py              # LLM接口客户端
│   └── data/               # 数据定义模块
│       ├── __init__.py
│       ├── attachment_styles.py    # 依恋类型定义
│       ├── character_profiles.py   # 虚拟人物配置
│       ├── communication_types.py  # 沟通类型定义
│       ├── conflict_scenarios.py   # 冲突场景定义
│       ├── emotions.py             # 情绪类型定义
│       ├── personality_types.py    # 性格类型定义
│       ├── prompt_templates.py     # 提示词模板
│       └── relationship_beliefs.py # 关系信念定义
```

### 核心组件

1. **数据定义模块** (api/data/)：包含各种虚拟人物特质和场景定义
2. **LLM接口模块** (api/llm.py)：负责与大语言模型API的交互
3. **虚拟人物模拟器** (character_simulator.py)：管理对话流程和情绪评估
4. **基准测试运行器** (benchmark_runner.py)：执行批量测试和结果分析

## 关键模块详解

### 1. LLM接口模块 (api/llm.py)

该模块提供与大型语言模型API的交互接口，支持DeepSeek和OpenRouter两种API服务。

#### 主要类和方法

```python
class LLMClient:
    def __init__(self, api_type="deepseek"):  
        # 初始化客户端，选择API类型
        
    def _load_api_keys(self):  
        # 从环境变量或配置文件加载API密钥
        
    def call(self, prompt, model=None, temperature=0.7, max_tokens=2000, system_prompt=None, messages=None):  
        # 通用API调用接口
        
    def _call_deepseek(self, prompt, model=None, temperature=0.7, max_tokens=2000, system_prompt=None, messages=None):  
        # 调用DeepSeek API
        
    def _call_openrouter(self, prompt, model=None, temperature=0.7, max_tokens=2000, system_prompt=None, messages=None):  
        # 调用OpenRouter API，失败时回退到DeepSeek
        
    def create_chat_completion(self, messages, model=None, temperature=0.7, max_tokens=2000):  
        # 创建聊天完成（兼容OpenAI API格式）
```

#### 关键特性

- **多API支持**：支持DeepSeek和OpenRouter两种API服务
- **自动加载配置**：从多种可能的位置自动加载API密钥
- **回退机制**：当OpenRouter API失败时自动回退到DeepSeek API
- **灵活性**：支持不同的提示词格式和模型参数

### 2. 数据定义模块 (api/data/)

该目录下的文件定义了系统所需的各种基础数据，包括性格特质、关系信念、沟通类型等。

#### 主要数据类型

1. **性格类型** (personality_types.py)
   ```python
   personality_types = [
       {
           "id": "openness_high",  # 标识符
           "name": "高开放性",      # 中文名称
           "description": "好奇心强，喜欢新事物...",  # 详细描述
           "interaction_style": "倾向于探索性对话..."  # 交互方式
       },
       # 其他性格类型...
   ]
   ```

2. **依恋类型** (attachment_styles.py)
   ```python
   attachment_styles = [
       {
           "id": "secure",  # 标识符
           "name": "安全型依恋",  # 中文名称
           "description": "能够在亲密关系中感到舒适...",  # 详细描述
           "interaction_style": "表达感受直接而适度...",  # 交互方式
           "conflict_response": "面对冲突时保持冷静..."  # 冲突响应方式
       },
       # 其他依恋类型...
   ]
   ```

3. **沟通类型** (communication_types.py)
   ```python
   communication_types = [
       {
           "id": "direct_opposition",  # 标识符
           "name": "直接对抗",  # 中文名称
           "description": "直接表达不满和反对意见...",  # 详细描述
           "interaction_style": "使用直接的语言表达不满...",  # 交互方式
           "example_phrases": ["我完全不同意你的看法", ...]  # 示例短语
       },
       # 其他沟通类型...
   ]
   ```

4. **关系信念** (relationship_beliefs.py)
   ```python
   relationship_beliefs = [
       {
           "id": "destiny_belief_high",  # 标识符
           "name": "强命定论信念",  # 中文名称
           "description": "坚信伴侣关系是命中注定的...",  # 详细描述
           "interaction_style": "在关系冲突时更容易放弃..."  # 交互方式
       },
       # 其他关系信念...
   ]
   ```

5. **冲突场景** (conflict_scenarios.py)
   ```python
   conflict_scenarios = [
       {
           "id": "communication_misunderstanding",  # 场景标识符
           "name": "沟通误解",  # 场景名称
           "description": "因沟通不畅导致的误解和冲突",  # 场景描述
           "situations": [  # 具体情境列表
               {
                   "id": "ignored_messages",  # 情境标识符
                   "name": "忽视消息",  # 情境名称
                   "description": "一方感到对方忽视了自己的消息...",  # 情境描述
                   "example": "男方因工作繁忙未及时回复...",  # 情境示例
                   "typical_triggers": ["回复延迟", "已读不回", ...]  # 典型触发因素
               },
               # 其他具体情境...
           ]
       },
       # 其他冲突场景...
   ]
   ```

6. **提示词模板** (prompt_templates.py)
   ```python
   character_prompt_template = """
   你现在将扮演一个名叫{name}的{age}岁{gender}性，请完全按照以下人物特质行事：
   
   ## 基本信息
   - 姓名：{name}
   - 年龄：{age}岁
   - 性别：{gender}
   - 背景：{background}
   
   ## 人物特质
   - 性格特点：{personality_description}
   - 关系观念：{relationship_belief_description}
   - 沟通方式：{communication_style_description}
   - 依恋类型：{attachment_style_description}
   
   ## 交互指南
   - 容易触发情绪反应的话题：{trigger_topics}
   - 面对压力的应对机制：{coping_mechanisms}
   
   ## 当前情境
   你正在与你的男/女朋友发生争执，争执的内容是：{conflict_description}
   
   ## 要求
   1. 完全沉浸于角色中，根据上述特质自然地回应对话
   2. 在每次回应后，提供一个内心独白，说明你当前的情绪状态（注意：这部分要用【内心】标记，对话的另一方看不到）
   3. 根据对话的进展实时调整你的情绪状态，考虑对方的言行如何影响你的感受
   4. 评估你的情绪值（-10到+10的范围，其中-10表示极度负面，0表示中性，+10表示极度正面）
   
   记住，你应该像一个真实的人一样回应，考虑你的性格特点、沟通方式和依恋类型如何影响你的反应。
   
   开始对话前，请先思考你对这个情境的初始情绪状态。
   """
   ```

7. **虚拟人物配置** (character_profiles.py)
   ```python
   sample_characters = [
       {
           "id": "anxious_destiny_believer",  # 角色ID
           "name": "林夏",  # 角色名称
           "gender": "女",  # 性别
           "age": 24,  # 年龄
           "personality_type": "neuroticism_high",  # 性格类型
           "relationship_belief": "destiny_belief_high",  # 关系信念
           "communication_type": "indirect_opposition",  # 沟通类型
           "attachment_style": "anxious",  # 依恋类型
           "background": "大学毕业后在一家设计公司工作...",  # 背景故事
           "trigger_topics": ["忽视", "工作优先", ...],  # 触发话题
           "coping_mechanisms": ["寻求确认", "情绪爆发", ...]  # 应对机制
       },
       # 其他示例角色...
   ]
   ```

### 3. 虚拟人物模拟器 (character_simulator.py)

该模块是核心模拟执行引擎，负责管理对话流程和情绪评估。

#### 主要类和方法

```python
class CharacterSimulator:
    def __init__(self, character_config=None, scenario_id=None, character_api="deepseek", 
                 partner_api="openrouter", expert_api="deepseek", max_turns=10, log_dir="logs",
                 use_emotion_prediction=True, use_expert_analysis=True, num_experts=3):
        # 初始化角色、场景和分析设置
        
    def _prepare_prompts(self):
        # 准备角色和伴侣的提示词
        
    def _parse_emotion(self, response):
        # 解析虚拟人物回复中的情绪评估
        
    def _predict_emotion(self):
        # 使用待测模型预测虚拟人物的下一轮情绪状态
        
    def _analyze_with_experts(self):
        # 使用多个专家模型分析虚拟人物的当前情绪状态
        
    def should_end_dialogue(self):
        # 判断对话是否应该结束
        
    def simulate_turn(self):
        # 模拟一轮对话
        
    def run_simulation(self):
        # 运行完整的对话模拟
```

#### 模拟流程

1. **初始化**：加载角色配置和冲突场景
2. **准备提示词**：根据角色特质和场景组装LLM提示词
3. **对话循环**：轮流让角色和伴侣发言，每轮解析情绪状态
4. **情感预测**：在每轮对话后，待测模型预测虚拟人物下一轮的情感状态
5. **专家分析**：多个专家模型实时分析虚拟人物的情感状态
6. **结束判断**：根据轮次和情绪变化判断何时结束对话
7. **返回结果**：包含完整对话历史、情绪变化曲线、情感预测和专家分析结果

### 4. 基准测试运行器 (benchmark_runner.py)

该模块负责批量执行测试和结果分析，支持多种测试配置。

#### 主要类和方法

```python
class BenchmarkRunner:
    def __init__(self, output_dir="benchmark_results", log_dir="logs", max_turns=10,
                 character_api="deepseek", partner_api="openrouter", expert_api="deepseek",
                 use_emotion_prediction=True, use_expert_analysis=True, num_experts=3):
        # 初始化基准测试配置
        
    def generate_test_cases(self, num_characters=5, scenario_ids=None):
        # 生成测试用例
        
    def run_single_test(self, test_case):
        # 运行单个测试用例
        
    def _calculate_prediction_accuracy(self, result):
        # 计算情感预测的准确度
        
    def _calculate_expert_consensus(self, result):
        # 计算专家分析的一致性
        
    def run_benchmark(self, test_cases=None, num_characters=5, scenario_ids=None, parallel=False, max_workers=4):
        # 运行所有测试用例
        
    def analyze_results(self, results, output_prefix):
        # 分析测试结果
        
    def _generate_charts(self, df, output_prefix):
        # 生成结果图表
```

#### 测试流程

1. **生成测试用例**：根据指定参数生成多个角色和场景组合
2. **并行/串行测试**：执行每个测试用例，记录结果
3. **情感预测评估**：评估待测模型的情感预测准确度
4. **专家一致性评估**：计算多专家分析的一致性
5. **结果分析**：统计分析测试结果并生成报告
6. **可视化**：生成多种图表展示测试结果

## 新增功能详解

### 1. 待测模型情感预测

该功能允许待测模型在每轮对话后，基于历史对话预测虚拟人物在下一轮对话中可能的情感状态。

#### 核心实现

- **预测时机**：每轮对话结束后、下一轮开始前
- **预测内容**：情绪类型、强度、评分和解释
- **评估方法**：将预测结果与实际情绪状态对比，计算准确度

#### 使用示例

```python
# 启用情感预测功能
simulator = CharacterSimulator(
    character_config=character,
    scenario_id=scenario_id,
    use_emotion_prediction=True,
    partner_api="openrouter"  # 待测模型API
)

# 运行模拟
result = simulator.run_simulation()

# 查看情感预测历史
prediction_history = result['emotion_prediction_history']
for prediction in prediction_history:
    print(f"轮次 {prediction['turn']}:")
    print(f"预测情绪: {prediction['predicted_emotion']}")
    print(f"情绪强度: {prediction['intensity']}")
    print(f"情绪评分: {prediction['emotion_score']}")
    print(f"预测解释: {prediction['explanation']}")
    print("---")
```

### 2. 多专家实时情感分析

该功能使用多个专家模型同时分析虚拟人物与待测模型的对话，实时评估虚拟人物的情感状态。

#### 核心实现

- **分析时机**：每轮对话结束后立即进行
- **专家数量**：默认使用3个专家模型（可配置）
- **分析内容**：主要情绪、强度、评分、关键触发点和简要分析
- **一致性计算**：评估多个专家之间分析结果的一致程度

#### 使用示例

```python
# 启用多专家分析功能
simulator = CharacterSimulator(
    character_config=character,
    scenario_id=scenario_id,
    use_expert_analysis=True,
    num_experts=3,
    expert_api="deepseek"  # 专家模型API
)

# 运行模拟
result = simulator.run_simulation()

# 查看专家分析历史
expert_history = result['expert_analysis_history']
for turn_analysis in expert_history:
    print(f"轮次 {turn_analysis['turn']}:")
    for analysis in turn_analysis['analyses']:
        print(f"专家 {analysis['expert_id']}:")
        print(f"主要情绪: {analysis['primary_emotion']}")
        print(f"情绪强度: {analysis['intensity']}")
        print(f"情绪评分: {analysis['emotion_score']}")
        print(f"关键触发点: {', '.join(analysis['key_triggers'])}")
        print(f"简要分析: {analysis['analysis']}")
    print("---")
```

## 运行方法

### 基本使用

```python
from LQBench.character_simulator import CharacterSimulator

# 创建模拟器
simulator = CharacterSimulator(
    character_api="deepseek",
    partner_api="openrouter",
    expert_api="deepseek",
    use_emotion_prediction=True,
    use_expert_analysis=True,
    num_experts=3
)

# 运行模拟
result = simulator.run_simulation()

# 打印结果
print(f"对话轮次: {result['turns_completed']}")
print(f"最终情绪分数: {result['final_emotion_score']}")
```

### 命令行运行

```bash
python -m LQBench.benchmark_runner --num-characters 3 --max-turns 8 --use-emotion-prediction --use-expert-analysis --num-experts 3
```

## 数据流向图

```
角色特质 → 提示词生成 → LLM接口 → 对话生成 → 情绪解析 → 对话流程控制 → 结果分析
  |                                 ↑
  |                                 |
场景选择 ---------------------------|
```

## 结果解读

每次测试的结果包含：

1. **基本信息**：角色ID、名称、性格特质、场景等
2. **对话统计**：完成轮次、初始情绪分、最终情绪分、情绪变化
3. **情绪曲线**：每轮对话的情绪分数变化
4. **详细对话**：完整的对话历史和情绪变化记录

批量测试的结果包含：

1. **CSV报告**：所有测试的汇总统计数据
2. **性格对比图**：不同性格特质的情绪变化对比
3. **场景对比图**：不同场景下的情绪变化对比
4. **依恋类型图**：不同依恋类型的情绪变化对比

## 开发扩展

### 添加新性格特质

在`api/data/personality_types.py`中添加新的性格类型：

```python
personality_types.append({
    "id": "your_new_type_id",
    "name": "新性格类型名称",
    "description": "详细描述...",
    "interaction_style": "交互风格描述..."
})
```

### 添加新场景

在`api/data/conflict_scenarios.py`中添加新的冲突场景：

```python
conflict_scenarios.append({
    "id": "new_scenario_id",
    "name": "新场景名称",
    "description": "场景描述...",
    "situations": [
        {
            "id": "situation_1",
            "name": "情境1名称",
            "description": "情境描述...",
            "example": "情境示例...",
            "typical_triggers": ["触发因素1", "触发因素2"]
        }
    ]
})
```

### 自定义情绪评估

修改`api/data/emotions.py`中的情绪评分阈值：

```python
emotion_scoring = {
    "threshold": {
        "improvement": 5,  # 情绪好转阈值
        "worsening": -5,   # 情绪恶化阈值
        "critical": -8     # 临界阈值
    }
}
```

## 注意事项

1. 必须提供有效的API密钥才能运行测试
2. 大模型API请求可能产生费用，请控制测试规模
3. 测试结果可能因模型版本和参数而异
4. 情绪解析基于大模型输出，准确性有限
5. 大规模并行测试可能受API调用限制影响 

## 评估模块详解

### 5. 对话评估模块 (metrics.py)

metrics.py 文件提供了一套全面的对话质量评估和角色特征分析工具，用于评估和分析生成的对话日志。该模块可以分析对话中的沟通模式、依恋类型特征、情感变化等多个维度，生成详细的评估报告。

#### 主要类和功能

1. **ConsistencyEvaluator 类**：角色特征归类器
   - 分析对话内容，识别角色的沟通模式和依恋类型
   - 支持基于关键词的规则式分析和API辅助分析
   - 能够识别六种沟通类型：直接表达、间接表达、情感表达、理性分析、问题导向、解决导向
   - 能够识别四种依恋类型：安全型、焦虑型、回避型、混乱型
   - 检测违反预设规则的行为

2. **DialogueEvaluator 类**：对话质量评估器
   - 提供全面的对话统计数据：消息数量、长度、词汇多样性等
   - 分析情感变化：情感范围、波动性、变化轨迹
   - 评估主题连贯性和互动质量
   - 分析说话风格和表达清晰度
   - 评估积极/消极因素的平衡
   - 生成综合的一致性得分和质量得分

3. **批量分析功能**
   - `analyze_dialogue_log`：分析单个对话日志文件
   - `batch_analyze_logs`：批量分析目录中的所有对话日志
   - 汇总统计数据：平均得分、沟通类型分布、依恋类型分布等
   
#### 使用方法

metrics.py 可以通过命令行参数进行配置，支持以下功能：

```bash
# 评估单个对话日志文件
python metrics.py -f 日志文件路径 -o 输出目录

# 批量评估目录中的所有日志文件
python metrics.py -d 日志目录 -o 输出目录

# 启用API辅助分析（用于规则式方法无法判断的情况）
python metrics.py -d 日志目录 --use-api --api-type deepseek

# 使用配置文件
python metrics.py -c 配置文件.json
```

配置文件示例（JSON格式）：
```json
{
    "input_directory": "logs_test",
    "output_dir": "logs_test_eval",
    "output": "logs_test_eval",
    "use_api": true,
    "api_type": "deepseek",
    "model_name": "deepseek-chat",
    "debug": false
}
```

#### 项目文件夹说明

- **logs_test/**：包含对话示例文件，用于测试和分析
- **logs_test_eval/**：存放评估结果的目录，包含对logs_test中对话的分析结果
- **metrics.py**：对话评估工具，用于分析对话质量、沟通模式和依恋特征

#### 示例输出

评估结果以JSON格式存储，包含以下主要信息：
- 基本元数据：文件名、角色信息、场景信息
- 对话统计：总消息数、平均长度、词汇多样性等
- 情感统计：情感范围、波动性、主导情感等
- 一致性分析：主题连贯性、互动质量、说话风格等
- 质量评估：倾听清晰度、积极/消极因素平衡等
- 角色特征：沟通类型、依恋类型、违禁行为数量等
- 情感分布：各类情感的出现频率

#### 评估维度说明

1. **沟通类型**：基于对话中出现的关键词和表达方式，将沟通模式分为六种类型
2. **依恋类型**：基于依恋理论，从对话中识别安全型、焦虑型、回避型和混乱型的特征
3. **一致性得分**：0-10分，评估对话的连贯性、互动质量和风格一致性
4. **质量得分**：0-10分，综合评估对话的质量，包括词汇多样性、主题连贯性、倾听能力等

通过这些评估，可以深入了解不同人物特质在对话中的表现差异，为虚拟角色的设计和优化提供数据支持。 