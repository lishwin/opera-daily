"""
萨尔茨堡音乐节 (Salzburg Festival) 爬虫
Source: https://www.salzburgerfestspiele.at/en/program
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


class SalzburgFestivalCrawler(BaseCrawler):
    """萨尔茨堡音乐节爬虫"""

    def __init__(self):
        super().__init__("salzburg_festival")
        self.base_url = "https://www.salzburgerfestspiele.at"
        self.calendar_url = f"{self.base_url}/en/program"

    def fetch_performances(self) -> list[Performance]:
        performances = []
        session = self._get_session()

        try:
            resp = session.get(self.calendar_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            performances = self._parse_html(soup)
        except requests.RequestException as e:
            print(f"[Salzburg] Error: {e}")

        return performances

    def _parse_html(self, soup: BeautifulSoup) -> list[Performance]:
        performances = []
        items = soup.select('[class*="event"], [class*="card"], article, [class*="program-item"], [class*="teaser"]')

        for item in items:
            title_el = item.select_one("h2, h3, h4, [class*='title'], a, strong")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            date_el = item.select_one("time, [class*='date'], [datetime]")
            date_str = date_el.get("datetime", "") if date_el else (date_el.get_text(strip=True) if date_el else "")

            link_el = item.select_one("a[href]")
            href = link_el.get("href", "") if link_el else ""
            url = href if href.startswith("http") else f"{self.base_url}{href}"

            venue_el = item.select_one("[class*='venue'], [class*='location']")
            venue = venue_el.get_text(strip=True) if venue_el else ""

            p = Performance(title=title, date=date_str, url=url, venue=venue)
            performances.append(p)

        return performances