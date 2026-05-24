"""
马德里皇家剧院 (Teatro Real) 爬虫
Source: https://www.teatroreal.es/en/programming
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


class TeatroRealCrawler(BaseCrawler):
    """马德里皇家剧院爬虫"""

    def __init__(self):
        super().__init__("teatro_real")
        self.base_url = "https://www.teatroreal.es"
        self.calendar_url = f"{self.base_url}/en/programming"

    def fetch_performances(self) -> list[Performance]:
        performances = []
        session = self._get_session()

        # Try API
        try:
            resp = session.get(f"{self.base_url}/api/v1/events", timeout=15,
                               headers={"Accept": "application/json"})
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

        # Try alternative API
        try:
            resp = session.get(f"{self.base_url}/en/api/calendar", timeout=15,
                               headers={"Accept": "application/json"})
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
            print(f"[TeatroReal] Error: {e}")

        return performances

    def _parse_api(self, data: dict) -> list[Performance]:
        performances = []
        events = data.get("events", data.get("data", data.get("results", [data])))
        if isinstance(events, dict):
            events = [events]

        for ev in events:
            title = (ev.get("title") or ev.get("name") or
                    ev.get("production", {}).get("title", ""))
            if not title:
                continue

            p = Performance(
                title=title,
                composer=ev.get("composer", ""),
                date=ev.get("date", ev.get("startDate", "")),
                time=ev.get("time", ev.get("startTime", "")),
                venue=ev.get("venue", ev.get("location", "Teatro Real")),
                url=ev.get("url", ev.get("link", "")),
                description=ev.get("description", ""),
            )
            performances.append(p)
        return performances

    def _parse_html(self, soup: BeautifulSoup) -> list[Performance]:
        performances = []
        cards = soup.select('[class*="event"], .card, article, [class*="item"], [class*="program-item"]')
        for card in cards:
            title_el = card.select_one("h2, h3, h4, a, [class*='title'], strong")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            date_el = card.select_one("time, [class*='date'], [datetime]")
            date_str = date_el.get("datetime", "") if date_el else (date_el.get_text(strip=True) if date_el else "")

            link_el = card.select_one("a[href]")
            href = link_el.get("href", "") if link_el else ""
            url = href if href.startswith("http") else f"{self.base_url}{href}"

            p = Performance(title=title, date=date_str, url=url)
            performances.append(p)
        return performances