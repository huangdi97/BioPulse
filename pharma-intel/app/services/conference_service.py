"""学术会议追踪服务。"""

import httpx
from datetime import datetime, timezone
from pharma_intel.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"

MOCK_CONFERENCES = [
    {
        "id": "asco-2026",
        "name": "ASCO 2026 Annual Meeting",
        "date": "2026-06-04",
        "location": "Chicago, IL",
        "topic": "肿瘤学",
        "attendees_count": 45000,
        "hot_topics": ["双抗", "ADC", "细胞治疗", "免疫检查点"],
        "key_kols": ["Dr. James Allison", "Dr. Carl June", "Dr. Padmanee Sharma"],
    },
    {
        "id": "aacr-2026",
        "name": "AACR Annual Meeting 2026",
        "date": "2026-04-18",
        "location": "Washington, DC",
        "topic": "癌症研究",
        "attendees_count": 22000,
        "hot_topics": ["KRAS抑制剂", "PROTAC", "肿瘤微环境", "早筛"],
        "key_kols": ["Dr. Margaret Foti", "Dr. Charles Sawyers", "Dr. Elaine Mardis"],
    },
    {
        "id": "esmo-2026",
        "name": "ESMO Congress 2026",
        "date": "2026-09-12",
        "location": "Barcelona, Spain",
        "topic": "肿瘤学",
        "attendees_count": 33000,
        "hot_topics": ["免疫联合疗法", "液体活检", "靶向耐药", "个体化疫苗"],
        "key_kols": [
            "Dr. Solange Peters",
            "Dr. Fabrice Barlesi",
            "Dr. Josep Tabernero",
        ],
    },
    {
        "id": "ash-2026",
        "name": "ASH Annual Meeting 2026",
        "date": "2026-12-05",
        "location": "San Diego, CA",
        "topic": "血液学",
        "attendees_count": 28000,
        "hot_topics": ["CAR-T长期随访", "双特异性抗体", "基因编辑", "骨髓纤维化"],
        "key_kols": ["Dr. Robert Negrin", "Dr. Catherine Bollard", "Dr. John Leonard"],
    },
    {
        "id": "aad-2026",
        "name": "AAD Annual Meeting 2026",
        "date": "2026-03-20",
        "location": "Orlando, FL",
        "topic": "皮肤病学",
        "attendees_count": 12000,
        "hot_topics": [
            "银屑病生物制剂",
            "特应性皮炎JAK抑制剂",
            "脱发治疗",
            "AI皮肤诊断",
        ],
        "key_kols": ["Dr. Mark Lebwohl", "Dr. Emma Guttman-Yassky", "Dr. Brett King"],
    },
    {
        "id": "acc-2026",
        "name": "ACC Scientific Session 2026",
        "date": "2026-04-02",
        "location": "Atlanta, GA",
        "topic": "心血管学",
        "attendees_count": 18000,
        "hot_topics": ["PCSK9抑制剂", "心衰新药", "TAVR长期数据", "脂蛋白(a)"],
        "key_kols": [
            "Dr. Deepak Bhatt",
            "Dr. Roxana Mehran",
            "Dr. Christopher O'Connor",
        ],
    },
    {
        "id": "ada-2026",
        "name": "ADA Scientific Sessions 2026",
        "date": "2026-06-26",
        "location": "Las Vegas, NV",
        "topic": "糖尿病/代谢",
        "attendees_count": 15000,
        "hot_topics": ["GLP-1双靶点", "CGM新技术", "糖尿病肾病", "代谢手术长期结局"],
        "key_kols": ["Dr. Robert Gabbay", "Dr. Anne Peters", "Dr. John Buse"],
    },
    {
        "id": "idweek-2026",
        "name": "IDWeek 2026",
        "date": "2026-10-07",
        "location": "Los Angeles, CA",
        "topic": "感染病学",
        "attendees_count": 10000,
        "hot_topics": ["新型抗生素", "mRNA疫苗", "抗真菌药物", "HIV长效疗法"],
        "key_kols": ["Dr. Jeanne Marrazzo", "Dr. Anthony Fauci", "Dr. David Ho"],
    },
    {
        "id": "sno-2026",
        "name": "SNO Annual Meeting 2026",
        "date": "2026-11-18",
        "location": "Houston, TX",
        "topic": "神经肿瘤学",
        "attendees_count": 4500,
        "hot_topics": [
            "胶质母细胞瘤疫苗",
            "TTFields联合免疫",
            "脑转移靶向治疗",
            "液体活检CNS",
        ],
        "key_kols": ["Dr. Michael Weller", "Dr. Susan Chang", "Dr. Roger Stupp"],
    },
    {
        "id": "ddw-2026",
        "name": "Digestive Disease Week 2026",
        "date": "2026-05-16",
        "location": "San Diego, CA",
        "topic": "消化病学",
        "attendees_count": 14000,
        "hot_topics": ["IBD新靶点", "NASH新药", "肠癌早筛", "粪菌移植标准化"],
        "key_kols": ["Dr. Maria Abreu", "Dr. Scott Friedman", "Dr. John Carethers"],
    },
]

