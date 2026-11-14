# -*- coding: utf-8 -*-
"""
课题10 · AI 批处理实证脚本（extract.py）
========================================
把 10 份杂乱的实验/会议记录文本，自动提取【日期、地点、参与人、关键结论】
四个字段，汇总成结构化 summary.csv，并对比"人工"与"AI 脚本"的耗时。

本脚本即为课题要求的"AI 脚本"交付物；其由大模型（提示词见 AI_PROMPT.md）
辅助生成，此处真实运行并计时，产出可核验的耗时对比数据。

运行：python3 extract.py
输出：summary.csv / time_comparison.csv / report.html
"""
import csv
import glob
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw_data")
OUT = HERE

CJK = r"一-鿿"  # 基本汉字范围

# 非人名特征字符：出现即判定该 token 不是姓名（覆盖引导词/连词/动词）
NOTNAME = set("有包括人参会到场和与他与或等了的地在将于及并的")


def extract_date(text):
    # 2026-10-12 / 2026/10/12 / 2026.10.17 / 2026年10月15号 / 10月13日
    m = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", text)
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    m = re.search(r"(\d{1,2})月(\d{1,2})[日号]?", text)
    if m:
        return f"2026-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return ""


def extract_location(text):
    # 允许数字/汉字/空格，匹配含地点关键词的片段（如 "431 实训室"）
    m = re.search(r"([%s0-9 ]{1,12}?(?:实训室|机房|图书馆|报告厅|工坊|会议室|走廊|三楼|门口))" % CJK, text)
    if m:
        loc = m.group(1).strip()
        # 去掉引导词前缀（地点在/于/在/会议室在/地点 等）
        loc = re.sub(r"^(地点在|地点：|地点|于|在|会议室在|会议室)\s*", "", loc)
        return loc
    return ""


def extract_participants(text):
    # 找含"参与人/参会/到场/人员/包括"的那一行，仅取关键词【之后】的 2–3 字中文 token，
    # 且 token 不得含有引导词/连词/动词字符（排除"人员有""机房开会""也来了"等误提）
    for line in text.splitlines():
        m = re.search(r"(参与人|参会|到场|人员|包括)", line)
        if m:
            after = line[m.end():]
            toks = re.split(r"[、，,；;。：:\s和与他与或等]+", after)
            names = [t.strip() for t in toks
                     if re.fullmatch(r"[%s]{2,3}" % CJK, t.strip())
                     and not any(ch in NOTNAME for ch in t.strip())]
            if names:
                return "、".join(names)
    return ""


def extract_conclusion(text):
    # 关键结论 / 结论 / 小结 之后，取到第一个句号或行尾；去掉前导冒号
    m = re.search(r"(?:关键结论|结论|小结)\s*:?=?>?\s*([^。\n]+)", text)
    if m:
        return m.group(1).strip().lstrip("：:：").rstrip("。 ")
    return ""


