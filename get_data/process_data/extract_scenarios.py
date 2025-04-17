import pandas as pd
import json
import os
import requests
import time
from typing import Dict, List, Union
from tqdm import tqdm

def load_data(csv_path: str) -> pd.DataFrame:
    """加载CSV数据并预处理"""
    df = pd.read_csv(csv_path)
    # 删除banner和video列
    df = df.drop(['banner', 'video'], axis=1, errors='ignore')
    return df

def create_conflict_prompt(row: pd.Series) -> str:
    """创建冲突场景分析的提示词"""
    context = f"标题: {row['title']}\n内容: {row['content']}\n对话: {row['conversation']}"
    prompt = f"""请分析以下小红书帖子中的情侣冲突场景，并按照指定格式输出：

{context}

请仔细分析冲突场景，并以下面的JSON格式输出。注意：
1. id应该是英文的简短标识，例如"communication_misunderstanding"
2. name是对应的中文简短名称，例如"沟通误解"
3. description是对整体冲突类型的描述
4. situations一般包含两个元素，分别描述矛盾双方的具体情况。例如：
   - 第一个situation描述一方的行为和感受
   - 第二个situation描述另一方的行为和感受
   每个situation都需要包含：
   - id: 具体情况的英文标识（如"person_a_feeling_ignored"）
   - name: 具体情况的中文名称（如"感到被忽视"）
   - description: 对这个具体情况的详细描述
   - example: 从帖子中提取的具体例子
   - typical_triggers: 导致这种情况的典型触发因素列表

请以下面的JSON格式输出：
{{
    "conflict_scenario": {{
        "id": "冲突类型的英文标识",
        "name": "冲突类型的中文名称",
        "description": "对这类冲突的整体描述",
        "situations": [
            {{
                "id": "第一方情况的英文标识",
                "name": "第一方情况的中文名称",
                "description": "对第一方情况的具体描述",
                "example": "从帖子中提取的第一方具体例子",
                "typical_triggers": ["第一方的触发因素1", "第一方的触发因素2"]
            }},
            {{
                "id": "第二方情况的英文标识",
                "name": "第二方情况的中文名称",
                "description": "对第二方情况的具体描述",
                "example": "从帖子中提取的第二方具体例子",
                "typical_triggers": ["第二方的触发因素1", "第二方的触发因素2"]
            }}
        ]
    }}
}}

请确保：
1. situations数组必须包含两个元素，分别对应矛盾双方
2. 每个situation的描述都要具体且详细
3. typical_triggers要反映该方在冲突中的具体触发因素
4. 输出必须是有效的JSON格式

请基于帖子内容，提供具体、详细的描述。"""
    return prompt

def create_character_prompt(row: pd.Series, conflict_data: Dict) -> str:
    """创建人物特征分析的提示词，使用冲突场景的信息来关联ID"""
    context = f"标题: {row['title']}\n内容: {row['content']}\n对话: {row['conversation']}"
    
    # 获取冲突场景的ID信息
    conflict_id = conflict_data["conflict_scenario"]["id"]
    situation_ids = [s["id"] for s in conflict_data["conflict_scenario"]["situations"]]
    
    prompt = f"""请分析以下小红书帖子中涉事双方的人物特征，并按照指定格式输出两个人物的特征配置：

{context}

请仔细分析文本中的人物特征，注意：
1. 根据文本内容，适当推测人物的姓名、性别和年龄
2. 其他特征（性格、沟通方式等）必须基于文本中明确体现的内容
3. 如果某个特征在文本中没有明确体现，请将其值设置为"未知"
4. 所有推测都应该合理且符合文本上下文
5. 特别注意分析每个人物对事件的认知评估和情绪反应

请为每个人物（A和B）提供以下JSON格式的配置：
{{
    "character_profiles": [
        {{
            "id": "{conflict_id}_{situation_ids[0]}",  # 使用冲突ID和情境ID的组合
            "name": "根据文本内容合理推测的名字，如果无法推测则适当虚构",
            "gender": "根据文本内容推测的性别，如果无法推测则适当虚构",
            "age": "根据文本内容推测的年龄（请给出具体数字），如果无法推测则适当虚构",
            "personality_type": "从文本中体现的性格特征，如neuroticism_high（焦虑）、openness_high（开放）等，如果不明确则为未知",
            "relationship_belief": "从文本中体现的关系信念，如destiny_belief_high（命定论）、growth_belief_moderate（成长论）等，如果不明确则为未知",
            "communication_type": "从文本中体现的沟通方式，如direct_cooperation（直接合作型）、indirect_opposition（间接对抗型）等，如果不明确则为未知",
            "attachment_style": "从文本中体现的依恋类型，如anxious（焦虑型）、avoidant（回避型）等，如果不明确则为未知",
            "background": "从文本中提取的背景信息，如果未提及则为未知",
            "trigger_topics": ["从文本中提取的容易引发情绪反应的话题，如果没有明确体现则为空列表"],
            "coping_mechanisms": ["从文本中提取的应对压力方式，如果没有明确体现则为空列表"],
            "suggested_primary_appraisal": {{
                "relevance": "分析该事件与该角色的核心目标、价值或需求的相关性，如'威胁到感情安全感'或'影响工作生活平衡'",
                "nature": "分析该角色如何评估该事件（威胁/损失/挑战/机会）及其潜在情绪反应（愤怒/悲伤/喜悦/恐惧）"
            }},
            "suggested_secondary_appraisal": {{
                "attribution": "分析该角色对事件成因的归因（责怪他人/责怪自己/归因于环境或偶然）",
                "coping_ability": "分析该角色是否认为自己具备应对能力（有信心/感到无力）",
                "coping_strategy": "分析该角色试图采取的策略（直接沟通/情绪表达/回避/争执/寻求理解）"
            }},
            "suggested_emotions": [
                "列出该角色可能体验的核心情绪词，如'委屈'、'愤怒'、'羞辱'、'焦虑'、'渴望被理解'等"
            ]
        }},
        {{
            "id": "{conflict_id}_{situation_ids[1]}",  # 使用冲突ID和情境ID的组合
            ... (与上面相同的字段)
        }}
    ]
}}

请确保：
1. 人物姓名、性别、年龄的推测和虚构要合理且符合中国文化背景
2. 其他特征分析必须基于文本中明确体现的内容
3. 确保输出是有效的JSON格式
4. 每个结论都应该可以从原文中找到依据或有合理的推测基础
5. 认知评估和情绪分析要符合心理学理论，并与文本内容保持一致

请基于帖子内容，提供准确、合理的分析。"""
    return prompt

