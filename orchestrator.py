"""
协调器 - Orchestrator
负责依次运行所有爬虫、保存数据、生成日报
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
import time
from datetime import datetime

from models import OperaHouse, OPERA_HOUSES_CONFIG


CRAWLER_MAP = {
    "metropolitan_opera": "metopera.MetOperaCrawler",
    "la_scala": "lascala.LaScalaCrawler",
    "wiener_staatsoper": "wienerstaatsoper.WienerStaatsoperCrawler",
    "opera_national_de_paris": "operadeparis.OperaDeParisCrawler",
    "royal_opera_house": "royaloperahouse.RoyalOperaHouseCrawler",
    "bayreuth_festspielhaus": "bayreuth.BayreuthCrawler",
    "sydney_opera_house": "sydneyoperahouse.SydneyOperaHouseCrawler",
    "national_centre_for_the_performing_arts": "nationalgrandtheater.NationalGrandTheaterCrawler",
    "salzburg_festival": "salzburg.SalzburgFestivalCrawler",
    "teatro_real": "teatroreal.TeatroRealCrawler",
}


def run_all_crawlers(output_dir: str = "data/raw") -> list[dict]:
    """运行所有爬虫并保存原始数据"""
    results = []
    os.makedirs(output_dir, exist_ok=True)

    for house_config in OPERA_HOUSES_CONFIG:
        house_id = house_config["id"]
        crawler_path = CRAWLER_MAP.get(house_id)
        if not crawler_path:
            print(f"[Orchestrator] No crawler for {house_id}, skipping")
            continue

        module_name, class_name = crawler_path.split(".")
        print(f"\n{'='*60}")
        print(f"[Orchestrator] Crawling: {house_config['name']} ({house_id})")
        print(f"{'='*60}")

        try:
            # Dynamic import
            import importlib
            module = importlib.import_module(f"crawlers.{module_name}")
            crawler_class = getattr(module, class_name)
            crawler = crawler_class()

            start = time.time()
            house = crawler.crawl()
            elapsed = time.time() - start

            # Save to JSON
            output_path = os.path.join(output_dir, f"{house_id}.json")
            house.save_json(output_path)

            result = {
                "id": house_id,
                "name": house.name,
                "name_en": house.name_en,
                "city": house.city,
                "country": house.country,
                "performances_count": len(house.performances),
                "updated_at": house.updated_at,
                "elapsed_seconds": round(elapsed, 2),
                "status": "success",
            }
            print(f"  ✓ {len(house.performances)} performances found ({elapsed:.1f}s)")
            results.append(result)

        except Exception as e:
            import traceback
            print(f"  ✗ Error: {e}")
            traceback.print_exc()
            results.append({
                "id": house_id,
                "name": house_config["name"],
                "status": "error",
                "error": str(e),
            })

    # Save summary
    summary_path = os.path.join(output_dir, "_summary.json")
    # Count total performances
    total = sum(r.get("performances_count", 0) for r in results if r.get("status") == "success")
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.now().isoformat(),
        "total_houses": len(OPERA_HOUSES_CONFIG),
        "success_count": sum(1 for r in results if r.get("status") == "success"),
        "error_count": sum(1 for r in results if r.get("status") == "error"),
        "total_performances": total,
        "houses": results,
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n[Orchestrator] Summary: {summary['success_count']}/{summary['total_houses']} houses, "
          f"{total} performances total")

    return results


if __name__ == "__main__":
    results = run_all_crawlers()
    # Generate report after crawling
    from report_generator import generate_daily_report
    generate_daily_report(results)