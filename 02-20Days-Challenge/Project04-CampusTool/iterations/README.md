# iterations/ —— 基于日志的 Git 迭代记录（大纲交付②：至少 3 次迭代 Diff）

大纲要求：基于运行日志发现的真实问题，做**至少 3 次有实质变更的 Git 提交**，形成迭代。
每次迭代在这里记一笔（也可直接靠 `git log -p` 体现 Diff）。

## 建议的 3 次迭代方向（示例）
1. **迭代1 · 初版上线**：完成基础规则提取 + 摘要 + 遥测，跑通首日日志。
2. **迭代2 · 按日志纠错**：从 telemetry 或 digest 发现漏提/误提（如把"11月"误判、遗漏"提交"），
   扩充 `KW` 规则库或修正正则，提交改进。
3. **迭代3 · 鲁棒性/体验**：处理编码异常、空 inbox 静默、增加 `--check` 自检，提交。

## 记录模板
```
## 迭代N（日期）
- 触发：从 process_logs/telemetry_YYYY-MM-DD.jsonl 或 digest 发现的问题
- 改动：src/campus_digest.py 的哪部分
- 验证：重跑后 items_extracted / errors 变化
- commit：<hash>
```
