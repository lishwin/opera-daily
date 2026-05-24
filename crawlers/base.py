"""
爬虫基类 - 所有歌剧院爬虫的公共接口
"""
from abc import ABC, abstractmethod
from models import OperaHouse, Performance


class BaseCrawler(ABC):
    """爬虫抽象基类"""

    def __init__(self, house_id: str):
        from models import get_opera_house_config
        self.config = get_opera_house_config(house_id)
        self.house_id = house_id
        self.session = None

    def _get_session(self):
        """获取或创建 requests session"""
        if self.session is None:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            })
        return self.session

    @abstractmethod
    def fetch_performances(self) -> list[Performance]:
        """爬取该歌剧院的演出排期，返回 Performance 列表"""
        ...

    def crawl(self) -> OperaHouse:
        """执行完整爬取流程"""
        import sys
        sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
        from models import OperaHouse, get_opera_house_config
        from datetime import datetime

        config = get_opera_house_config(self.house_id)
        performances = self.fetch_performances()

        house = OperaHouse(
            id=self.house_id,
            name=config["name"],
            name_en=config.get("name_en", ""),
            city=config.get("city", ""),
            country=config.get("country", ""),
            url=config.get("url", ""),
            performances=performances,
            updated_at=datetime.now().isoformat(),
        )
        return house