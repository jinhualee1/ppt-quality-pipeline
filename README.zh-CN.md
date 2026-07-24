# PPT Quality Pipeline

一个可复现的演示文稿质量评估工具链，覆盖文件归档、幻灯片渲染、确定性规则检查、人工视觉标注以及 JSON、CSV、XLSX 报告导出。

[English README](README.md)

![PPT Quality Review 标注工作台](docs/images/review-workspace.png)

## 项目价值

常见的 PPT 评估流程容易散落在一次性脚本、截图目录和人工表格中。本项目将它整理成可追踪的标准流程：

```text
任务 JSONL -> 产物归档 -> 页面渲染 -> 自动问题
           -> 人工标注 -> JSON / CSV / XLSX 报告
```

公开仓库只包含合成数据。与内部系统相关的采集器可以作为私有适配器接入，不需要污染公开代码和数据。

## 核心能力

- 为每个产物保存稳定、可审计的运行目录
- 使用 Playwright 和本机 Chrome/Chromium 渲染 HTML 幻灯片
- 支持图片、PDF，以及可移植的 PPTX 文本预览
- 检查页数、必需内容、禁用内容和缺失产物
- 提供人工标注页面，记录超框、重叠、空白页和备注
- 导出 JSON、CSV 和可选 XLSX 报告
- 防止误覆盖普通目录和目录穿越
- 自带完全合成的正反例 Demo 与单元测试

## 快速开始

需要 Python 3.10+、Node.js 20+ 和 Chrome、Edge 或 Chromium。

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate

python -m pip install -e ".[xlsx,pptx]"
corepack enable
pnpm install

pqp doctor
pqp demo
pqp serve --run-dir runs/demo
```

然后打开 [http://127.0.0.1:8765](http://127.0.0.1:8765)。

Demo 包含两个任务：一个通过全部自动检查；另一个故意缺少一页和一项必需内容，用来展示问题证据与人工标注流程。

## 使用自己的任务

```json
{"id":"deck-001","query":"制作一份三页评审材料","artifacts":[{"path":"deck.html","kind":"html","role":"generated"}],"expectation":{"page_count":3,"required_keywords":["证据","评审"]}}
```

```bash
pqp run --tasks tasks.jsonl --output runs/my-run
pqp serve --run-dir runs/my-run
pqp export --run-dir runs/my-run --format xlsx
```

详细字段见 [任务格式](docs/task-format.md)，实现结构见 [架构说明](docs/architecture.md)。

## 当前边界

- HTML 与图片可进行视觉渲染。
- PDF 需要安装 `pdf` 可选依赖。
- PPTX 默认生成文字预览，不等价于完整视觉渲染；生产环境应接入 LibreOffice、Microsoft PowerPoint 或托管渲染服务。
- 本地标注服务默认只监听 `127.0.0.1`，没有身份认证，不应暴露到不可信网络。

## 测试

```bash
python -m unittest discover -s tests -v
pnpm run check
```

## 许可证

MIT
