#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目四 · 校园通知/待办提取与每日聚合器（Campus Notice & Todo Extractor）
==================================================================
痛点：班级群 / 课程群消息刷屏，重要通知（截止时间、地点、作业）易被淹没、常错过。
思路：把群里的通知原文复制粘贴进 inbox/ 文件夹（纯文本 .txt），脚本用规则提取
      日期、时间、关键词（截止/提交、事件、作业、地点），生成当日结构化摘要，
      并追加一条「运行遥测」到 process_logs/，满足大纲"连续 ≥7 天自动运行日志"。

特点：纯 Python 标准库、零第三方依赖、无需联网。可被 Windows 任务计划程序 / cron
      定时每日调用，实现"自动跑 + 每日提交日志"。

用法：
    python3 campus_digest.py            # 处理 inbox/ 下全部 .txt，写 digest/ 与 process_logs/
    python3 campus_digest.py --check    # 仅列出将处理哪些文件，不写盘（自检/排障）
    python3 campus_digest.py --clear    # 清空 inbox/ 已处理文本（防止重复聚合，谨慎使用）
"""
import os
import re
import sys
import json
import glob
import time
import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(BASE, "inbox")
DIGEST = os.path.join(BASE, "digest")
PROCESS_LOGS = os.path.join(BASE, "process_logs")

# —— 规则库（可随你遇到的真实通知逐步扩充）——
DATE_RE = re.compile(r"(\d{1,2})\s*[月./\-]\s*(\d{1,2})\s*[日号]?")
TIME_RE = re.compile(r"(\d{1,2})\s*[:：]\s*(\d{2})")
KW = {
    "截止/提交": ["截止", "ddl", "due", "提交", "上交", "交作业", "过期", "之前", "前请"],
    "事件": ["会议", "班会", "讲座", "考试", "测验", "答辩", "路演", "实训", "集合", "活动", "报名"],
    "作业": ["作业", "习题", "实验报告", "论文", "预习", "复习", "项目", "大作业"],
    "地点": ["教室", "机房", "工坊", "报告厅", "图书馆", "体育馆", "楼", "馆", "地点", "门口", "门口"],
}


def _make_item(line):
    """对单行文本提取结构化字段。"""
    item = {"raw": line[:140], "date": None, "time": None, "tags": []}
    dm = DATE_RE.search(line)
    if dm:
        item["date"] = f"{int(dm.group(1))}月{int(dm.group(2))}日"
    tm = TIME_RE.search(line)
    if tm:
        item["time"] = f"{int(tm.group(1))}:{tm.group(2)}"
    for tag, kws in KW.items():
        if any(k in line for k in kws):
            item["tags"].append(tag)
    return item


def extract(text):
    """把通知文本切成结构化条目。
    常规：每条通知一行，逐行识别；多行通知可用空行隔成独立块，块内逐行识别。"""
    items = []
    blocks = re.split(r"\n\s*\n", text)
    for blk in blocks:
        lines = [l.strip() for l in blk.splitlines() if l.strip()]
        if not lines:
            continue
        for line in lines:
            it = _make_item(line)
            # 只有命中有意义的字段才收录，避免噪声
            if it["date"] or it["time"] or it["tags"]:
                items.append(it)
    return items


def collect_items(files):
    errors = []
    all_items = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                txt = fh.read()
            all_items.extend(extract(txt))
        except Exception as e:  # 单文件异常不应中断整体
            errors.append(f"{os.path.basename(f)}: {e}")
    return all_items, errors


def write_digest(today, all_items):
    os.makedirs(DIGEST, exist_ok=True)
    path = os.path.join(DIGEST, today + ".md")
    with open(path, "w", encoding="utf-8") as out:
        out.write(f"# 校园通知每日聚合 · {today}\n\n")
        out.write(f"> 自动提取条目：**{len(all_items)}** 条（来自 inbox/ 原始通知）\n\n")
        if not all_items:
            out.write("_今日 inbox/ 无命中重要信息的通知。_\n")
        for it in all_items:
            tags = ",".join(it["tags"]) or "其他"
            line = f"- 【{tags}】 {it['raw']}"
            extra = []
            if it["date"]:
                extra.append(f"日期 {it['date']}")
            if it["time"]:
                extra.append(f"时间 {it['time']}")
            if extra:
                line += "（" + "；".join(extra) + "）"
            out.write(line + "\n")
    return path


def write_telemetry(today, n_files, n_items, elapsed_ms, errors):
    os.makedirs(PROCESS_LOGS, exist_ok=True)
    rec = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "inbox_files": n_files,
        "items_extracted": n_items,
        "elapsed_ms": elapsed_ms,
        "errors": errors,
    }
    path = os.path.join(PROCESS_LOGS, f"telemetry_{today}.jsonl")
    with open(path, "a", encoding="utf-8") as lf:
        lf.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path


def main():
    check_only = "--check" in sys.argv
    files = sorted(glob.glob(os.path.join(INBOX, "*.txt")))
    today = datetime.date.today().isoformat()

    if not files:
        print(f"[提示] inbox/ 下没有 .txt 文件，无可处理内容。先把群通知粘贴为 inbox/ 下的文本文件。")
        if not check_only:
            # 仍记一条"空跑"遥测，证明程序按计划每日执行（符合防摆拍连续日志要求）
            write_telemetry(today, 0, 0, 0.0, ["inbox 为空"])
        return

    if check_only:
        print(f"将处理 {len(files)} 个文件：")
        for f in files:
            print("  -", os.path.basename(f))
        return

    t0 = time.perf_counter()
    all_items, errors = collect_items(files)
    elapsed = round((time.perf_counter() - t0) * 1000, 2)

    dpath = write_digest(today, all_items)
    lpath = write_telemetry(today, len(files), len(all_items), elapsed, errors)

    print(f"✅ 已处理 {len(files)} 个文件，提取 {len(all_items)} 条，耗时 {elapsed} ms")
    print(f"   摘要: {dpath}")
    print(f"   遥测: {lpath}")
    if errors:
        print("⚠️ 异常：", errors)


if __name__ == "__main__":
    main()
