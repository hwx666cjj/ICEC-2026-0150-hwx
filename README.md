# ICEC-2026 选拔考核 · 过程仓库

> 深圳城市职业学院 · 信息与通信学院「智能·创造者」创新实验班（ICEC）2026 级选拔考核过程留痕仓库。
> 本仓库按选拔大纲 `assessment.html` 的 GitHub 规范组织，记录基础素养实地测评与 AI 协同过程。

## 选题说明
- **第一阶段（基础素养实地测评，10选2，20分）**：已完成 **课题10 · 日常数字任务耗时审计与 AI 批处理实证**
  - 选择理由：10 个实地课题中唯一不依赖「校园实地测量 + 本人现场同框照片」的数字任务，最契合「用 AI 工具完成重复数字任务」的考核导向，且可由本人真实运行产出可核验数据。
- （其余 9 个实地课题需到校实地采样与同框认证，留待线下补做。）

## 仓库结构（遵循大纲 Step 0 规范）
```
ICEC-2026-学号后四位-姓名拼音/
├── README.md                      # 本文件：选题与结构说明
├── 01-Field-Discovery/            # 第一阶段：基础素养实地测评
│   └── Task10-DigitalAudit/       # 课题10 完整交付
│       ├── raw_data/              # 10 份原始样本（note_01..10.txt）
│       ├── make_samples.py        # 样本生成器（可复现）
│       ├── extract.py             # AI 辅助批处理脚本（AI 脚本）
│       ├── AI_PROMPT.md           # 生成脚本所用提示词（Prompt）
│       ├── summary.csv            # 自动提取的结构化汇总
│       ├── time_comparison.csv    # 人工 vs AI 耗时对比表
│       ├── report.html            # 可视化审计报告
│       ├── process_log.md         # 过程记录（迭代与排障）
│       └── process_logs/          # 运行日志目录
└── 03-AI-Collaboration/           # 关键 AI 提问/排障对话存档（见各任务 AI_PROMPT.md）
```

## 提交与运行指引
```bash
# 1. 生成样本
python3 01-Field-Discovery/Task10-DigitalAudit/make_samples.py
# 2. 运行 AI 批处理脚本（自动产出 summary.csv / time_comparison.csv / report.html）
python3 01-Field-Discovery/Task10-DigitalAudit/extract.py
# 3. 提交过程留痕
git add . && git commit -m "课题10：样本+AI脚本+耗时审计" && git push origin main
```

## 诚信声明
本仓库全部数据、脚本与日志均为本人真实动手完成；AI 仅作为协同工具，原始数据与过程记录如实提交，无造假或代做。
