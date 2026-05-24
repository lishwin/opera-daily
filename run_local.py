#!/usr/bin/env python3
"""
Opera Daily - 主入口脚本（生产/本地两用）
在 GitHub Actions 中调用此脚本
"""
import sys
import os
from pathlib import Path

# 确保项目路径
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

# 设置编码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def main():
    import json
    from datetime import datetime, date, timezone
    from orchestrator import run_all_crawlers
    from report_generator import generate_daily_report

    print("🎭 Opera Daily Report Generator")
    print(f"   Started at: {datetime.now(timezone.utc).isoformat()}")
    print(f"   Project: {PROJECT_DIR}")
    print("=" * 60)

    # Step 1: Run crawlers
    print("\n📡 Step 1: Crawling opera houses...")
    os.makedirs("data/raw", exist_ok=True)
    results = run_all_crawlers()

    # Step 2: Generate report
    print("\n📝 Step 2: Generating daily report...")
    report_path = generate_daily_report(results)

    # Step 3: Summary
    print("\n📊 Summary:")
    success = sum(1 for r in results if r.get("status") == "success")
    total = len(results)
    total_perf = sum(r.get("performances_count", 0) for r in results if r.get("status") == "success")
    errors = [r for r in results if r.get("status") == "error"]
    print(f"   Opera houses: {success}/{total}")
    print(f"   Total performances: {total_perf}")
    if errors:
        print(f"   Errors ({len(errors)}):")
        for e in errors:
            print(f"     ✗ {e.get('name', e['id'])}: {e.get('error', 'unknown')}")
    if report_path:
        print(f"\n   Report: {report_path}")
    print("\n🎉 Done!")

    # Exit with error code if all crawlers failed
    if success == 0 and total > 0:
        print("❌ All crawlers failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()