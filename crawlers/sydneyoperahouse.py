"""
悉尼歌剧院 (Sydney Opera House) 爬虫
Source: https://www.sydneyoperahouse.com/whats-on
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


class SydneyOperaHouseCrawler(BaseCrawler):
    """悉尼歌剧院爬虫"""

    def __init__(self):
        super().__init__("sydney_opera_house")
        self.base_url = "https://www.sydneyoperahouse.com"
        self.calendar_url = f"{self.base_url}/whats-on"

    def fetch_performances(self) -> list[Performance]:
        performances = []
        session = self._get_session()

        # Try API
        api_urls = [
            "https://www.sydneyoperahouse.com/api/events?page=1&limit=50",
            "https://www.sydneyoperahouse.com/api/v1/events",
            "https://www.sydneyoperahouse.com/api/whatson",
        ]
        for api_url in api_urls:
            try:
                resp = session.get(api_url, timeout=15,
                                   headers={"Accept": "application/json"})
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        perfs = self._parse_api(data)
                        if perfs:
                            return perfs
                    except (json.JSONDecodeError, KeyError):
                        continue
            except requests.RequestException:
                continue

        # Fallback: scrape HTML
        try:
            resp = session.get(self.calendar_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            performances = self._parse_html(soup)
        except requests.RequestException as e:
            print(f"[SydneyOH] Error: {e}")

        return performances

    def _parse_api(self, data: dict) -> list[Performance]:
        """Parse JSON API response"""
        performances = []
        events = data.get("events", data.get("data", data.get("results", data.get("items", [data]))))
        if isinstance(events, dict):
            events = [events]

        for ev in events:
            title = (ev.get("title") or ev.get("name") or ev.get("eventName") or "")
            if not title:
                continue

            p = Performance(
                title=title,
                composer=ev.get("composer", ev.get("artist", "")),
                date=ev.get("date", ev.get("startDate", ev.get("eventDate", ""))),
                time=ev.get("time", ev.get("startTime", "")),
                venue=ev.get("venue", ev.get("location", ev.get("theatre", ""))),
                url=ev.get("url", ev.get("link", ev.get("eventUrl", ""))),
                description=ev.get("description", ev.get("shortDescription", "")),
            )
            performances.append(p)
        return performances

    def _parse_html(self, soup: BeautifulSoup) -> list[Performance]:
        """Fallback HTML parsing"""
        performances = []
        cards = soup.select('[class*="card"], article, [class*="event"], [class*="show"], [class*="performance"]')
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