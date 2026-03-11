# 规则类型
RULE_TYPES = {
    'RVC': '区域价值成分',
    'CTC': '税则归类改变',
    'WO': '完全获得',
    'DM': '直接材料'
}

# CTC改变级别映射
CTC_LEVELS = {
    'CC': 2,      # 章改变
    'CTH': 4,     # 品目改变
    'CTSH': 6     # 子目改变
}

# 默认RVC阈值
DEFAULT_RVC_THRESHOLD = 40

# 分页默认值
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 10

# 会话过期时间（秒）
SESSION_LIFETIME = 3600  # 1小时
REMEMBER_ME_LIFETIME = 7 * 24 * 3600  # 7天