def main():
    files = sorted(glob.glob(os.path.join(RAW, "*.txt")))
    rows = []
    t0 = time.perf_counter()
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            text = f.read()
        rows.append({
            "file": os.path.basename(fp),
            "chars": len(text),
            "date": extract_date(text),
            "location": extract_location(text),
            "participants": extract_participants(text),
            "conclusion": extract_conclusion(text),
        })
    elapsed = time.perf_counter() - t0  # 真实 AI 脚本耗时（秒）

    # 人工基线模型：开文件+阅读+定位+手敲 4 字段，约 25s 起步 + 每字 1/15 秒
    for r in rows:
        r["manual_s"] = round(25 + r["chars"] / 15, 1)
        r["ai_s"] = round(elapsed / len(rows), 4)

    # 写出结构化汇总
    with open(os.path.join(OUT, "summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "date", "location", "participants", "conclusion"])
        for r in rows:
            w.writerow([r["file"], r["date"], r["location"], r["participants"], r["conclusion"]])

    # 写出耗时对比
    total_manual = sum(r["manual_s"] for r in rows)
    with open(os.path.join(OUT, "time_comparison.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "chars", "manual_s", "ai_s", "speedup_x"])
        for r in rows:
            sp = r["manual_s"] / r["ai_s"] if r["ai_s"] > 0 else 0
            w.writerow([r["file"], r["chars"], r["manual_s"], r["ai_s"], f"{sp:.0f}"])
        w.writerow(["TOTAL", sum(r["chars"] for r in rows), round(total_manual, 1),
                    round(elapsed, 4), f"{total_manual / elapsed:.0f}"])

    build_report(rows, elapsed, total_manual)
    print(f"✅ 处理 {len(rows)} 个文件，AI 脚本总耗时 {elapsed:.4f}s")
    print(f"   人工基线估算 {total_manual:.0f}s（{total_manual/60:.1f} 分钟）")
    print(f"   提速约 {total_manual/elapsed:.0f} 倍")


def build_report(rows, elapsed, total_manual):
    total_chars = sum(r["chars"] for r in rows)
    speedup = total_manual / elapsed if elapsed > 0 else 0
    # 条形图：人工 vs AI 总耗时
    def bar(val, maxv, color, label, unit=""):
        w = 320
        bw = (val / maxv) * (w - 80) if maxv else 0
        return (f'<div style="margin:6px 0"><span style="display:inline-block;width:90px">{label}</span>'
                f'<span style="display:inline-block;height:18px;width:{bw:.0f}px;background:{color};'
                f'vertical-align:middle"></span> {val:.1f}{unit}</div>')

    maxv = max(total_manual, elapsed)
    bars = bar(total_manual, maxv, "#d95f0e", "人工基线", " s") + bar(elapsed, maxv, "#2c7fb8", "AI 脚本", " s")

    summary_tbl = "".join(
        f"<tr><td>{r['file']}</td><td>{r['date']}</td><td>{r['location']}</td>"
        f"<td>{r['participants']}</td><td>{r['conclusion']}</td></tr>" for r in rows)

    cmp_tbl = "".join(
        f"<tr><td>{r['file']}</td><td>{r['chars']}</td><td>{r['manual_s']}</td>"
        f"<td>{r['ai_s']}</td><td>{r['manual_s']/r['ai_s']:.0f}×</td></tr>" for r in rows)

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>课题10 · 数字任务耗时审计与 AI 批处理实证</title>
<style>
 body{{font-family:-apple-system,'Segoe UI','Microsoft YaHei',sans-serif;max-width:960px;margin:0 auto;padding:24px;color:#222}}
 h1{{border-bottom:3px solid #2c7fb8;padding-bottom:8px}}
 h2{{color:#2c7fb8;margin-top:26px}}
 .card{{background:#fafafa;border:1px solid #eee;border-radius:8px;padding:16px;margin:12px 0}}
 table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{border:1px solid #ddd;padding:6px 8px}}
 .kpi{{display:inline-block;background:#eef6fb;border:1px solid #cfe3f2;border-radius:8px;padding:12px 18px;margin:6px}}
 .kpi b{{display:block;font-size:22px;color:#2c7fb8}}
 code{{background:#f0f0f0;padding:2px 4px;border-radius:4px}}
</style></head><body>
<h1>课题10 · 日常数字任务耗时审计与 AI 批处理实证</h1>
<p>第一阶段·基础素养实地测评（10选2）｜ 零编程门槛 ｜ 可复现交付</p>

<h2>1. 任务定义</h2>
<div class="card">选定高频重复数字任务：<b>从 10 份格式不一的实验/会议记录文本中，提取「日期、地点、参与人、关键结论」
四个字段并汇总为一张结构化表格</b>。分别用「纯人工」与「AI 辅助脚本」两种方法完成，审计耗时并制定人机校验规则。</div>

<h2>2. 关键指标</h2>
<div class="card">
 <div class="kpi"><b>{len(rows)}</b>样本文件</div>
 <div class="kpi"><b>{total_chars}</b>总字符</div>
 <div class="kpi"><b>{total_manual:.0f}s</b>人工基线</div>
 <div class="kpi"><b>{elapsed:.3f}s</b>AI 脚本</div>
 <div class="kpi"><b>{speedup:.0f}×</b>提速倍数</div>
</div>

<h2>3. 耗时对比</h2>
<div class="card">{bars}
<p style="color:#666;font-size:12px">注：人工基线按「开文件+阅读+定位+手敲 4 字段」建模为 25s 起步 + 每字符 1/15 秒；
AI 脚本耗时为脚本真实运行 wall-clock 时间（含读取与正则提取）。</p>
</div>

<h2>4. 逐文件耗时明细</h2>
<div class="card"><table>
<tr><th>文件</th><th>字符数</th><th>人工(s)</th><th>AI(s)</th><th>提速</th></tr>
{cmp_tbl}
<tr><td><b>合计</b></td><td><b>{total_chars}</b></td><td><b>{total_manual:.0f}</b></td><td><b>{elapsed:.3f}</b></td><td><b>{speedup:.0f}×</b></td></tr>
</table></div>

<h2>5. AI 自动提取结果（summary.csv）</h2>
<div class="card"><table>
<tr><th>文件</th><th>日期</th><th>地点</th><th>参与人</th><th>关键结论</th></tr>
{summary_tbl}
</table></div>

<h2>6. 人机校验规则（Human-in-the-loop）</h2>
<div class="card"><ol>
<li><b>字段完整性校验</b>：脚本提取后逐行检查 4 字段非空；空值标红交人工补录。</li>
<li><b>日期归一化校验</b>：统一为 YYYY-MM-DD；未识别到年份的「X月X日」默认补 2026，需人工确认年份。</li>
<li><b>人名白名单</b>：参与人 token 仅接受 2–4 个汉字；疑似误提（如结论里的名字）由人工剔除。</li>
<li><b>抽样复核</b>：10 份中至少抽 2 份人工对照原文核对，一致率须 100% 才采信整批。</li>
<li><b>结论截断检查</b>：结论字段不应包含换行/后续段落，超长即判定正则越界，人工修整。</li>
</ol></div>

<h2>7. 交付物（证据链）</h2>
<div class="card"><ul>
<li><code>raw_data/note_01..10.txt</code> — 10 份原始样本（任务样本）</li>
<li><code>extract.py</code> — AI 辅助生成的批处理脚本（AI 脚本）</li>
<li><code>AI_PROMPT.md</code> — 生成该脚本所用的提示词（Prompt）</li>
<li><code>summary.csv</code> — 自动提取的结构化汇总</li>
<li><code>time_comparison.csv</code> — 人工 vs AI 耗时对比表</li>
<li><code>report.html</code> — 本可视化审计报告</li>
<li><code>process_log.md</code> — 过程记录（迭代与排障）</li>
</ul></div>
</body></html>"""

    with open(os.path.join(OUT, "report.html"), "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    main()
