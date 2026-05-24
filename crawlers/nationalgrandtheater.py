"""
中国国家大剧院 (National Centre for the Performing Arts) 爬虫
Source: https://www.chncpa.org/performance/index.html
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import re
import requests
from bs4 import BeautifulSoup

from models import Performance, Artist
from crawlers.base import BaseCrawler


class NationalGrandTheaterCrawler(BaseCrawler):
    """中国国家大剧院爬虫"""

    def __init__(self):
        super().__init__("national_centre_for_the_performing_arts")
        self.base_url = "https://www.chncpa.org"
        self.calendar_url = f"{self.base_url}/performance/index.html"
        # API endpoint used by the NCPA website
        self.api_url = "https://api.chncpa.org/api/v1/performances"

    def fetch_performances(self) -> list[Performance]:
        performances = []
        session = self._get_session()

        # Try API
        try:
            resp = session.get(self.api_url, timeout=15,
                               headers={"Accept": "application/json"},
                               params={"pageSize": 50, "pageNum": 1})
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    perfs = self._parse_api(data)
                    if perfs:
                        return perfs
                except (json.JSONDecodeError, KeyError):
                    pass
        except requests.RequestException:
            pass

        # Try alternative API path
        try:
            resp = session.get(f"{self.base_url}/api/performance/list",
                               timeout=15, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    perfs = self._parse_api(data)
                    if perfs:
                        return perfs
                except (json.JSONDecodeError, KeyError):
                    pass
        except requests.RequestException:
            pass

        # Fallback: scrape HTML
        try:
            resp = session.get(self.calendar_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            performances = self._parse_html(soup)
        except requests.RequestException as e:
            print(f"[NCPA] Error: {e}")

        return performances

    def _parse_api(self, data: dict) -> list[Performance]:
        """Parse NCPA API response"""
        performances = []
        items = data.get("data", data.get("results", data.get("list", data.get("items", [data]))))
        if isinstance(items, dict):
            items = [items]
        if isinstance(items, list):
            for item in items:
                title = (item.get("name") or item.get("title") or
                        item.get("performanceName", ""))
                if not title:
                    continue
                p = Performance(
                    title=title,
                    composer=item.get("composer", ""),
                    date=item.get("date", item.get("startDate", item.get("performanceDate", ""))),
                    time=item.get("time", item.get("startTime", "")),
                    venue=item.get("venue", item.get("location", "")),
                    url=item.get("url", item.get("link", "")),
                    description=item.get("description", item.get("introduction", "")),
                    language=item.get("language", ""),
                )
                performances.append(p)

        return performances

    def _parse_html(self, soup: BeautifulSoup) -> list[Performance]:
        """Parse NCPA HTML"""
        performances = []

        cards = soup.select('[class*="card"], [class*="item"], [class*="list-item"], '
                           '[class*="performance"], [class*="show"], article, li')
        for card in cards:
            title_el = card.select_one("h2, h3, h4, a, [class*='title'], [class*='name'], strong")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or len(title) < 2:
                continue

            date_el = card.select_one("time, [class*='date'], [class*='time'], [datetime]")
            date_str = date_el.get("datetime", "") if date_el else (date_el.get_text(strip=True) if date_el else "")

            link_el = card.select_one("a[href]")
            href = link_el.get("href", "") if link_el else ""
            url = href if href.startswith("http") else f"{self.base_url}{href}" if href else ""

            p = Performance(title=title, date=date_str, url=url)
            performances.append(p)
        return performances