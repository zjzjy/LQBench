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
    def __init__(self, character_config=None, scenario_id=None, character_api="deepseek", partner_api="openrouter", max_turns=10, log_dir="logs"):
        # 初始化角色和场景
        
    def _prepare_prompts(self):
        # 准备角色和伴侣的提示词
        
    def _parse_emotion(self, response):
        # 解析虚拟人物回复中的情绪评估
        
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
4. **结束判断**：根据轮次和情绪变化判断何时结束对话
5. **返回结果**：包含完整对话历史和情绪变化曲线

### 4. 基准测试运行器 (benchmark_runner.py)

该模块负责批量执行测试和结果分析，支持多种测试配置。

#### 主要类和方法

```python
class BenchmarkRunner:
    def __init__(self, output_dir="benchmark_results", log_dir="logs", max_turns=10, character_api="deepseek", partner_api="openrouter"):
        # 初始化测试环境
        
    def generate_test_cases(self, num_characters=5, scenario_ids=None):
        # 生成测试用例
        
    def run_single_test(self, test_case):
        # 运行单个测试用例
        
    def run_benchmark(self, test_cases=None, num_characters=5, scenario_ids=None, parallel=False, max_workers=4):
        # 运行基准测试
        
    def analyze_results(self, results, output_prefix):
        # 分析测试结果并生成报告和图表
        
    def _generate_charts(self, df, output_prefix):
        # 生成图表
```

#### 测试流程

1. **生成测试用例**：创建多个不同特质组合的虚拟人物和场景配对
2. **批量执行**：串行或并行执行多个测试用例
3. **结果收集**：汇总每个测试的结果和情绪变化
4. **数据分析**：生成CSV报告和多种对比图表
5. **结果保存**：将报告保存到指定输出目录

## 使用方法

### 基本用法

通过命令行运行基准测试：

```bash
# 基本执行（生成5个随机角色测试所有场景）
python -m LQBench.benchmark_runner --num_characters 5 --max_turns 10

# 指定特定场景
python -m LQBench.benchmark_runner --scenarios communication_misunderstanding time_allocation

# 使用并行执行
python -m LQBench.benchmark_runner --parallel --max_workers 4
```

### 配置文件

在`LQBench/config.json`中设置API密钥和默认参数：

```json
{
    "DEEPSEEK_API_KEY": "你的DeepSeek API密钥",
    "OPENROUTER_API_KEY": "你的OpenRouter API密钥",
    "DEFAULT_CHARACTER_API": "deepseek",
    "DEFAULT_PARTNER_API": "openrouter",
    "MAX_TURNS": 10,
    "LOG_DIR": "logs",
    "OUTPUT_DIR": "benchmark_results",
    "PARALLEL_EXECUTION": false,
    "MAX_WORKERS": 4
}
```

### 自定义虚拟人物

可以通过编程方式创建自定义虚拟人物：

```python
from LQBench.api.data.character_profiles import create_character_profile
from LQBench.character_simulator import CharacterSimulator

# 创建自定义角色
my_character = create_character_profile(
    id="custom_character",
    name="张三",
    gender="男",
    age=28,
    personality_type="conscientiousness_high",
    relationship_belief="growth_belief_high",
    communication_type="direct_cooperation",
    attachment_style="secure",
    background="软件工程师，工作认真负责，注重效率",
    trigger_topics=["不守时", "工作干涉"],
    coping_mechanisms=["理性分析", "沟通解决"]
)

# 创建模拟器
simulator = CharacterSimulator(
    character_config=my_character,
    scenario_id="time_allocation",
    max_turns=8
)

# 运行模拟
result = simulator.run_simulation()
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