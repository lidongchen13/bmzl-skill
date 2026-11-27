# BMZL · 笔墨之林推文写作技能

把一篇经济学实证论文，写成《笔墨之林》公众号规范的**中文推文**，并直接产出一份排版合规的 Word。

这是给 AI Agent 用的 **Skill**（Agent Skills 格式）：把写作流程、硬性规范、句式模板和三个排版脚本打包在一起，Agent 读到它之后能按固定套路把论文变成可交稿的推文初稿。

---

## 它做什么

输入一篇英文实证论文（PDF 或全文），输出 `xxx_笔墨之林.docx`，结构固定为六节：

| 节 | 内容 |
|---|---|
| 0 原文信息 | 作者 / 题目 / 期刊 / 时间 / DOI |
| 标题 | `【笔墨之林】<期刊缩写>: <主标题>——<副标题>` |
| 【推荐理由】 | ≤120 字符，一句钩子 + 结论 + 机制 |
| 1 研究背景 | **三段**：经济问题 → 背景事实 → 本文做了什么 |
| 2 研究内容 | 2.1 数据 / 2.2 方法（两个回归方程，交代下标、固定效应与聚类）/ 2.3 结果（每张图/表一段 + 一段适应与投影） |
| 3 研究结论与贡献 | **两段**：方法与发现 + 三点贡献 |
| 4 本期作者 | 照片占位 + 一句话简介 |

排版硬约束：仿宋小四、英文 Times New Roman、两端对齐、无缩进、段间空行、**表上图下**、图表用论文原图截图（不含英文表题与 Notes）、公式白底截图、全文 1,000–2,500 字。

## 目录结构

```
bmzl-skill/
├── SKILL.md                 # 主文件：流程、硬性规范、脚本用法
├── manifest.yaml            # 按需加载声明
├── references/
│   ├── blueprint.md         # 分节句式骨架、字数预算、正反例、JSON 模板
│   ├── spec.md              # 写作规范完整条款（SOP 转写）
│   ├── checklist.md         # 交付前 40 条自检
│   └── example.md           # 已采纳样稿的文本版（约 2,480 字）
└── scripts/
    ├── build_docx.py        # JSON → 排版合规的 docx（含字数与格式自检）
    ├── crop_exhibit.py      # 从 PDF 裁表/图，自动去题注与 Notes；支持扫描件
    └── render_equation.py   # LaTeX 公式 → 白底 PNG
```

## 安装

**Claude Code / 通用 Agent Skills**

```bash
git clone https://github.com/<you>/bmzl-skill.git
cp -r bmzl-skill ~/.claude/skills/bmzl
```

**DeepSeek Harness**

```powershell
# 把仓库目录放进本地 skills 根目录，重启会话后生效
Copy-Item -Recurse .\bmzl-skill "$env:USERPROFILE\.dsh\skills\bmzl"
```

## 用法

给 Agent 一份论文 PDF，然后说：

> 用 BMZL 技能把这篇论文写成笔墨之林推文。

Agent 会依次：读全文 → 建数字账本 → 写 2.3 → 写 2.1/2.2 → 写 1 → 写 3 → 写标题与推荐理由 → 裁图 → 组装 Word → 过自检清单。

三个脚本也可以单独用：

```bash
# 裁表（表题在上、Notes 在下）
python scripts/crop_exhibit.py --pdf paper.pdf --page 14 --start "TABLE 1." --end "Notes" --out build/tab1.png

# 裁图（图题在下）
python scripts/crop_exhibit.py --pdf paper.pdf --page 18 --mode figure --start "FIGURE 2." --out build/fig2.png

# 公式
python scripts/render_equation.py --tex "Y_{ict}=\beta R_{ct}+X_{ct}\gamma" --out build/eq1.png

# 组装
python scripts/build_docx.py --spec build/article.json --out out/title_笔墨之林.docx --strict
```

## 依赖

| 用途 | 依赖 |
|---|---|
| `build_docx.py` | `python-docx` |
| `crop_exhibit.py` | poppler（`pdftotext`、`pdftoppm`）+ `Pillow` |
| `render_equation.py` | TeXLive（`pdflatex`）+ `Pillow` |

poppler 通常随 TeXLive 一起提供；Windows 上把 `C:\texlive\<year>\bin\windows` 加进 `PATH`，或设置 `TEXBIN` 环境变量。

## 关于

- 写作规范来自《笔墨之林初稿写作指南》（E3M SOP_ATT_5A）的条款化整理。
- `references/example.md` 是一篇已采纳推文的文本版（读的是 Doshi, *Chicken and Egg: Electricity Transmission and Investment in Renewable Energy*, JPubE 2026），仅作结构与文风参考。

## License

[MIT](LICENSE) © 2026 lidongchen13

代码与文档均可自由使用、修改与再分发，保留版权声明即可。
