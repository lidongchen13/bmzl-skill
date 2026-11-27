---
name: bmzl
description: >-
  按《笔墨之林》推文规范，把一篇经济学实证论文写成可直接交稿的中文推文，并输出排版合规的 Word。Use for 笔墨之林推文、BMZL 推文、
  公众号推文、论文推文、把这篇文章写成推文、帮我写一篇推文, when the user supplies an economics paper (PDF or full text) and wants the
  笔墨之林 format: 0 原文信息 / 【笔墨之林】标题 / 【推荐理由】/ 1 研究背景 / 2 研究内容 / 3 研究结论与贡献 / 4 本期作者.
  也用于返修已有笔墨之林稿（改结构、压字数、换图表、调格式、补列号）。Not for academic manuscripts, literature reviews,
  translation, referee responses, or slide decks.
---

# BMZL：笔墨之林推文写作

把一个期刊论文（多为英文实证论文）写成中文公众号推文，交一份可直接进排版流程的 `.docx`。

## 交付物

- 一个 Word 文件：`<论文短标题>_笔墨之林.docx`，放在用户给出的目录下。
- 正文 **1,000–2,500 字（硬上限，绝不可超）**，结构固定为 0–4 节，三张以内图表，公式为截图。
- 不交付 Markdown、PDF、PPT；稿子本身即最终物。
- 范例：`references/example.md`（已采纳稿的文本版，2,482 字；含篇幅分配与"值得学的五处"，图表位置按表上图下标注）。

## 开工前必做的三件事

1. **读全文**：正文、全部表与图、脚注、附录（有则读）。只读摘要就下笔是本技能最常见的失败。
2. **建数字账本**：把每个可引用的数字抄成一行——`系数 / 标准误 / p值 / 表号 + 列号 / 样本量`。后文所有数字只能从账本里取，不得凭印象写。
3. **定期刊缩写与中文标题**：缩写取期刊通用简称（AER、JPE、QJE、ECMA、REStud、JEEA、JAERE、JEEM、AEJ: Applied …）。标题自拟，不要直译英文标题。

## 写作顺序（**不要**从第一段开始写）

| 步 | 写什么 | 为什么这个顺序 |
|---|---|---|
| 1 | 2.3 研究结果（三段表报 + 一段适应与投影） | 先钉死数字与结论，后面各节都从它派生 |
| 2 | 2.1 研究数据、2.2 研究方法 | 为 2.3 的每个结果提供来源与识别依据 |
| 3 | 1 研究背景（三段） | 读者需要的信息量由正文倒推 |
| 4 | 3 研究结论与贡献（两段） | 只概括，不重复 2.3 的数字 |
| 5 | 【推荐理由】（≤120 字符）、标题、【0 原文信息】 | 最后写，因为要概括全文 |
| 6 | 出图：封面、表格截图、公式截图 | 见「脚本」 |
| 7 | 组装 JSON → `build_docx.py` → 自检 → 交付 | 见「脚本」与 `references/checklist.md` |

写每一节前打开 `references/blueprint.md` 对应小节，照它的句式骨架与字数预算写；规则有争议时查 `references/spec.md`。

## 硬性规范（违反即退稿）

字数
- 全文 1,000–2,500 字；`build_docx.py` 同时打印「全文口径」与「正文口径」两个字数。
- 默认按**全文口径**卡 2,500（中文每字 1、英文每词 1，含标题、原文信息、图表题）；若主编只看正文，加 `--body-only`，此时只统计 1–3 节（不含图表题与原文信息）。

版式
- 中文仿宋小四（12pt），英文 Times New Roman，两端对齐，**正文一律不缩进**。
- 段落之间空一行；每节首段前、末段后各空一行。
- 重点加粗；**不用斜体**；数字前后不加空格。
- 括号一律英文半角，并按邻接字符决定空格：前接英文/数字则括号前加空格（`Zhang et al. (2025)`），前接中文则不加（`列(1)`、`人口(2020年)`）；括号后的规则同理。

图表
- 最多 3 张图表；**必须用论文原表/原图的截图**，不用 Word 原生表格重画。
- 截图**不含英文表题（TABLE n.）与 Notes**；**表上图下**：表题放表格上方、图题放图片下方，居中、依次编号：`表1: ……`、`图1: ……`（英文冒号+空格）。
- 正文图表**不需要**再标"图片来源"（团队约定）；只有封面图要写一行来源注。
- 表题前空一行，图/表后空一行；表格建议 ≤6 列。
- 正文提到图表时，先说「表1报告……」，再逐列给数；**每个系数后注明列号**：`13%(第1列)`。

