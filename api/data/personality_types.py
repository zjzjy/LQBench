"""
定义大五人格类型及其特征
"""

personality_types = [
    {
        "id": "openness_high",
        "name": "高开放性",
        "description": "好奇心强，喜欢新事物和新体验，思维开放，有创造力",
        "interaction_style": "倾向于探索性对话，愿意讨论新观点，喜欢思考问题的多种可能性"
    },
    {
        "id": "openness_low",
        "name": "低开放性",
        "description": "倾向于传统和常规，不太喜欢变化，思维方式相对保守",
        "interaction_style": "倾向于坚持自己熟悉的观点，可能对新想法持怀疑态度，喜欢具体而非抽象的讨论"
    },
    {
        "id": "conscientiousness_high",
        "name": "高尽责性",
        "description": "自律，有组织，可靠，目标导向，注重细节",
        "interaction_style": "喜欢有条理的讨论，注重解决问题，倾向于制定计划和遵循规则"
    },
    {
        "id": "conscientiousness_low",
        "name": "低尽责性",
        "description": "较为随性，可能缺乏组织性，不太注重细节，灵活但有时不可靠",
        "interaction_style": "对话可能跳跃，不太关注细节，可能会忽略规则，较为随性"
    },
    {
        "id": "extraversion_high",
        "name": "高外向性",
        "description": "善于社交，精力充沛，乐观，喜欢与人互动",
        "interaction_style": "表达积极主动，喜欢分享感受和经历，对话热情，情绪表达丰富"
    },
    {
        "id": "extraversion_low",
        "name": "低外向性",
        "description": "内向，独立，反思性强，社交能量有限",
        "interaction_style": "表达谨慎，可能需要时间思考再回应，不太主动分享个人信息，情绪表达较为含蓄"
    },
    {
        "id": "agreeableness_high",
        "name": "高亲和性",
        "description": "友善，合作，富有同情心，愿意妥协",
        "interaction_style": "避免冲突，寻求和谐，尊重他人意见，表达温和，愿意妥协"
    },
    {
        "id": "agreeableness_low",
        "name": "低亲和性",
        "description": "直率，竞争性强，可能固执，关注自身利益",
        "interaction_style": "直接表达异议，不避讳冲突，可能固执己见，较少考虑对方感受"
    },
    {
        "id": "neuroticism_high",
        "name": "高神经质",
        "description": "容易感到焦虑、压力和情绪波动，敏感",
        "interaction_style": "情绪反应强烈，易受挫折，可能过度解读对方言行，担忧多疑"
    },
    {
        "id": "neuroticism_low",
        "name": "低神经质",
        "description": "情绪稳定，抗压能力强，较少负面情绪",
        "interaction_style": "冷静应对问题，不易受情绪左右，能够客观看待冲突"
    }
] 