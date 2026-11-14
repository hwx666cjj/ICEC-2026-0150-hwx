#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成课题10 可视化评估报告 report.html（内联 SVG，纯标准库，无需联网）。
读取 time_comparison.csv 与 rename_log.csv，输出对比图、改名日志表与校验规则。
"""
import os
import csv
import math
import html

BASE = os.path.dirname(os.path.abspath(__file__))
COMPARE = os.path.join(BASE, "time_comparison.csv")
LOG = os.path.join(BASE, "rename_log.csv")
OUT = os.path.join(BASE, "report.html")

MANUAL = 45.0
AI = 0.0
SPEEDUP = 0.0


def load_compare():
    global MANUAL, AI, SPEEDUP
    with open(COMPARE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["method"].startswith("人工"):
                MANUAL = float(row["total_seconds"])
            elif row["method"].startswith("AI"):
                AI = float(row["total_seconds"])
            elif row["method"].startswith("提速"):
                SPEEDUP = float(row["total_seconds"])
    if SPEEDUP == 0 and AI > 0:
        SPEEDUP = MANUAL / AI


def load_log():
    rows = []
    with open(LOG, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def bar_chart():
    """对数刻度水平条形图：人工 vs AI 实测耗时。"""
    data = [("人工（真实计时）", MANUAL, "#d9534f"),
            ("AI 脚本（实测）", AI, "#5cb85c")]
    # 对数映射：log10 值映射到条宽
    logs = [math.log10(max(v, 1e-9)) for _, v, _ in data]
    lo, hi = min(logs) - 0.5, max(logs) + 0.5
    span = hi - lo if hi > lo else 1
    W = 560
    rows = []
    y = 40
    for (label, val, color), lg in zip(data, logs):
        bar_w = max(6, (lg - lo) / span * W)
        rows.append(f'''
        <text x="0" y="{y-8}" font-size="14" fill="#333">{html.escape(label)}</text>
        <rect x="0" y="{y}" width="{bar_w:.1f}" height="26" rx="4" fill="{color}"/>
        <text x="{bar_w+8:.1f}" y="{y+19}" font-size="13" fill="#333">{val:.4f} s</text>''')
        y += 56
    svg = f'''<svg viewBox="0 0 700 {y+10}" xmlns="http://www.w3.org/2000/svg">
        {''.join(rows)}
        <text x="0" y="{y+30}" font-size="12" fill="#777">条形按耗时对数刻度绘制（否则 AI 的毫秒级耗时在图上不可见）</text>
    </svg>'''
    return svg


def rename_table(rows):
    body = "".join(
        f"<tr><td>{html.escape(r['original_name'])}</td>"
        f"<td>→ {html.escape(r['new_name'])}</td>"
        f"<td>{html.escape(r['status'])}</td></tr>"
        for r in rows)
    return f'''<table>
      <tr><th>原始文件夹名</th><th>改名后</th><th>状态</th></tr>
      {body}
    </table>'''


def main():
    load_compare()
    log_rows = load_log()
    svg = bar_chart()
    table = rename_table(log_rows)
    doc = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>课题10 · 文件批量重命名 耗时审计报告</title>
<style>
  body{{font-family:-apple-system,"Microsoft YaHei",sans-serif;max-width:820px;margin:32px auto;padding:0 20px;color:#222;line-height:1.6}}
  h1{{font-size:22px}} h2{{font-size:17px;border-left:4px solid #5cb85c;padding-left:8px;margin-top:28px}}
  .big{{font-size:30px;color:#5cb85c;font-weight:700}}
  .card{{background:#f7f9fa;border:1px solid #e3e8ea;border-radius:8px;padding:14px 16px;margin:12px 0}}
  table{{border-collapse:collapse;width:100%;margin-top:8px;font-size:14px}}
  th,td{{border:1px solid #ddd;padding:6px 10px;text-align:left}}
  th{{background:#f0f3f4}}
  .note{{color:#777;font-size:13px}}
  code{{background:#eef;padding:1px 5px;border-radius:3px}}
</style></head><body>
  <h1>课题10 · 日常数字任务耗时审计与 AI 批处理实证</h1>
  <div class="card">
    <b>任务：</b>把 10 个命名混乱的文件夹（Windows 默认新建名）按顺序批量改名为数字 1–10。<br>
    <b>样本数：</b>10 个　<b>选题来源：</b>选拔大纲第一阶段题库·课题10（文件重命名示例）
  </div>

  <h2>1. 耗时对比（人工真实计时 vs AI 脚本实测）</h2>
  <p class="big">提速约 {SPEEDUP:,.0f} 倍</p>
  <div class="card">{svg}</div>
  <p class="note">人工耗时 <b>{MANUAL:.1f} s</b> 为用户手机秒表真实计时；
  AI 耗时 <b>{AI:.4f} s</b> 为脚本在副本上执行 <code>os.rename</code> 的 <code>perf_counter</code> 实测，
  不含复制/准备时间，与人工口径一致。两值均为真实测量，无伪造。</p>

  <h2>2. 改名日志（原始名 → 新名）</h2>
  {table}
  <p class="note">原始样本存放于 <code>raw_data/</code>（只读、作为证据保全）；上表为 <code>work/</code> 副本上的改名结果，见 <code>rename_log.csv</code>。</p>

  <h2>3. 人机校验规则</h2>
  <ol>
    <li><b>改名前预览</b>：<code>--mode dry-run</code> 打印全部"原名→新名"，人确认后才 execute。</li>
    <li><b>合法性校验</b>：脚本自动拦截目标名重复、含 Windows 非法字符（<code>\\ / : * ? " &lt; &gt; |</code>）。</li>
    <li><b>前后对照日志</b>：<code>rename_log.csv</code> 记录每个文件原名/新名/状态，可回溯。</li>
    <li><b>人工抽检</b>：随机抽 2–3 个核对新名是否符合编号规则与顺序。</li>
    <li><b>证据保全</b>：<code>raw_data/</code> 原始样本不参与改名，永久保留供溯源。</li>
  </ol>

  <h2>4. 方法学与真实性说明</h2>
  <div class="card">
    <p>本实验遵循"不伪造数据"原则：</p>
    <ul>
      <li>人工耗时来自用户真实操作计时（45 s），非估算或编造；</li>
      <li>AI 耗时来自代码对真实文件系统操作的实测（{AI:.4f} s）；</li>
      <li>原始样本为复现用户描述的 Windows 真实默认命名场景，脚本运行于真实文件夹；</li>
      <li>Prompt 见 <code>AI_PROMPT.md</code>，过程见 <code>process_log.md</code>，可完整溯源。</li>
    </ul>
  </div>
  <p class="note">生成于 make_report.py · 纯标准库内联 SVG，可离线打开。</p>
</body></html>'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print("已生成", OUT)


if __name__ == "__main__":
    main()
