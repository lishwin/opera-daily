"""
纽约大都会歌剧院 (Metropolitan Opera) 爬虫
Source: https://www.metopera.org/season/calendar/
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


class MetOperaCrawler(BaseCrawler):
    """纽约大都会歌剧院爬虫"""

    def __init__(self):
        super().__init__("metropolitan_opera")
        self.base_url = "https://www.metopera.org"
        self.calendar_url = f"{self.base_url}/season/calendar"

    def fetch_performances(self) -> list[Performance]:
        performances = []
        session = self._get_session()

        # Met Opera uses a JSON API for the calendar
        try:
            api_url = "https://www.metopera.org/api/calendar/v1/events"
            resp = session.get(api_url, timeout=30,
                               headers={"Accept": "application/json, text/plain, */*"})
            if resp.status_code == 200 and resp.text.strip().startswith("{"):
                data = resp.json()
                performances = self._parse_api(data)
                if performances:
                    return performances
        except (requests.RequestException, json.JSONDecodeError):
            pass

        # Also try the production API
        try:
            api_url = "https://www.metopera.org/api/production/v1/productions"
            resp = session.get(api_url, timeout=15,
                               headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                performances = self._parse_api(data)
                if performances:
                    return performances
        except (requests.RequestException, json.JSONDecodeError):
            pass

        # Fallback: scrape HTML
        try:
            resp = session.get(self.calendar_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            performances = self._parse_html(soup)
        except requests.RequestException as e:
            print(f"[MetOpera] Error: {e}")

        return performances

    def _parse_api(self, data: dict) -> list[Performance]:
        """Parse Met Opera API JSON response"""
        performances = []
        productions = data.get("productions", data.get("events", data.get("results", [data])))
        if isinstance(productions, dict):
            productions = [productions]

        for prod in productions:
            title = (prod.get("title") or prod.get("production", {}).get("title", "") or "")
            if not title:
                continue

            # Met Opera data often nested under performances
            perf_list = prod.get("performances", [prod])
            for perf in perf_list:
                if isinstance(perf, str):
                    continue
                date_str = (perf.get("date") or perf.get("startDate") or
                           prod.get("date", ""))
                time_str = (perf.get("time") or perf.get("startTime") or "")

                p = Performance(
                    title=title,
                    composer=prod.get("composer", ""),
                    date=date_str,
                    time=time_str,
                    venue="Metropolitan Opera House",
                    url=prod.get("url", prod.get("link", "")),
                    description=prod.get("description", prod.get("shortDescription", "")),
                )

                # Parse cast/artists
                for role_data in prod.get("roles", prod.get("cast", [])):
                    if isinstance(role_data, dict):
                        artist_name = (role_data.get("artist") or
                                      role_data.get("name") or "")
                        role_name = role_data.get("role", "")
                        if artist_name:
                            # Determine if conductor/director/singer
                            rl = role_data.get("roleType", role_data.get("function", "")).lower()
                            if "conductor" in rl:
                                p.conductors.append(Artist(name=artist_name, role=role_data.get("role", "")))
                            elif "director" in rl or "stage" in rl or "production" in rl:
                                p.directors.append(Artist(name=artist_name, role=role_data.get("role", "")))
                            else:
                                p.cast.append(Artist(name=artist_name, role=role_name))

                performances.append(p)

        return performances

    def _parse_html(self, soup: BeautifulSoup) -> list[Performance]:
        """Fallback HTML parsing"""
        performances = []
        events = soup.select(
            '[class*="event"], .card, article, [class*="production"], '
            '[class*="calendar-item"], [class*="performance"]'
        )
        for event in events:
            title_el = event.select_one("h2, h3, h4, [class*='title'], a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            date_el = event.select_one("time, [class*='date'], [datetime]")
            date_str = date_el.get("datetime", "") if date_el else ""

            link_el = event.select_one("a[href]") if not title_el.name == "a" else title_el
            href = link_el.get("href", "") if link_el else ""
            url = href if href.startswith("http") else f"{self.base_url}{href}"

            p = Performance(title=title, date=date_str, url=url)
            performances.append(p)
        return performances