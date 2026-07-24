# Portfolio Notes

## One-line description

Built an end-to-end presentation quality pipeline that converts generated
artifacts into rendered evidence, deterministic findings, human annotations,
and structured reports.

## Resume bullets

- Designed a modular Python and Playwright pipeline for staging, rendering,
  evaluating, and reviewing presentation artifacts with traceable provenance.
- Implemented deterministic checks for output availability, page count, and
  content requirements, with JSON, CSV, and XLSX reporting.
- Built a responsive local annotation workspace for slide-level overflow,
  overlap, blank-page, and reviewer-note workflows.
- Separated private source-system collectors from a reusable public evaluation
  core and replaced sensitive fixtures with reproducible synthetic examples.

## 中文简历表述

- 设计并实现生成式 PPT 质量评估流水线，覆盖产物归档、页面渲染、规则检查、人工标注与结构化报告导出。
- 基于 Python 与 Playwright 构建模块化适配器，支持 HTML、图片、PDF 和 PPTX 预览，并保留完整证据链。
- 实现页数、必需内容、禁用内容及缺失产物等确定性检查，并输出 JSON、CSV、XLSX 报告。
- 将内部数据采集逻辑与公开评估核心解耦，使用合成数据构建可复现、可安全发布的 GitHub Demo。

## Interview discussion

Useful design tradeoffs to discuss:

- Why deterministic checks and human review complement rather than replace
  each other
- Why source collectors are adapters instead of evaluator dependencies
- How safe run markers prevent destructive overwrite mistakes
- Where portable PPTX previews stop being sufficient and visual-fidelity
  rendering becomes necessary
- How synthetic fixtures preserve reproducibility without exposing user data