公式
- 公式用白底截图，与上段文字间空一行，公式后空一行。
- 正文说明符号时先交代下标：`式中，下标i表示个体，c表示社区，m表示出生月份，t表示年份。`
- 变量前后格式全文统一，正文用不带下标的字母（Y、R、X、Φ、ε）。

结构
- 0 原文信息 / 标题 / 【推荐理由】/ 1 研究背景（**三段**）/ 2 研究内容（2.1、2.2、2.3）/ 3 研究结论与贡献（**两段**）/ 4 本期作者。
- 各节的写法见 `references/blueprint.md`，结构不对等于重写。

语言
- 第三人称、学术语体：`本文识别……`、`识别策略采用……`、`本文测算……`；不出现「我们」。
- 一句话不超过两行，一个句子只承载一层逻辑；不「一逗到底」。
- 段首不用「但是」；不用「同时/与此同时」；不用「颠覆了」这类夸张词；不用「较多」「几天」这类模糊词。
- 标点：中文用全角，括号用半角；冒号前不宜过长。

## 脚本

三个脚本都在 `scripts/`，用工作区的 Python 运行（先 `load_workspace_dependencies` 取路径）。

```bash
# 1) 从 PDF 裁一张表/图（自动去掉英文表题与 Notes；只依赖 poppler）
python scripts/crop_exhibit.py --pdf paper.pdf --page 14 \
  --start "TABLE 1." --end "Notes" --out build/tab1.png

# 2) 渲染公式为白底 PNG（需要 TeXLive 的 pdflatex）
python scripts/render_equation.py \
  --tex "Y_{ict}=\beta R_{ct}+X_{ct}\gamma+\Phi_{ct}+\varepsilon_{ict}" --out build/eq1.png

# 3) 组装 Word（读 JSON，打印字数与自检信息；--strict 有问题即非零退出）
python scripts/build_docx.py --spec build/article.json --out out/xxx_笔墨之林.docx --strict
# 只按正文口径卡字数时加 --body-only
```

- **表**用默认 `--mode table`（表题在上、Notes 在下）；**图的题注在图下方**，必须加 `--mode figure`；两种自动模式都不对时用 `--mode clip "x0,y0,x1,y1"` 手框（points）。
- **扫描件 / 无文字层 PDF**：`--mode table|figure` 全都会失效（它们靠文字坐标定位）。改用 `--list-bands` 打印本页所有内容块及其 y 范围，再用 `--mode clip` 按该范围精确框选：
  ```bash
  python scripts/crop_exhibit.py --pdf scan.pdf --page 3 --list-bands --out tmp.png
  python scripts/crop_exhibit.py --pdf scan.pdf --page 3 --mode clip --clip "70,120,415,330" --out build/tab1.png
  ```
  若整页就是一张图，直接 `--clip` 到页面出血位（如 `"0,0,595,842"`）。先渲染一张页面预览（`office_render` 或 `pdftoppm -r 100`）再定坐标最快。
- 定位页码：`pdfinfo paper.pdf` 看总页数，`pdftotext -f N -l N -layout paper.pdf -` 里搜 `TABLE 1.` 确认物理页码（不是期刊页码）。
- `crop_exhibit.py` 会提示 natural size 与建议宽度：表一律按 14.65 cm（正文栏宽）插入。
- `render_equation.py` 会给出 `suggested width_cm`，直接抄进 JSON。
- 依赖：`python-docx`、`Pillow`（工作区运行时已带）、poppler、TeXLive；缺哪个就补到当前解释器。
- 脚本的中间文件写在输出目录下的普通子目录；不要写到系统临时目录或隐藏目录，某些环境会拒绝写入。
- 找不到 `pdftotext`/`pdflatex` 时，把 TeXLive 的 `bin\windows` 加进 PATH，或设 `TEXBIN` 环境变量。

## 交付前

逐项过 `references/checklist.md`。至少确认：字数、三张图表是否含 Notes、括号是否全半角、标题冒号、推荐理由字符数、每节段落数（背景 3 段、结论 2 段、结果 3+1 段）。

## 退稿高发点（本技能历史返工统计）

1. 直接把英文表贴进去，标题与 Notes 没裁掉。
2. 结果部分只罗列系数，不写经济含义，没有收束句。
3. 每个系数后没有列号，读者对不上表。
4. 研究背景写成文献综述，没有把「经济问题」提炼出来。
5. 结论与 2.3 大段重复。
6. 字数超限后靠删空格、改标点凑数。
7. 括号中英混用；数字与单位之间加空格。
