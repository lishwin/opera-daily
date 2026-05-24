"""
维也纳国家歌剧院 (Wiener Staatsoper) 爬虫
Source: https://www.wiener-staatsoper.at/en/performances/calendar/
API: https://www.wiener-staatsoper.at/api/spielplan/v1/calendar
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta

from models import Performance, Artist
from crawlers.base import BaseCrawler


class WienerStaatsoperCrawler(BaseCrawler):
    """维也纳国家歌剧院爬虫"""

    def __init__(self):
        super().__init__("wiener_staatsoper")
        self.api_base = "https://www.wiener-staatsoper.at/api/spielplan/v1"

    def fetch_performances(self) -> list[Performance]:
        performances = []
        session = self._get_session()

        # Try API first
        today = date.today()
        for days_offset in range(0, 90):
            d = today + timedelta(days=days_offset)
            date_str = d.strftime("%Y-%m-%d")
            try:
                api_url = f"{self.api_base}/calendar?date={date_str}"
                resp = session.get(api_url, timeout=15,
                                   headers={"Accept": "application/json"})
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        perfs = self._parse_api_response(data, date_str)
                        performances.extend(perfs)
                    except (ValueError, KeyError):
                        pass
            except requests.RequestException:
                continue

        if performances:
            return performances

        # Fallback: scrape HTML calendar
        try:
            resp = session.get(
                "https://www.wiener-staatsoper.at/en/performances/calendar/",
                timeout=30,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            performances = self._parse_html(soup)
        except requests.RequestException as e:
            print(f"[WienerStaatsoper] Error: {e}")

        return performances

    def _parse_api_response(self, data: dict, date_str: str) -> list[Performance]:
        """Parse the API JSON response"""
        performances = []
        events = data.get("events", data.get("performances", data.get("results", [data])))
        if isinstance(events, dict):
            events = [events]

        for event in events:
            if isinstance(event, str):
                continue
            title = (event.get("title") or event.get("name") or
                     event.get("production", {}).get("title", ""))
            if not title:
                continue

            p = Performance(
                title=title,
                composer=event.get("composer", {}).get("name", "") if isinstance(event.get("composer"), dict) else "",
                date=date_str,
                time=event.get("time", event.get("begin", "")),
                venue=event.get("venue", event.get("location", "")),
                url=event.get("url", event.get("link", "")),
                description=event.get("description", event.get("shorttext", "")),
            )
            # Parse artists
            for artist_data in event.get("artists", event.get("cast", [])):
                if isinstance(artist_data, dict):
                    name = artist_data.get("name", "")
                    role = artist_data.get("role", artist_data.get("function", ""))
                    if name:
                        if "conductor" in role.lower() or "dirigent" in role.lower():
                            p.conductors.append(Artist(name=name, role=role))
                        elif "director" in role.lower() or "regie" in role.lower() or "inszenierung" in role.lower():
                            p.directors.append(Artist(name=name, role=role))
                        else:
                            p.cast.append(Artist(name=name, role=role))
            performances.append(p)
        return performances

    def _parse_html(self, soup: BeautifulSoup) -> list[Performance]:
        """Fallback HTML parsing"""
        performances = []
        events = soup.select('[class*="event"], [class*="performance"], .card, article')
        for event in events:
            title_el = event.select_one("h2, h3, [class*='title']")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue

            date_el = event.select_one("time, [class*='date'], [datetime]")
            date_str = date_el.get("datetime", "") if date_el else ""

            link_el = event.select_one("a[href]")
            url = ""
            if link_el:
                href = link_el.get("href", "")
                url = href if href.startswith("http") else f"https://www.wiener-staatsoper.at{href}"

            p = Performance(title=title, date=date_str, url=url)
            performances.append(p)
        return performances