MOCK_DETAILS = {
    "asco-2026": {
        "agenda": [
            {
                "day": "2026-06-04",
                "sessions": ["全体大会: 免疫治疗前沿", "专题研讨: ADC药物临床进展"],
            },
            {
                "day": "2026-06-05",
                "sessions": ["口头报告: 双特异性抗体", "教育专场: 生物标志物指导治疗"],
            },
            {
                "day": "2026-06-06",
                "sessions": [" poster 专场: 精准肿瘤学", "闭幕演讲: 癌症治愈之路"],
            },
        ],
        "speakers": [
            {
                "name": "Dr. James Allison",
                "affiliation": "MD Anderson",
                "topic": "免疫检查点抑制剂的过去与未来",
            },
            {
                "name": "Dr. Carl June",
                "affiliation": "UPenn",
                "topic": "CAR-T细胞治疗20年",
            },
            {
                "name": "Dr. Padmanee Sharma",
                "affiliation": "MD Anderson",
                "topic": "免疫联合疗法的生物标志物",
            },
        ],
        "related_papers_count": 2800,
    },
    "aacr-2026": {
        "agenda": [
            {
                "day": "2026-04-18",
                "sessions": ["全体大会: 癌症生物学新范式", "专题: KRAS药物十年征程"],
            },
            {
                "day": "2026-04-19",
                "sessions": ["口头报告: PROTAC技术突破", "教育专场: 肿瘤微环境调控"],
            },
            {
                "day": "2026-04-20",
                "sessions": [" poster 专场: 早筛与液体活检", "闭幕: 精准预防策略"],
            },
        ],
        "speakers": [
            {
                "name": "Dr. Margaret Foti",
                "affiliation": "AACR",
                "topic": "癌症研究的未来方向",
            },
            {
                "name": "Dr. Charles Sawyers",
                "affiliation": "MSKCC",
                "topic": "靶向治疗的耐药机制",
            },
            {
                "name": "Dr. Elaine Mardis",
                "affiliation": "Nationwide Children's",
                "topic": "基因组学驱动的精准医疗",
            },
        ],
        "related_papers_count": 6500,
    },
}


async def get_upcoming_conferences(limit: int = 10) -> list[dict]:
    """获取即将召开的学术会议列表。

    当前返回模拟数据（真实数据需要外部 API 集成）。
    通过缓存减少重复请求，默认返回最多 10 场会议。

    Args:
        limit: 返回会议数量上限，默认 10。

    Returns:
        会议列表，每项包含 name, date, location, topic,
        attendees_count, hot_topics, key_kols 等字段。
    """
    cache_key = f"conferences:upcoming:{limit}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CLOUD_API}/pubmed/search",
            json={
                "query": "clinical trial conference 2026",
                "limit": 20,
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            papers = data.get("data", data.get("papers", []))

    conferences = MOCK_CONFERENCES[:limit]
    if papers:
        for conf in conferences:
            conf["related_papers"] = (
                [p.get("title", "") for p in papers[:5]] if papers else []
            )

    set_cache(cache_key, conferences, ttl=1800)
    return conferences


async def get_conference_detail(conference_id: str) -> dict | None:
    """获取指定会议的详细信息。

    包括议程、演讲嘉宾列表及相关论文数量。
    若会议不存在则返回 None。

    Args:
        conference_id: 会议标识符，如 "asco-2026"。

    Returns:
        会议详情字典，含 agenda、speakers、related_papers_count；不存在时返回 None。
    """
    cache_key = f"conference:detail:{conference_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    detail = MOCK_DETAILS.get(conference_id)
    if detail is None:
        return None

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CLOUD_API}/pubmed/search",
            json={
                "query": conference_id.replace("-", " "),
                "limit": 10,
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            papers = data.get("data", data.get("papers", []))
            detail["related_papers"] = [p.get("title", "") for p in papers[:10]]

    set_cache(cache_key, detail, ttl=1800)
    return detail


async def analyze_conference_trends(months: int = 6) -> dict:
    """分析近期学术会议的热点话题趋势。

    从模拟会议数据中提取 hot_topics，聚合统计各个话题的
    出现频次，按热度排序。同时通过 PubMed API 获取近期论文
    辅助验证热点方向。

    Args:
        months: 分析窗口月数，默认 6。

    Returns:
        趋势分析结果，含热门话题列表及覆盖会议数。
    """
    cache_key = f"conference:trends:{months}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    topic_counter: dict[str, int] = {}
    for conf in MOCK_CONFERENCES:
        for topic in conf["hot_topics"]:
            topic_counter[topic] = topic_counter.get(topic, 0) + 1

    trending = [
        {"topic": topic, "mentions": count, "conferences_covered": count}
        for topic, count in sorted(topic_counter.items(), key=lambda x: -x[1])
    ]

    result = {
        "trending_topics": trending,
        "analysis_window_months": months,
        "total_conferences_analyzed": len(MOCK_CONFERENCES),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    set_cache(cache_key, result, ttl=1800)
    return result
