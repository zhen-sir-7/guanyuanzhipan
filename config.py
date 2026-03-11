import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库
DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'origin_system.db')}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 密钥
SECRET_KEY = "origin_system_2026_secret_key"

# 爬虫
POLICY_URLS = {
    "customs": "http://www.customs.gov.cn/customs/xwfb34/302425/index.html",
    "mofcom": "http://www.mofcom.gov.cn/article/b/g/"
}

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

# RVC阈值配置
RVC_THRESHOLD = {
    "RCEP": {
        "methods": [
            {"type": "fob", "threshold": 40, "description": "FOB价法"},
            {"type": "net_cost", "threshold": 35, "description": "净成本法"}
        ],
        "description": "RCEP原产地规则"
    },
    "CAI": {
        "calculation_type": "fob",
        "threshold": 50,
        "description": "CAI规则"
    }
}

# 搜索配置
SEARCH_CONFIGS = {
    "customs": {
        "search_page_url": "http://www.customs.gov.cn/",
        "form_selector": "form[action*='search.customs.gov.cn']",
        "keyword_field": "keyWords",
        "extra_fields": {},
        "result_selector": ".news_list li a",
        "date_selector": "span"
    },
    "mofcom": {}
}