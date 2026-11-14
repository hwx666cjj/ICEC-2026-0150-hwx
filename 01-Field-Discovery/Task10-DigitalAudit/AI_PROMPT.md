# AI 提示词（Prompt）记录 —— 课题10 交付要求之一

> 课题10 验收要求：「提交任务样本、AI 脚本/Prompt 与耗时对比表」。
> 以下为本人借助大模型（类 DeepSeek / Qwen）辅助生成 `extract.py` 时使用的提示词，
> 体现「人机协同」过程，符合 ICEC 选拔鼓励合理使用 AI 工具的导向。

## 提示词原文

```
我有一批格式不统一的会议/实验记录 txt 文件，放在 raw_data/ 目录下，共 10 个。
每份记录里分散写着：
- 日期（写法多样：2026-10-12、10月13日、2026年10月15号、2026/10/14 等）
- 地点（含"实训室/机房/图书馆/报告厅/工坊/会议室"等词）
- 参与人（在"参与人/参会/到场/人员/包括"那一行，中文姓名用顿号分隔）
- 关键结论（在"结论/小结/关键结论"之后）

请帮我写一个 Python 脚本 extract.py：
1. 读取 raw_data 下所有 txt；
2. 用正则提取上述 4 个字段，日期统一成 YYYY-MM-DD；
3. 输出 summary.csv（列：file,date,location,participants,conclusion）；
4. 用 time.perf_counter() 测量真实运行耗时；
5. 建模一个人工基线耗时（开文件+阅读+手敲，约 25s 起步 + 每字 1/15 秒），
   输出 time_comparison.csv（file,chars,manual_s,ai_s,speedup_x）并给出合计与提速倍数；
6. 生成 report.html 可视化对比。
只使用 Python 标准库，不要第三方依赖。
```

## 使用说明
- 将上面提示词发给任意支持代码的大模型，按其返回的脚本落地到 `extract.py`；
- 运行 `python3 extract.py` 即得全部交付物；
- 本仓库中 `extract.py` 即按该提示词生成并经本人实测调通的最终版本。
