# config/seeds.py
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SiteConfig:
    name: str
    seed_urls: List[str]
    allowed_domains: List[str]
    article_path_patterns: List[str]      # regex patterns for article URLs
    category_path_patterns: List[str]     # regex patterns for category/archive pages
    deny_patterns: List[str]              # patterns to always skip
    requires_js: bool = False
    crawl_depth: int = 3
    rate_limit_delay: float = 1.5         # seconds between requests

SEED_SITES = [
    SiteConfig(
        name="thehackernews",
        seed_urls=[
            "https://thehackernews.com/",
            "https://thehackernews.com/search/label/Vulnerability",
            "https://thehackernews.com/search/label/Malware",
            "https://thehackernews.com/search/label/Data Breach",
        ],
        allowed_domains=["thehackernews.com"],
        article_path_patterns=[r"/\d{4}/\d{2}/.+\.html$"],
        category_path_patterns=[r"/search/label/.+", r"/p/archive\.html"],
        deny_patterns=[r"/cdn-cgi/", r"#", r"javascript:"],
        rate_limit_delay=1.5,
    ),
    SiteConfig(
        name="bleepingcomputer",
        seed_urls=[
            "https://www.bleepingcomputer.com/",
            "https://www.bleepingcomputer.com/news/security/",
            "https://www.bleepingcomputer.com/news/vulnerabilities-and-exploits/",
            "https://www.bleepingcomputer.com/tag/ransomware/",
        ],
        allowed_domains=["bleepingcomputer.com"],
        article_path_patterns=[r"/news/.+/.+/$"],
        category_path_patterns=[r"/news/[a-z-]+/$", r"/tag/[a-z-]+/"],
        deny_patterns=[r"/forums/", r"/download/", r"/contact", r"/about"],
        rate_limit_delay=2.0,
    ),
    SiteConfig(
        name="securityweek",
        seed_urls=[
            "https://www.securityweek.com/",
            "https://www.securityweek.com/category/vulnerabilities/",
            "https://www.securityweek.com/category/malware-threats/",
            "https://www.securityweek.com/category/cyberwarfare/",
        ],
        allowed_domains=["securityweek.com"],
        article_path_patterns=[r"/[a-z0-9-]+-\d+/$", r"/[a-z0-9-]+/$"],
        category_path_patterns=[r"/category/[a-z-]+/", r"/category/[a-z-]+/page/\d+/"],
        deny_patterns=[r"/advertise", r"/privacy", r"/careers", r"/contact"],
        rate_limit_delay=1.5,
    ),
    SiteConfig(
        name="darkreading",
        seed_urls=[
            "https://www.darkreading.com/",
            "https://www.darkreading.com/vulnerabilities-threats",
            "https://www.darkreading.com/threat-intelligence",
            "https://www.darkreading.com/attacks-breaches",
        ],
        allowed_domains=["darkreading.com"],
        article_path_patterns=[r"/[a-z-]+/[a-z0-9-]+$"],
        category_path_patterns=[r"/[a-z-]+$", r"/[a-z-]+/\d+$"],
        deny_patterns=[r"/about", r"/contact", r"/privacy", r"/events"],
        rate_limit_delay=1.5,
    ),
    SiteConfig(
        name="krebsonsecurity",
        seed_urls=[
            "https://krebsonsecurity.com/",
            "https://krebsonsecurity.com/category/data-breaches/",
            "https://krebsonsecurity.com/category/malware/",
            "https://krebsonsecurity.com/category/web-fraud-2-0/",
        ],
        allowed_domains=["krebsonsecurity.com"],
        article_path_patterns=[r"/\d{4}/\d{2}/[a-z0-9-]+/$"],
        category_path_patterns=[r"/category/[a-z0-9-]+/", r"/category/[a-z0-9-]+/page/\d+/"],
        deny_patterns=[r"/about", r"/contact", r"/privacy"],
        rate_limit_delay=2.0,
    ),
]