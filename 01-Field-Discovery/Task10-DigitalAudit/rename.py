#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课题10：日常数字任务耗时审计与 AI 批处理实证 —— 文件批量重命名脚本
===================================================================
任务：把一批命名混乱的文件夹，按"顺序编号 1..N"的规则批量改名。
对比：人工逐个改名（用户真实计时） vs 本脚本批量改名（代码实测耗时）。

设计要点（对应选拔"人机校验规则"与"真实性"要求）：
1. 只读 raw_data/ 作为原始样本证据，绝不改动它；实际改名在 work/ 副本上进行。
2. 改名前先 dry-run 打印"原名 -> 新名"对照表，确认无误再 execute。
3. 改名前做合法性校验：目标名不能重复、不能含 Windows 非法字符。
4. 仅对"重命名操作本身"计实测耗时（perf_counter），不含准备/复制时间，保证对比公平。
5. 写出 rename_log.csv（原名/新名/状态）与 time_comparison.csv（人工 vs AI 耗时）。

用法：
    python3 rename.py --mode dry-run     # 仅预览方案，不改任何文件
    python3 rename.py --mode execute     # 真正执行改名并实测耗时
"""
import os
import sys
import re
import time
import csv
import shutil
import argparse


def natural_key(s):
    """自然排序键：把字符串里的数字按数值比较，使 ' (2)' 排在 ' (10)' 前。"""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "raw_data")        # 原始样本（只读、作为证据保留）
WORK = os.path.join(BASE, "work")           # 改名操作实际发生的副本目录
LOG = os.path.join(BASE, "rename_log.csv")
COMPARE = os.path.join(BASE, "time_comparison.csv")

# 用户真实人工耗时（手机计时所得，单位：秒）——这是课题要求的"人工耗时"真值
MANUAL_TOTAL_SECONDS = 45.0

ILLEGAL = set('\\/:*?"<>|')  # Windows 文件夹名非法字符


def plan_renames(raw_dir):
    """读取原始文件夹，生成 原名 -> 顺序编号 的改名方案。
    排序采用稳定的字典序，确保每次运行结果一致、可追溯。"""
    items = [n for n in os.listdir(raw_dir)
             if os.path.isdir(os.path.join(raw_dir, n))]
    items.sort(key=natural_key)  # 自然顺序：(2) 在 (10) 前，符合人类编号直觉
    mapping = {name: str(i) for i, name in enumerate(items, start=1)}
    return items, mapping


def validate(mapping):
    """人机校验规则（脚本侧自动检查）：冲突与非法字符。"""
    issues = []
    targets = list(mapping.values())
    if len(targets) != len(set(targets)):
        issues.append("目标名存在重复（会相互覆盖）")
    for t in targets:
        bad = [c for c in t if c in ILLEGAL]
        if bad:
            issues.append(f"目标名含 Windows 非法字符 {bad} -> {t!r}")
    return issues


def main():
    ap = argparse.ArgumentParser(description="课题10 批量重命名（人工 vs AI 实测）")
    ap.add_argument("--mode", choices=["dry-run", "execute"], default="dry-run")
    args = ap.parse_args()

    items, mapping = plan_renames(RAW)
    issues = validate(mapping)

    print("=" * 60)
    print(f"原始样本目录：{RAW}")
    print(f"待处理样本数：{len(items)}")
    print("重命名方案（预览）：")
    for old, new in mapping.items():
        print(f"    {old!r}  ->  {new!r}")
    print("=" * 60)

    if issues:
        print("❌ 校验未通过：", issues)
        sys.exit(1)
    print("✅ 校验通过：无重名、无非法字符")

    if args.mode == "dry-run":
        print("\n[dry-run] 未执行任何改动。确认方案无误后，运行：")
        print("    python3 rename.py --mode execute")
        return

    # ---- execute：在 work/ 副本上真正改名，并仅对改名操作实测耗时 ----
    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    shutil.copytree(RAW, WORK)  # 复制原始样本到副本，保护 raw_data 证据

    start = time.perf_counter()
    rows = []
    for old, new in mapping.items():
        src = os.path.join(WORK, old)
        dst = os.path.join(WORK, new)
        os.rename(src, dst)
        rows.append((old, new, "renamed"))
    elapsed = time.perf_counter() - start

    with open(LOG, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["original_name", "new_name", "status"])
        for r in rows:
            w.writerow(r)

    with open(COMPARE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["method", "total_seconds", "per_sample_seconds", "note"])
        w.writerow(["人工(真实计时)", MANUAL_TOTAL_SECONDS,
                    round(MANUAL_TOTAL_SECONDS / len(items), 3),
                    "用户实际操作10个文件夹改名，手机秒表计时"])
        w.writerow(["AI脚本(实测)", round(elapsed, 6),
                    round(elapsed / len(items), 6),
                    "脚本在 work/ 副本上对 rename 操作的 perf_counter 实测"])
        speedup = MANUAL_TOTAL_SECONDS / elapsed if elapsed > 0 else float('inf')
        w.writerow(["提速倍数", round(speedup, 1), "", f"人工/AI ≈ {speedup:.0f}x"])

    print(f"\n[execute] 已重命名 {len(rows)} 个文件夹")
    print(f"[execute] 实测改名耗时：{elapsed*1000:.3f} ms （{elapsed:.6f} s）")
    print(f"[execute] 人工真实耗时：{MANUAL_TOTAL_SECONDS:.1f} s ｜ 提速约 {speedup:.0f} 倍")
    print(f"[execute] 日志已写出：{os.path.basename(LOG)}、{os.path.basename(COMPARE)}")


if __name__ == "__main__":
    main()
