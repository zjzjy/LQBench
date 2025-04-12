"""
定义情侣冲突场景及相关描述
"""

conflict_scenarios = [
    {
        "id": "communication_misunderstanding",
        "name": "沟通误解",
        "description": "因沟通不畅导致的误解和冲突",
        "situations": [
            {
                "id": "ignored_messages",
                "name": "忽视消息",
                "description": "一方感到对方忽视了自己的消息或不及时回复",
                "example": "男方因工作繁忙未及时回复女方的消息，女方感到被忽视和不重视",
                "typical_triggers": ["回复延迟", "已读不回", "沟通频率不一致"]
            },
            {
                "id": "misinterpreted_tone",
                "name": "语气误解",
                "description": "一方误解了对方的语气或表达方式",
                "example": "女方以开玩笑的语气评论男方的穿着，男方却理解为批评并感到不满",
                "typical_triggers": ["文字缺乏情感表达", "回复简短", "幽默感差异"]
            }
        ]
    },
    {
        "id": "time_allocation",
        "name": "时间分配",
        "description": "关于如何分配时间给关系、工作和个人爱好的冲突",
        "situations": [
            {
                "id": "work_life_balance",
                "name": "工作与生活平衡",
                "description": "一方认为对方工作时间过长，忽视了感情和生活",
                "example": "男方经常加班到深夜，女方感到被忽视并质疑关系的重要性",
                "typical_triggers": ["频繁加班", "周末仍工作", "疲惫导致互动质量下降"]
            },
            {
                "id": "social_time_conflict",
                "name": "社交时间冲突",
                "description": "对于与朋友聚会或参加社交活动时间的争议",
                "example": "女方频繁与朋友聚会，男方希望有更多二人独处时间",
                "typical_triggers": ["频繁外出", "回家晚", "预期不一致"]
            }
        ]
    },
    {
        "id": "financial_issues",
        "name": "财务问题",
        "description": "关于金钱管理、消费习惯和财务决策的冲突",
        "situations": [
            {
                "id": "spending_habits",
                "name": "消费习惯",
                "description": "双方在消费观念和习惯上的差异导致冲突",
                "example": "女方喜欢购买奢侈品，男方更注重储蓄和投资，导致对财务规划有分歧",
                "typical_triggers": ["大额消费", "无计划购物", "财务目标不一致"]
            },
            {
                "id": "financial_responsibility",
                "name": "财务责任",
                "description": "关于谁应该支付特定费用或如何分担日常开销的争议",
                "example": "男方认为双方应该平等分担房租，女方则认为应该按收入比例分配",
                "typical_triggers": ["账单分摊", "大额支出决策", "金钱透明度"]
            }
        ]
    },
    {
        "id": "future_planning",
        "name": "未来规划",
        "description": "关于关系发展方向、婚姻计划或人生目标的分歧",
        "situations": [
            {
                "id": "marriage_timing",
                "name": "婚姻时机",
                "description": "对于何时结婚或是否结婚的意见不一致",
                "example": "女方希望两年内结婚并生子，男方则想等事业更稳定后再考虑",
                "typical_triggers": ["家庭压力", "朋友结婚", "年龄焦虑"]
            },
            {
                "id": "relocation_conflict",
                "name": "搬迁冲突",
                "description": "一方因工作或其他原因需要搬迁，导致关系面临挑战",
                "example": "男方获得国外工作机会，女方不愿离开家乡和家人",
                "typical_triggers": ["工作机会", "城市偏好", "家庭依恋"]
            }
        ]
    },
    {
        "id": "boundary_issues",
        "name": "边界问题",
        "description": "关于个人空间、隐私和决策自主权的冲突",
        "situations": [
            {
                "id": "privacy_concerns",
                "name": "隐私顾虑",
                "description": "关于个人隐私和界限的争议",
                "example": "女方翻看男方手机消息，男方感到隐私被侵犯并产生信任危机",
                "typical_triggers": ["手机使用", "社交媒体互动", "独处时间需求"]
            },
            {
                "id": "family_involvement",
                "name": "家庭介入",
                "description": "一方家庭过度介入关系决策或日常生活的问题",
                "example": "男方父母频繁干预二人生活决策，女方感到不被尊重",
                "typical_triggers": ["频繁家庭聚会", "决策需征求家人意见", "过度依赖父母"]
            }
        ]
    }
] 