"""
拜罗伊特节日剧院 (Bayreuther Festspiele) 爬虫
Source: https://www.bayreuther-festspiele.de/en/programme/
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


class BayreuthCrawler(BaseCrawler):
    """拜罗伊特节日剧院爬虫"""

    def __init__(self):
        super().__init__("bayreuth_festspielhaus")
        self.base_url = "https://www.bayreuther-festspiele.de"
        self.calendar_url = f"{self.base_url}/en/programme/"

    def fetch_performances(self) -> list[Performance]:
        performances = []
        session = self._get_session()

        # Bayreuth festival typically lists all performances for the upcoming summer
        try:
            resp = session.get(self.calendar_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            performances = self._parse_html(soup)
        except requests.RequestException as e:
            print(f"[Bayreuth] Error: {e}")

        return performances

    def _parse_html(self, soup: BeautifulSoup) -> list[Performance]:
        """Parse Bayreuth festival programme page"""
        performances = []

        items = soup.select('[class*="event"], [class*="card"], article, '
                           '[class*="program-item"], [class*="production"], '
                           '[class*="werk"], [class*="auffuehrung"]')

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

            composer_el = item.select_one("[class*='composer'], .artist, [class*='autor']")
            composer = composer_el.get_text(strip=True) if composer_el else ""

            p = Performance(title=title, date=date_str, url=url, composer=composer)

            # Check for conductor/director info
            details = item.get_text(" ", strip=True)
            for match in re.finditer(r'(Conductor|Dirigent|Director|Regie|Inszenierung)\s*[:\-]?\s*([A-Za-zÀ-ÖØ-öø-ÿ\s\.]+)', details):
                role = match.group(1)
                name = match.group(2).strip()
                if name and len(name) > 2:
                    if "conductor" in role.lower() or "dirigent" in role.lower():
                        p.conductors.append(Artist(name=name, role=role))
                    else:
                        p.directors.append(Artist(name=name, role=role))

            performances.append(p)
        return performances