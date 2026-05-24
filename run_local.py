#!/usr/bin/env python3
"""
本地运行测试脚本 - 模拟 GitHub Actions 环境执行
"""
import sys
import os
from pathlib import Path

# 确保项目目录在 Python 路径中
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

def main():
    print("🎭 Opera Daily - Local Test Runner")
    print("=" * 50)

    # Step 1: 运行爬虫
    print("\n📡 Step 1: Running crawlers...")
    from orchestrator import run_all_crawlers
    results = run_all_crawlers()

    # Step 2: 生成日报
    print("\n📝 Step 2: Generating daily report...")
    from report_generator import generate_daily_report
    report_path = generate_daily_report(results)

    # Step 3: 验证
    print("\n✅ Step 3: Verification")
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")

    # Check raw data
    raw_files = list(Path("data/raw").glob("*.json"))
    print(f"   Raw data files: {len(raw_files)}")

    # Check report
    report_file = Path(report_path)
    if report_file.exists():
        size = report_file.stat().st_size
        print(f"   Report: {report_path} ({size:,} bytes)")
    else:
        print(f"   ❌ Report not generated!")

    # Summary
    success = sum(1 for r in results if r.get("status") == "success")
    total = len(results)
    total_perf = sum(r.get("performances_count", 0) for r in results if r.get("status") == "success")
    print(f"\n📊 Summary:")
    print(f"   Opera houses: {success}/{total}")
    print(f"   Total performances: {total_perf}")
    print(f"\n   Report: docs/daily/opera-daily-{today}.md")
    print(f"   Latest:  docs/daily/latest.md")
    print("\n🎉 Done!")


if __name__ == "__main__":
    main()