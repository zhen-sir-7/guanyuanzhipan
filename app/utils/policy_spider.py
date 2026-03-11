import requests
from bs4 import BeautifulSoup
import config
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def crawl_policy(keyword):
    """根据关键词爬取政策信息"""
    policies = []
    keyword_lower = keyword.lower()

    try:
        policy_urls = config.POLICY_URLS
    except AttributeError:
        policy_urls = {}
    try:
        search_configs = config.SEARCH_CONFIGS
    except AttributeError:
        search_configs = {}
    try:
        headers = config.REQUEST_HEADERS
    except AttributeError:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    for source_name, cfg in search_configs.items():
        try:
            policies.extend(_search_by_form(
                session=session,
                name=source_name,
                search_page_url=cfg.get("search_page_url"),
                form_selector=cfg.get("form_selector"),
                keyword_field=cfg.get("keyword_field", "keyWords"),
                extra_fields=cfg.get("extra_fields", {}),
                result_selector=cfg.get("result_selector"),
                date_selector=cfg.get("date_selector"),
                keyword=keyword
            ))
        except Exception as e:
            logger.error(f"{source_name} 表单搜索失败：{e}", exc_info=True)

    if not policies:
        policies = _fallback_list_mode(session, policy_urls, headers, keyword_lower)

    seen = set()
    unique = []
    for p in policies:
        key = (p["title"], p["url"])
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique[:10]

def _search_by_form(session, name, search_page_url, form_selector, keyword_field,
                    extra_fields, result_selector, date_selector, keyword):
    if not search_page_url:
        logger.warning(f"{name} 未配置 search_page_url，跳过")
        return []

    logger.info(f"{name}：正在获取搜索页面 {search_page_url}")
    resp = session.get(search_page_url, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or 'utf-8'
    soup = BeautifulSoup(resp.text, "html.parser")

    if form_selector:
        form = soup.select_one(form_selector)
        if not form:
            raise Exception(f"未找到匹配选择器 '{form_selector}' 的表单")
    else:
        form = soup.find("form")
        if not form:
            raise Exception("页面中找不到任何表单")
    logger.info(f"{name}：找到表单，action={form.get('action')}")

    form_action = form.get("action")
    if not form_action:
        raise Exception("表单缺少 action 属性")
    post_url = urljoin(search_page_url, form_action)

    form_data = {}
    for hidden in form.find_all("input", type="hidden"):
        name_attr = hidden.get("name")
        value = hidden.get("value", "")
        if name_attr:
            form_data[name_attr] = value
    form_data.update(extra_fields)
    form_data[keyword_field] = keyword

    logger.info(f"{name}：提交POST到 {post_url}，数据：{form_data}")
    resp = session.post(post_url, data=form_data, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or 'utf-8'
    soup = BeautifulSoup(resp.text, "html.parser")

    items = soup.select(result_selector) if result_selector else soup.find_all("a", href=True, limit=50)
    results = []
    for a in items:
        title = a.get('title') or a.get_text(strip=True)
        if not title:
            continue
        href = a["href"]
        full_url = urljoin(post_url, href)
        publish_time = ""
        if date_selector:
            parent = a.find_parent()
            if parent:
                time_tag = parent.select_one(date_selector)
                if time_tag:
                    publish_time = time_tag.get_text(strip=True)
        results.append({
            "title": title,
            "url": full_url,
            "source": name,
            "time": publish_time
        })
    logger.info(f"{name} 获取到 {len(results)} 条结果")
    return results

def _fallback_list_mode(session, policy_urls, headers, keyword_lower):
    policies = []
    for name, url in policy_urls.items():
        if not url:
            continue
        try:
            logger.info(f"列表模式抓取 {name}，URL: {url}")
            resp = session.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True, limit=50):
                title = a.get_text(strip=True)
                if title and keyword_lower in title.lower():
                    href = a["href"]
                    full_url = urljoin(url, href)
                    policies.append({
                        "title": title,
                        "url": full_url,
                        "source": name,
                        "time": ""
                    })
        except Exception as e:
            logger.error(f"{name} 列表模式失败：{e}")
    return policies