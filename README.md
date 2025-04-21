# LOVE: 情感智能评估系统

LOVE (Learning Observational Virtual Emotions) 是一个多代理系统，旨在通过模拟浪漫关系中的情感冲突来评估大语言模型的情感智能。

## 项目概述

LOVE系统使用多代理架构模拟不同个性角色在浪漫关系冲突场景中的对话和情感变化。系统由以下几个主要组件构成：

1. **角色代理 (Character Agent)**: 模拟具有特定人格、依恋风格和沟通方式的虚拟角色
2. **伙伴代理 (Partner Agent)**: 模拟虚拟角色的伴侣，旨在以建设性的方式解决冲突
3. **情绪代理 (Emotion Agent)**: 跟踪和分析对话过程中的情感变化
4. **记忆代理 (Memory Agent)**: 管理对话历史和提取关键记忆点
5. **对话管理器 (Dialogue Manager)**: 协调代理之间的交互和管理对话流程
6. **数据可视化工具 (Dialogue Visualizer)**: 提供对话结果的可视化分析

## 功能特点

- 多样化的角色池：包含不同依恋风格、沟通模式和性格特点的虚拟角色
- 丰富的冲突场景：模拟现实中常见的浪漫关系冲突
- 实时情感跟踪：分析对话中的情感变化和强度
- 对话记忆管理：提取和利用关键信息指导对话
- 可视化分析：通过图表和报告展示对话成效和情感变化
- 多种运行模式：支持单次对话、批量评估和全面测试

## 快速开始

### 环境准备

确保你已安装Python 3.8或更高版本，然后安装所需依赖：

```bash
pip install -r requirements.txt
```

### 项目结构

```
LOVE/
├── data/                       # 数据目录
│   ├── characters/             # 角色数据
│   │   ├── templates/          # 角色模板
│   │   └── character_pool.json # 角色池定义
│   └── scenarios/              # 场景数据
│       ├── templates/          # 场景模板
│       └── scenario_pool.json  # 场景池定义
├── src/                        # 源代码
│   ├── agents/                 # 代理实现
│   │   ├── character_agent.py  # 角色代理
│   │   ├── partner_agent.py    # 伙伴代理
│   │   ├── emotion_agent.py    # 情绪代理
│   │   └── memory_agent.py     # 记忆代理
│   ├── dialogue/               # 对话管理
│   │   └── dialogue_manager.py # 对话管理器
│   ├── utils/                  # 工具函数
│   │   ├── data_loader.py      # 数据加载器
│   │   └── helper_functions.py # 辅助函数
│   ├── visualization/          # 可视化工具
│   │   └── dialogue_visualizer.py # 对话可视化
│   ├── api/                    # API接口
│   │   └── openrouter_api.py   # OpenRouter API封装
│   └── main.py                 # 主程序入口
├── scripts/                    # 脚本工具
│   └── test_dialogue_manager.py # 测试脚本
├── config/                     # 配置文件
│   └── api_config.json         # API配置
├── results/                    # 结果保存目录
│   └── dialogues/              # 对话结果
├── visualizations/             # 可视化输出目录
├── logs/                       # 日志目录
├── requirements.txt            # 依赖列表
└── README.md                   # 项目说明
```

### 运行单次对话

```bash
python src/main.py --mode single --character char_001 --scenario scenario_005
```

### 运行批量对话

```bash
python src/main.py --mode batch --batch-config config/batch_config.json
```

批量配置文件示例 (batch_config.json):

```json
[
  {"character_id": "char_001", "scenario_id": "scenario_005"},
  {"character_id": "char_002", "scenario_id": "scenario_012"}
]
```

### 运行评估模式

```bash
python src/main.py --mode evaluation
```

## 配置说明

你可以通过创建自定义配置文件来修改系统行为：

```bash
python src/main.py --config config/custom_config.json
```

配置文件示例 (custom_config.json):

```json
{
  "max_turns": 15,
  "save_results": true,
  "generate_report": true,
  "api_settings": {
    "timeout": 60,
    "max_retries": 5
  }
}
```

## API配置

在使用系统前，需要在`config/api_config.json`中配置OpenRouter API密钥：

```json
{
  "api_key": "your_openrouter_api_key_here",
  "api_base": "https://openrouter.ai/api/v1",
  "default_model": "anthropic/claude-3-opus",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

## 结果分析

对话完成后，系统会在`results/dialogues/`目录下生成结果文件，包括：

- `dialogue_history.json`: 完整对话历史
- `dialogue_result.json`: 对话结果摘要
- `dialogue_state_*.json`: 各轮对话状态

同时，可视化报告会保存在`visualizations/`目录中，包括：

- 消息分布图
- 情绪流动图
- 消息长度分布图
- 对话摘要图

## 自定义扩展

### 添加新角色

1. 在`data/characters/templates/`中创建新的角色JSON文件
2. 更新`data/characters/character_pool.json`添加角色信息

### 添加新场景

1. 在`data/scenarios/templates/`中创建新的场景JSON文件
2. 更新`data/scenarios/scenario_pool.json`添加场景信息

## 系统要求

- Python 3.8+
- numpy
- matplotlib
- aiohttp
- asyncio
- openai (用于OpenRouter API接口)

## 许可证

[MIT License](LICENSE) 