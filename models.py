"""
全球歌剧院演出排期日报工具 - 核心数据模型

定义歌剧院、演出、艺术家等数据结构。
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, date
import json
import hashlib


@dataclass
class Artist:
    """艺术家信息"""
    name: str
    role: str = ""          # 角色（指挥、导演、歌手等）
    nationality: str = ""    # 国籍

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Artist":
        return cls(**d)


@dataclass
class Performance:
    """单场演出信息"""
    title: str               # 剧目名称（如《茶花女》）
    composer: str = ""       # 作曲家
    date: str = ""           # 演出日期 (YYYY-MM-DD)
    time: str = ""           # 演出时间 (HH:MM)
    venue: str = ""          # 演出厅
    conductors: list[Artist] = field(default_factory=list)
    directors: list[Artist] = field(default_factory=list)
    cast: list[Artist] = field(default_factory=list)
    description: str = ""    # 简介
    url: str = ""            # 购票链接
    language: str = ""       # 演出语言
    duration: str = ""       # 时长

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "composer": self.composer,
            "date": self.date,
            "time": self.time,
            "venue": self.venue,
            "conductors": [a.to_dict() for a in self.conductors],
            "directors": [a.to_dict() for a in self.directors],
            "cast": [a.to_dict() for a in self.cast],
            "description": self.description,
            "url": self.url,
            "language": self.language,
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Performance":
        d = dict(d)
        d["conductors"] = [Artist.from_dict(a) for a in d.get("conductors", [])]
        d["directors"] = [Artist.from_dict(a) for a in d.get("directors", [])]
        d["cast"] = [Artist.from_dict(a) for a in d.get("cast", [])]
        return cls(**d)


@dataclass
class OperaHouse:
    """歌剧院信息"""
    id: str                  # 唯一标识符（用于文件名）
    name: str                # 名称（中文）
    name_en: str = ""        # 英文名
    city: str = ""           # 城市
    country: str = ""        # 国家
    url: str = ""            # 官网
    performances: list[Performance] = field(default_factory=list)
    updated_at: str = ""     # 更新时间

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "name_en": self.name_en,
            "city": self.city,
            "country": self.country,
            "url": self.url,
            "performances": [p.to_dict() for p in self.performances],
            "updated_at": self.updated_at or datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OperaHouse":
        d = dict(d)
        d["performances"] = [Performance.from_dict(p) for p in d.get("performances", [])]
        return cls(**d)

    def save_json(self, path: str):
        """保存到 JSON 文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_json(cls, path: str) -> "OperaHouse":
        """从 JSON 文件加载"""
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


# 全球歌剧院默认配置
OPERA_HOUSES_CONFIG = [
    {
        "id": "metropolitan_opera",
        "name": "纽约大都会歌剧院",
        "name_en": "Metropolitan Opera",
        "city": "纽约",
        "country": "美国",
        "url": "https://www.metopera.org",
    },
    {
        "id": "la_scala",
        "name": "米兰斯卡拉歌剧院",
        "name_en": "Teatro alla Scala",
        "city": "米兰",
        "country": "意大利",
        "url": "https://www.teatroallascala.org",
    },
    {
        "id": "wiener_staatsoper",
        "name": "维也纳国家歌剧院",
        "name_en": "Vienna State Opera",
        "city": "维也纳",
        "country": "奥地利",
        "url": "https://www.wiener-staatsoper.at",
    },
    {
        "id": "opera_national_de_paris",
        "name": "巴黎歌剧院",
        "name_en": "Opéra national de Paris",
        "city": "巴黎",
        "country": "法国",
        "url": "https://www.operadeparis.fr",
    },
    {
        "id": "royal_opera_house",
        "name": "英国皇家歌剧院",
        "name_en": "Royal Opera House",
        "city": "伦敦",
        "country": "英国",
        "url": "https://www.roh.org.uk",
    },
    {
        "id": "bayreuth_festspielhaus",
        "name": "拜罗伊特节日剧院",
        "name_en": "Bayreuth Festspielhaus",
        "city": "拜罗伊特",
        "country": "德国",
        "url": "https://www.bayreuther-festspiele.de",
    },
    {
        "id": "sydney_opera_house",
        "name": "悉尼歌剧院",
        "name_en": "Sydney Opera House",
        "city": "悉尼",
        "country": "澳大利亚",
        "url": "https://www.sydneyoperahouse.com",
    },
    {
        "id": "national_centre_for_the_performing_arts",
        "name": "中国国家大剧院",
        "name_en": "National Centre for the Performing Arts",
        "city": "北京",
        "country": "中国",
        "url": "https://www.chncpa.org",
    },
    {
        "id": "salzburg_festival",
        "name": "萨尔茨堡音乐节",
        "name_en": "Salzburg Festival",
        "city": "萨尔茨堡",
        "country": "奥地利",
        "url": "https://www.salzburgerfestspiele.at",
    },
    {
        "id": "teatro_real",
        "name": "马德里皇家剧院",
        "name_en": "Teatro Real",
        "city": "马德里",
        "country": "西班牙",
        "url": "https://www.teatroreal.es",
    },
]


def get_opera_house_config(house_id: str) -> dict:
    """根据ID获取歌剧院配置"""
    for h in OPERA_HOUSES_CONFIG:
        if h["id"] == house_id:
            return h
    raise ValueError(f"Unknown opera house: {house_id}")


def performance_date_key(p: Performance) -> str:
    """用于去重的日期键"""
    return f"{p.date}|{p.title}|{p.venue}"