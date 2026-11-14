#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课题02 · 个人手机多工况发热与掉电实测 —— 分析脚本（纯标准库，内联 SVG，无需联网）

读取 raw_data/phone_power_template.csv（用户填好真实电量%/温度后另存为 phone_power.csv），
自动计算各工况掉电速率、温升，并生成可视化报告 report.html。

用法：
    python3 analyze_phone_power.py            # 默认读 raw_data/phone_power.csv
    python3 analyze_phone_power.py 路径.csv    # 指定数据文件
"""
import os
import csv
import html
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "raw_data")
DEFAULT_CSV = os.path.join(RAW, "phone_power.csv")
TEMPLATE_CSV = os.path.join(RAW, "phone_power_template.csv")
OUT = os.path.join(BASE, "report.html")

# 工况顺序与配色（与大纲一致：待机/短视频/导航拍摄/高帧率游戏）
COND_ORDER = ["standby", "video", "navcam", "game"]
COND_ZH = {"standby": "待机", "video": "短视频", "navcam": "导航/拍摄", "game": "高帧率游戏"}
COLOR = {"standby": "#5cb85c", "video": "#f0ad4e", "navcam": "#5bc0de", "game": "#d9534f"}


def parse_num(s):
    s = (s or "").strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_rows(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def build_series(rows):
    """按工况分组，返回 {cond: [(t, batt, temp), ...]} 已按时间排序。"""
    series = {c: [] for c in COND_ORDER}
    for r in rows:
        c = (r.get("condition_en") or "").strip().lower()
        if c not in series:
            continue
        t = parse_num(r.get("time_min"))
        b = parse_num(r.get("battery_pct"))
        tp = parse_num(r.get("temp_c"))
        if t is None:
            continue
        series[c].append((t, b, tp))
    for c in series:
        series[c].sort(key=lambda x: x[0])
    return series


def drain_rate(points):
    """掉电速率 %/min = (首-末电量)/(末-首时间)。"""
    batt = [(t, b) for t, b, _ in points if b is not None]
    if len(batt) < 2:
        return None
    (t0, b0), (t1, b1) = batt[0], batt[-1]
    if t1 == t0:
        return None
    return (b0 - b1) / (t1 - t0)


def temp_rise(points):
    temps = [(t, tp) for t, _, tp in points if tp is not None]
    if len(temps) < 2:
        return None
    return temps[-1][1] - temps[0][1]


def line_chart(series, title, ylabel, ymin, ymax, w=680, h=340, value_fmt="{:.0f}"):
    padL, padR, padT, padB = 52, 18, 28, 36
    plotW = w - padL - padR
    plotH = h - padT - padB
    # x 轴固定 0..30
    xmin, xmax = 0.0, 30.0

    def sx(x):
        return padL + (x - xmin) / (xmax - xmin) * plotW

    def sy(y):
        if ymax == ymin:
            return padT + plotH / 2
        return padT + (ymax - y) / (ymax - ymin) * plotH

    parts = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<text x="0" y="16" font-size="14" fill="#333">{html.escape(title)}</text>')
    # y 网格
    for i in range(5):
        yy = ymin + (ymax - ymin) * i / 4
        yp = sy(yy)
        parts.append(f'<line x1="{padL}" y1="{yp:.1f}" x2="{w-padR}" y2="{yp:.1f}" stroke="#eee"/>')
        parts.append(f'<text x="{padL-6}" y="{yp+4:.1f}" font-size="11" fill="#888" text-anchor="end">{value_fmt.format(yy)}</text>')
    # x 轴刻度
    for xt in range(0, 31, 5):
        xp = sx(xt)
        parts.append(f'<text x="{xp:.1f}" y="{h-padB+16}" font-size="11" fill="#888" text-anchor="middle">{xt}</text>')
    parts.append(f'<text x="{w-padR}" y="{h-padB+30}" font-size="11" fill="#888" text-anchor="end">{html.escape(ylabel)}</text>')
    # 折线
    for c in COND_ORDER:
        pts = series.get(c, [])
        valid = []
        for (t, b, tp) in pts:
            v = b if ylabel.startswith("电量") else tp
            if v is not None:
                valid.append((t, v))
        if len(valid) < 2:
            continue
        d = " ".join(f"{sx(t):.1f},{sy(v):.1f}" for t, v in valid)
        parts.append(f'<polyline points="{d}" fill="none" stroke="{COLOR[c]}" stroke-width="2.2"/>')
        for t, v in valid:
            parts.append(f'<circle cx="{sx(t):.1f}" cy="{sy(v):.1f}" r="2.6" fill="{COLOR[c]}"/>')
        # 图例
    lx = padL + 4
    ly = padT + 6
    for c in COND_ORDER:
        parts.append(f'<rect x="{lx}" y="{ly}" width="11" height="11" fill="{COLOR[c]}"/>')
        parts.append(f'<text x="{lx+16}" y="{ly+10}" font-size="11" fill="#333">{COND_ZH[c]}</text>')
        lx += 78
    parts.append("</svg>")
    return "".join(parts)


def bar_chart(items, title, ylabel, w=680, h=300, color="#d9534f"):
    """竖向条形图，items=[(label, value), ...]。"""
    if not items:
        return ""
    maxv = max(v for _, v in items) or 1
    padL, padR, padT, padB = 52, 18, 28, 40
    plotW = w - padL - padR
    plotH = h - padT - padB
    n = len(items)
    bw = plotW / n * 0.6
    gap = plotW / n
    parts = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<text x="0" y="16" font-size="14" fill="#333">{html.escape(title)}</text>')
    for i, (lab, val) in enumerate(items):
        x = padL + gap * i + (gap - bw) / 2
        bh = val / maxv * plotH
        y = padT + plotH - bh
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{color}" rx="3"/>')
        parts.append(f'<text x="{x+bw/2:.1f}" y="{y-6:.1f}" font-size="12" fill="#333" text-anchor="middle">{val:.2f}</text>')
        parts.append(f'<text x="{x+bw/2:.1f}" y="{h-padB+18}" font-size="12" fill="#555" text-anchor="middle">{html.escape(lab)}</text>')
    # y 轴基线
    parts.append(f'<line x1="{padL}" y1="{padT+plotH}" x2="{w-padR}" y2="{padT+plotH}" stroke="#ccc"/>')
    parts.append(f'<text x="{padL-6}" y="{padT+plotH+4}" font-size="11" fill="#888" text-anchor="end">0</text>')
    parts.append(f'<text x="{w-padR}" y="{padT-8}" font-size="11" fill="#888" text-anchor="end">{html.escape(ylabel)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def make_table(rows):
    body = ""
    for r in rows:
        b = (r.get("battery_pct") or "").strip()
        tp = (r.get("temp_c") or "").strip()
        body += (f"<tr><td>{html.escape(r.get('condition_zh',''))}</td>"
                 f"<td>{html.escape(str(r.get('time_min','')))}</td>"
                 f"<td>{html.escape(b) if b else '—'}</td>"
                 f"<td>{html.escape(tp) if tp else '—'}</td>"
                 f"<td>{html.escape(r.get('note','') or '')}</td></tr>")
    return f'''<table>
      <tr><th>工况</th><th>时间(分)</th><th>电量%</th><th>温度℃</th><th>备注</th></tr>
      {body}
    </table>'''


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if src and os.path.exists(src):
        path = src
    elif os.path.exists(DEFAULT_CSV):
        path = DEFAULT_CSV
    elif os.path.exists(TEMPLATE_CSV):
        print("⚠️ 未找到 raw_data/phone_power.csv，请用真实数据覆盖模板后另存为 phone_power.csv，")
        print("   或执行：python3 analyze_phone_power.py 你的数据.csv")
        return
    else:
        print("未找到数据文件。")
        return

    rows = load_rows(path)
    series = build_series(rows)

    rates = {c: drain_rate(series[c]) for c in COND_ORDER}
    rises = {c: temp_rise(series[c]) for c in COND_ORDER}

    # 电量图 y 范围
    all_b = [b for c in COND_ORDER for _, b, _ in series[c] if b is not None]
    bmin = min(all_b) - 2 if all_b else 80
    bmax = max(all_b) + 2 if all_b else 100
    batt_svg = line_chart(series, "各工况电量% 随时间变化", "电量%", bmin, bmax, value_fmt="{:.0f}")

    # 温度图
    has_temp = any(rises[c] is not None for c in COND_ORDER)
    if has_temp:
        all_t = [tp for c in COND_ORDER for _, _, tp in series[c] if tp is not None]
        tmin = min(all_t) - 2 if all_t else 25
        tmax = max(all_t) + 2 if all_t else 45
        temp_svg = line_chart(series, "各工况温度℃ 随时间变化", "温度℃", tmin, tmax, value_fmt="{:.0f}")
    else:
        temp_svg = '<p class="note">未填写温度数据，已跳过温度图（可在 CSV 的 temp_c 列补测后重跑）。</p>'

    rate_items = [(COND_ZH[c], rates[c]) for c in COND_ORDER if rates[c] is not None]
    rate_svg = bar_chart(rate_items, "各工况掉电速率（%/分钟，越高越耗电）", "%/min")

    # 关键结论
    valid_rates = [(c, rates[c]) for c in COND_ORDER if rates[c] is not None]
    hottest = max(valid_rates, key=lambda x: x[1])[0] if valid_rates else None
    valid_rises = [(c, rises[c]) for c in COND_ORDER if rises[c] is not None]
    max_rise = max(valid_rises, key=lambda x: x[1])[0] if valid_rises else None

    findings = []
    if hottest:
        findings.append(f"耗电最快的工况是 <b>{COND_ZH[hottest]}</b>，平均掉电 <b>{rates[hottest]:.2f} %/分钟</b>。")
    if max_rise:
        findings.append(f"发热最明显的工况是 <b>{COND_ZH[max_rise]}</b>，30 分钟内温升 <b>{rises[max_rise]:.1f} ℃</b>。")
    if not findings:
        findings.append("数据尚未完整，请补全 CSV 后重跑。")

    findings_html = "".join(f"<li>{f}</li>" for f in findings)

    doc = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>课题02 · 手机多工况发热与掉电实测报告</title>
<style>
  body{{font-family:-apple-system,"Microsoft YaHei",sans-serif;max-width:860px;margin:32px auto;padding:0 20px;color:#222;line-height:1.6}}
  h1{{font-size:22px}} h2{{font-size:17px;border-left:4px solid #d9534f;padding-left:8px;margin-top:28px}}
  .card{{background:#f7f9fa;border:1px solid #e3e8ea;border-radius:8px;padding:14px 16px;margin:12px 0}}
  table{{border-collapse:collapse;width:100%;margin-top:8px;font-size:14px}}
  th,td{{border:1px solid #ddd;padding:6px 10px;text-align:left}}
  th{{background:#f0f3f4}}
  .note{{color:#777;font-size:13px}}
  code{{background:#eef;padding:1px 5px;border-radius:3px}}
  ul{{font-size:14px}}
</style></head><body>
  <h1>课题02 · 个人手机多工况发热与掉电实测</h1>
  <div class="card">
    <b>采样：</b>手机在 待机 / 短视频 / 导航·拍摄 / 高帧率游戏 4 种工况下，各 30 分钟、每 5 分钟记录电量% 与温度℃。<br>
    <b>样本：</b>4 工况 × 6 时间点 = <b>24 组</b>时间序列（对照大纲"提交 24 组时间序列 CSV 表"）。
  </div>

  <h2>1. 电量随时间变化</h2>
  <div class="card">{batt_svg}</div>

  <h2>2. 温度随时间变化</h2>
  <div class="card">{temp_svg}</div>

  <h2>3. 各工况掉电速率对比</h2>
  <div class="card">{rate_svg}</div>

  <h2>4. 关键发现（自动生成，供撰写省电策略报告参考）</h2>
  <div class="card"><ul>{findings_html}</ul>
    <p class="note">把以上结论并入 <code>power_saving_report.md</code> 的"数据概览/高功耗模块分析"段，并据此给出系统省电策略。</p>
  </div>

  <h2>5. 原始数据表（24 组）</h2>
  {make_table(rows)}

  <p class="note">报告由 analyze_phone_power.py 生成 · 纯标准库内联 SVG，可离线打开。数据来源：{html.escape(os.path.basename(path))}（用户真实测量）。</p>
</body></html>'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print("已生成", OUT)
    print("掉电速率 %/min：", {COND_ZH[c]: (round(rates[c], 3) if rates[c] else None) for c in COND_ORDER})
    print("温升 ℃：", {COND_ZH[c]: (round(rises[c], 1) if rises[c] else None) for c in COND_ORDER})


if __name__ == "__main__":
    main()
