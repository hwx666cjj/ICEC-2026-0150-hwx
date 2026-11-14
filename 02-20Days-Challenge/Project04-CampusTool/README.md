# 项目四 · 校园真实痛点轻量化实用程序（7 天运行日志验证）

> 第二阶段（8选1，60分）选题。对应大纲 *Project 04: Campus Utility Software / Agent & 7-Day Telemetry Verification*。

## 一、选定痛点与工具
- **痛点**：班级群 / 课程群消息刷屏，重要通知（截止时间、地点、作业）易被淹没、常错过。
- **工具**：**校园通知/待办提取与每日聚合器** `src/campus_digest.py`
  - 输入：把群通知原文粘贴进 `inbox/*.txt`
  - 处理：规则提取 日期 / 时间 / 关键词（截止·提交 / 事件 / 作业 / 地点）
  - 输出：`digest/YYYY-MM-DD.md` 结构化每日摘要 + `process_logs/telemetry_YYYY-MM-DD.jsonl` 运行遥测
  - 特性：**纯标准库、零依赖、无需联网、可定时自动运行**（不出门、坐桌前即可完成）

> 若不想要"通知聚合"，可改做"错题归档助手"或"器材借还核对"——只需替换 `src/` 的处理逻辑，目录与日志规范不变。

## 二、大纲交付 ↔ 本仓库映射
| 大纲交付 | 落点 | 分值 |
|----------|------|------|
| ① 连续 ≥7 天自动运行日志（脱敏时间戳/调用频次/耗时/报错） | `process_logs/telemetry_*.jsonl`（每日定时跑） | 25 |
| ② 基于日志的 ≥3 次 Git 迭代 Diff | `iterations/` 记录 + `git log -p` | 20 |
| ③ 完整源码 + 8 位真实用户反馈 | `src/campus_digest.py` + `user_feedback/` | 15 |

## 三、7 天执行计划（今日 2026-11-14，封仓 11-24）
- **D1（11-14）脚手架 + 首日运行**：本目录搭好，跑通脚本，产生第 1 天 telemetry。
- **D2–D7（11-15 ~ 11-20）每日定时运行**：系统定时任务每日触发，向同学收集/粘贴当日群通知，脚本自动写摘要+日志。
- **中途迭代（≥3次）**：看着 telemetry/digest 的漏提误提，扩充 `KW` 规则库、修正则、加 `--check` 自检，每次 `git commit` 一次。
- **D? 收尾**：找 8 位同学试用并填 `user_feedback/`，写 `user_feedback/summary.md`。

## 四、每日操作清单（约 3 分钟）
1. 把当天班级群/课程群的重要通知复制粘贴为 `inbox/某批.txt`（多条空行分隔）。
2. 运行：`python3 src/campus_digest.py`
3. 看一眼 `digest/今日.md` 提取是否准确；不准就改 `src/campus_digest.py` 的 `KW` 规则并 `git commit`。
4. 确认 `process_logs/telemetry_今日.jsonl` 多了一行。
5. `git add -A && git commit -m "Dn 运行日志" && git push`（push 在你本机执行）。

## 五、定时自动运行（防摆拍关键）
### Windows 任务计划程序
1. 任务计划程序 → 创建基本任务 → 触发器"每天"、时间如 22:00。
2. 操作"启动程序"：`python.exe`
3. 参数：`绝对路径\src\campus_digest.py`
4. 起始于（可选）：`绝对路径\Project04-CampusTool`
> 即使忘记手动跑，定时任务也会每日生成一条遥测，保证连续性。

### macOS / Linux（cron）
```cron
0 22 * * * cd /绝对路径/Project04-CampusTool && /usr/bin/python3 src/campus_digest.py
```

## 六、自检
```bash
python3 src/campus_digest.py --check    # 列出将处理哪些 inbox 文件，不写盘
```

## 七、真实性声明
- 7 天 telemetry 为**系统定时任务真实每日执行**产生，非一次性补造；
- 源码为本人开发、AI 协同辅助；用户反馈为 8 位真实同学填写。
