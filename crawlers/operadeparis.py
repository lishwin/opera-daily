"""
巴黎歌剧院 (Opéra national de Paris) 爬虫
Source: https://www.operadeparis.fr/agenda
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from models import Performance, Artist
from crawlers.base import BaseCrawler


class OperaDeParisCrawler(BaseCrawler):
    """巴黎歌剧院爬虫 - 爬取 https://www.operadeparis.fr/agenda"""

    def __init__(self):
        super().__init__("opera_national_de_paris")
        self.base_url = "https://www.operadeparis.fr"
        self.agenda_url = f"{self.base_url}/agenda"

    def fetch_performances(self) -> list[Performance]:
        performances = []
        session = self._get_session()

        try:
            resp = session.get(self.agenda_url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[OperaDeParis] Error fetching agenda: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")

        # Paris Opera renders events via JavaScript. Try to find JSON data in __NEXT_DATA__ or similar
        # Pattern: look for script tags with json data
        perf_blocks = soup.select('[class*="event"], [class*="spectacle"], [class*="card"], article, [class*="item"]')

        # If no content found in HTML, try to parse from embedded JSON-LD or script data
        for script in soup.select("script"):
            text = script.string or ""
            if "application/ld+json" in (script.get("type", "")):
                try:
                    import json
                    data = json.loads(text)
                    if isinstance(data, dict):
                        items = [data]
                    else:
                        items = data
                    for item in items:
                        if item.get("@type") in ("Event", "TheaterEvent", "MusicEvent"):
                            p = Performance(
                                title=item.get("name", ""),
                                date=item.get("startDate", ""),
                                url=item.get("url", ""),
                                description=item.get("description", ""),
                            )
                            if p.title:
                                performances.append(p)
                except (json.JSONDecodeError, KeyError):
                    continue
            # Try __INITIAL_STATE__ or __NEXT_DATA__
            if "__NEXT_DATA__" in text or "__INITIAL_STATE__" in text or "window.__NUXT__" in text:
                try:
                    import json
                    # Extract JSON object
                    match = re.search(r'({.*})', text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))
                        self._parse_json_data(data, performances)
                except (json.JSONDecodeError, AttributeError):
                    continue

        # Fallback: try to parse HTML cards if JS-rendered data wasn't found
        if not performances:
            performances = self._parse_html_cards(soup)

        return performances

    def _parse_html_cards(self, soup: BeautifulSoup) -> list[Performance]:
        """Fallback HTML parsing for card elements"""
        performances = []
        # Common selectors for event cards
        selectors = [
            '[class*="event"]', '[class*="card"]', 'article',
            '[class*="teaser"]', '[class*="listing"] > li', '[class*="grid"] > div',
            '[data-component="EventCard"]', '[class*="AgendaCard"]',
        ]
        for sel in selectors:
            cards = soup.select(sel)
            if len(cards) > 3:
                for card in cards:
                    title_el = card.select_one("h3, h2, [class*='title'], [class*='name']")
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    if not title:
                        continue

                    date_el = card.select_one("[class*='date'], time, [datetime]")
                    date_str = ""
                    if date_el:
                        date_str = date_el.get("datetime", "") or date_el.get_text(strip=True)

                    link_el = card.select_one("a[href]")
                    url = ""
                    if link_el:
                        href = link_el.get("href", "")
                        url = href if href.startswith("http") else f"{self.base_url}{href}"

                    desc_el = card.select_one("[class*='desc'], p")
                    desc = desc_el.get_text(strip=True) if desc_el else ""

                    p = Performance(
                        title=title,
                        date=date_str,
                        url=url,
                        description=desc,
                    )
                    performances.append(p)
                if performances:
                    break
        return performances

    def _parse_json_data(self, data: dict, performances: list):
        """Recursively parse JSON data for event information"""
        if isinstance(data, dict):
            if data.get("@type") in ("Event", "TheaterEvent", "MusicEvent", "TheaterGroup"):
                title = data.get("name", "")
                if title:
                    p = Performance(
                        title=title,
                        date=data.get("startDate", ""),
                        url=data.get("url", ""),
                        description=data.get("description", ""),
                    )
                    # Avoid duplicates
                    if not any(x.title == p.title and x.date == p.date for x in performances):
                        performances.append(p)
            for v in data.values():
                self._parse_json_data(v, performances)
        elif isinstance(data, list):
            for item in data:
                self._parse_json_data(item, performances)