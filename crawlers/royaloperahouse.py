"""
英国皇家歌剧院 (Royal Opera House) 爬虫
Source: https://www.roh.org.uk/tickets-and-events
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


class RoyalOperaHouseCrawler(BaseCrawler):
    """皇家歌剧院爬虫"""

    def __init__(self):
        super().__init__("royal_opera_house")
        self.base_url = "https://www.roh.org.uk"
        self.calendar_url = f"{self.base_url}/tickets-and-events"

    def fetch_performances(self) -> list[Performance]:
        performances = []
        session = self._get_session()

        # Try API
        try:
            api_url = "https://www.roh.org.uk/api/events?page=1&pageSize=50"
            resp = session.get(api_url, timeout=30,
                               headers={"Accept": "application/json"})
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    performances = self._parse_api(data)
                    if performances:
                        return performances
                except (json.JSONDecodeError, KeyError):
                    pass
        except requests.RequestException:
            pass

        # Try another API endpoint
        try:
            api_url = "https://www.roh.org.uk/api/events/calendar"
            resp = session.get(api_url, timeout=15,
                               headers={"Accept": "application/json"})
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    performances = self._parse_api(data)
                    if performances:
                        return performances
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
            print(f"[ROH] Error: {e}")

        return performances

    def _parse_api(self, data: dict) -> list[Performance]:
        """Parse ROH API response"""
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
                venue=ev.get("venue", ev.get("location", "Royal Opera House")),
                url=ev.get("url", ev.get("link", "")),
                description=ev.get("description", ev.get("shortDescription", "")),
            )

            # Cast
            for artist_data in ev.get("cast", ev.get("artists", [])):
                if isinstance(artist_data, dict):
                    name = artist_data.get("name", "")
                    role = (artist_data.get("role", "") or
                           artist_data.get("function", ""))
                    if name:
                        rl_lower = role.lower()
                        if "conductor" in rl_lower:
                            p.conductors.append(Artist(name=name, role=role))
                        elif "director" in rl_lower:
                            p.directors.append(Artist(name=name, role=role))
                        else:
                            p.cast.append(Artist(name=name, role=role))
            performances.append(p)
        return performances

    def _parse_html(self, soup: BeautifulSoup) -> list[Performance]:
        """Fallback HTML parsing"""
        performances = []
        cards = soup.select(
            '[class*="event"], .card, article, [class*="performance"], '
            '[class*="production-card"], [class*="listing-item"]'
        )
        for card in cards:
            title_el = card.select_one("h2, h3, h4, a, [class*='title'], strong")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            date_el = card.select_one("time, [class*='date'], [datetime], [class*='month'], [class*='day']")
            date_str = date_el.get("datetime", "") if date_el else (date_el.get_text(strip=True) if date_el else "")

            link_el = card.select_one("a[href]")
            href = link_el.get("href", "") if link_el else ""
            url = href if href.startswith("http") else f"{self.base_url}{href}"

            p = Performance(title=title, date=date_str, url=url)
            performances.append(p)
        return performances