def call_deepseek_api(prompt: str, api_key: str) -> str:
    """调用Deepseek API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API调用失败: {response.status_code} - {response.text}")

def extract_json_from_response(response: str) -> Dict:
    """从API响应中提取JSON部分"""
    try:
        json_str = response[response.find('{'):response.rfind('}')+1]
        return json.loads(json_str)
    except Exception as e:
        raise Exception(f"JSON解析失败: {str(e)}")

def process_data(df: pd.DataFrame, api_key: str, conflict_output_path: str, character_output_path: str):
    """处理数据并分别保存冲突场景和人物配置"""
    conflict_scenarios = []
    character_profiles = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing rows"):
        try:
            # 获取冲突场景分析
            conflict_prompt = create_conflict_prompt(row)
            conflict_response = call_deepseek_api(conflict_prompt, api_key)
            conflict_data = extract_json_from_response(conflict_response)
            conflict_scenarios.append(conflict_data["conflict_scenario"])
            
            # API速率限制
            time.sleep(1)
            
            # 获取人物特征分析，传入冲突数据以关联ID
            character_prompt = create_character_prompt(row, conflict_data)
            character_response = call_deepseek_api(character_prompt, api_key)
            character_data = extract_json_from_response(character_response)
            character_profiles.extend(character_data["character_profiles"])
            
            # 每处理10条数据保存一次
            if (idx + 1) % 10 == 0:
                # 保存冲突场景
                with open(conflict_output_path, 'w', encoding='utf-8') as f:
                    json.dump({"conflict_scenarios": conflict_scenarios}, f, ensure_ascii=False, indent=2)
                
                # 保存人物配置
                with open(character_output_path, 'w', encoding='utf-8') as f:
                    json.dump({"character_profiles": character_profiles}, f, ensure_ascii=False, indent=2)
                
                print(f"Processed {idx + 1} entries")
            
            # API速率限制
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing row {idx}: {str(e)}")
            continue
    
    # 最终保存
    with open(conflict_output_path, 'w', encoding='utf-8') as f:
        json.dump({"conflict_scenarios": conflict_scenarios}, f, ensure_ascii=False, indent=2)
    
    with open(character_output_path, 'w', encoding='utf-8') as f:
        json.dump({"character_profiles": character_profiles}, f, ensure_ascii=False, indent=2)

def main():
    # 获取API密钥
    api_key = "sk-ded58190e01c48a59f824ba2647494ff"  # 直接设置API密钥
    
    # 设置路径
    csv_path = "raw_data/素材提取结果_数据表_表格.csv"  # 修改路径
    conflict_output_path = "data/extracted_conflict_scenarios.json"
    character_output_path = "data/extracted_character_profiles.json"
    
    # 加载数据
    print("Loading data...")
    df = load_data(csv_path)
    
    # 只取前5条数据
    #df = df.head(5)
    
    # 处理数据
    print("Processing data...")
    process_data(df, api_key, conflict_output_path, character_output_path)
    
    print(f"Done! Results saved to {conflict_output_path} and {character_output_path}")

if __name__ == "__main__":
    main() 