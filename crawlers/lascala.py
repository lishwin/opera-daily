"""
米兰斯卡拉歌剧院 (Teatro alla Scala) 爬虫
Source: https://www.teatroallascala.org/en/season/calendar.html
API: https://www.teatroallascala.org/api/calendar
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta

from models import Performance, Artist
from crawlers.base import BaseCrawler


class LaScalaCrawler(BaseCrawler):
    """斯卡拉歌剧院爬虫"""

    def __init__(self):
        super().__init__("la_scala")
        self.base_url = "https://www.teatroallascala.org"
        self.calendar_url = f"{self.base_url}/en/season/calendar.html"

    def fetch_performances(self) -> list[Performance]:
        performances = []
        session = self._get_session()

        # Try HTML scraping - La Scala renders calendar as HTML
        try:
            resp = session.get(self.calendar_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            performances = self._parse_html(soup)
        except requests.RequestException as e:
            print(f"[LaScala] Error fetching calendar: {e}")

        if performances:
            return performances

        # Fallback: try XML/JSON endpoints
        try:
            # La Scala sometimes uses a JSON API
            api_url = f"{self.base_url}/api/events?lang=en"
            resp = session.get(api_url, timeout=15, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                performances = self._parse_api(data)
        except (requests.RequestException, json.JSONDecodeError):
            pass

        return performances

    def _parse_html(self, soup: BeautifulSoup) -> list[Performance]:
        """Parse the HTML calendar page"""
        performances = []

        # La Scala calendar typically uses a table or grid layout
        event_items = soup.select(
            '[class*="event"], [class*="calendar-item"], [class*="card-"]'
            '[class*="grid-item"], [data-event], tr.calendar-row, .item, article'
        )

        for item in event_items:
            title_el = item.select_one("h2, h3, h4, [class*='title'], [class*='name'], strong")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            # Date
            date_el = item.select_one("time, [class*='date'], [datetime], [class*='giorno']")
            date_str = ""
            if date_el:
                date_str = date_el.get("datetime", "") or date_el.get_text(strip=True)

            # Link
            link_el = item.select_one("a[href]")
            url = ""
            if link_el:
                href = link_el.get("href", "")
                url = href if href.startswith("http") else f"{self.base_url}{href}"

            # Description / composer hint
            desc_el = item.select_one("p, [class*='desc'], [class*='info'], [class*='composer']")
            desc = desc_el.get_text(strip=True) if desc_el else ""

            # Venue
            venue_el = item.select_one("[class*='venue'], [class*='location'], [class*='sala']")
            venue = venue_el.get_text(strip=True) if venue_el else ""

            p = Performance(title=title, date=date_str, url=url,
                          description=desc, venue=venue)
            performances.append(p)

        return performances

    def _parse_api(self, data: dict) -> list[Performance]:
        """Parse JSON API response"""
        performances = []
        events = data.get("events", data.get("data", data.get("items", [data])))
        if isinstance(events, dict):
            events = [events]

        for ev in events:
            title = (ev.get("title") or ev.get("name") or "")
            if not title:
                continue
            p = Performance(
                title=title,
                date=ev.get("date", ev.get("startDate", "")),
                time=ev.get("time", ev.get("hour", "")),
                venue=ev.get("venue", ev.get("location", "")),
                url=ev.get("url", ev.get("link", "")),
                description=ev.get("description", ""),
            )
            performances.append(p)
        return performances