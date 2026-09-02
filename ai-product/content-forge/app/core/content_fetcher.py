"""内容抓取器：抓取网页正文"""
import re
import requests
from bs4 import BeautifulSoup
from loguru import logger


class ContentFetcher:
    """网页内容抓取与正文提取"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    TIMEOUT = 15

    def fetch(self, url: str, retry: int = 2) -> str:
        """
        抓取 URL 并提取正文内容
        返回纯文本内容
        """
        for attempt in range(retry + 1):
            try:
                resp = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT, allow_redirects=True)
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding or "utf-8"
                content = self._extract_text(resp.text, url)
                if len(content) < 100:
                    logger.warning(f"抓取内容过少（{len(content)} 字），URL={url}")
                    if attempt < retry:
                        continue
                logger.info(f"成功抓取 {url}，提取正文 {len(content)} 字")
                return content
            except Exception as e:
                logger.warning(f"抓取失败（第 {attempt + 1} 次）：{url}，错误：{e}")
                if attempt >= retry:
                    raise
        return ""

    def _extract_text(self, html: str, url: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        selectors = [
            ("div", {"id": "js_content"}),
            ("div", {"class": "rich_media_content"}),
            ("article", {}),
            ("div", {"id": "article_content"}),
            ("main", {}),
            ("div", {"class": re.compile(r"content|article|post|entry|main")}),
            ("body", {}),
        ]

        for selector in selectors:
            if len(selector) == 2:
                tag_name, attrs = selector
                elem = soup.find(tag_name, attrs)
            else:
                elem = soup.find(selector)
            if elem:
                text = elem.get_text(separator="\n", strip=True)
                text = re.sub(r"\n{3,}", "\n\n", text)
                return text

        return soup.get_text(separator="\n", strip=True)

    def is_valid_url(self, url: str) -> bool:
        if not url:
            return False
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            return False
        return len(url) > 10
