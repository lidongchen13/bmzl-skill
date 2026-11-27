#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build a 《笔墨之林》 article DOCX from a JSON spec.

用法:
    python build_docx.py --spec article.json --out out/xxx_笔墨之林.docx [--strict]

JSON 结构（最短可用）:
{
  "meta": {"authors": "...", "title": "...", "journal": "...", "date": "...", "doi": "..."},
  "cover": {"path": "cover.png", "note": "注：封面图片由推文作者自制。"},   # 可选
  "headline": "【笔墨之林】JEEA: 主标题——副标题",
  "recommend": "【推荐理由】……",
  "blocks": [
    {"heading": "1. 研究背景"},
    {"p": "正文段落，可用 **加粗**"},
    {"subheading": "2.1 研究数据"},
    {"equation": {"path": "eq1.png", "width_cm": 6.2}},
    {"exhibit": {"caption": "表1: ……", "image": "tab1.png", "width_cm": 14.65}},
    {"figure": {"caption": "图1: ……", "image": "fig1.png"}},
    {"note": "注：……"},
    {"author": {"photo": "author.png", "text": "【姓名】，【单位】，研究方向为【研究方向】。"}}
  ]
}

图片路径相对 JSON 文件所在目录（也接受绝对路径）。
"""
import argparse
import json
import os
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

CN = "仿宋"
EN = "Times New Roman"
TEXT_W = 14.65          # cm，正文栏宽 = 21 - 3.175*2
HEADLINE_PREFIX = "【笔墨之林】"


# ---------------------------------------------------------------- low level
def setup_document():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.left_margin = Cm(3.175)
    sec.right_margin = Cm(3.175)
    sec.top_margin = Cm(2.54)
    sec.bottom_margin = Cm(2.54)
    # 行网格：与笔墨之林原模板一致，正文按 15.6pt 网格对齐（观感约为 1.5 倍行距）
    grid = OxmlElement("w:docGrid")
    grid.set(qn("w:type"), "lines")
    grid.set(qn("w:linePitch"), "312")
    sec._sectPr.append(grid)

    normal = doc.styles["Normal"]
    normal.font.name = EN
    normal.font.size = Pt(12)
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:ascii"), EN)
    rfonts.set(qn("w:hAnsi"), EN)
    rfonts.set(qn("w:eastAsia"), CN)
    rfonts.set(qn("w:cs"), EN)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    return doc


def style_run(run, size=12, bold=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    rpr = run._r.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:ascii"), EN)
    rfonts.set(qn("w:hAnsi"), EN)
    rfonts.set(qn("w:eastAsia"), CN)
    rfonts.set(qn("w:cs"), EN)
    if bold:
        rpr.append(OxmlElement("w:bCs"))


def add_text(doc, text, align=None, size=12, bold_all=False, line=None,
             keep_with_next=False):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    if line is not None:
        p.paragraph_format.line_spacing = line
    if keep_with_next:
        p.paragraph_format.keep_with_next = True
    for i, seg in enumerate(str(text).split("**")):
        if not seg:
            continue
        r = p.add_run(seg)
        style_run(r, size=size, bold=bold_all or (i % 2 == 1))
    return p


def add_blank(doc, align=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    return p


def add_image(doc, path, width_cm):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(path, width=Cm(width_cm))
    return p


def resolve(path, base_dir):
    if os.path.isabs(path):
        return path
    candidate = os.path.join(base_dir, path)
    if not os.path.exists(candidate):
        raise SystemExit("找不到图片: %s（相对 %s）" % (path, base_dir))
    return candidate


# ---------------------------------------------------------------- blocks
def emit_meta(doc, meta):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.5
    style_run(p.add_run("0. 原文信息"), bold=True)
    for label, key in (("作者", "authors"), ("题目", "title"),
                       ("期刊", "journal"), ("时间", "date"), ("DOI", "doi")):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = Pt(22)
        style_run(p.add_run(label + ": "), bold=True)
        style_run(p.add_run(str(meta.get(key, ""))), bold=False)


def emit_content(doc, block, base_dir):
    """Emit one block's content; surrounding blank lines are handled by the caller."""
    if "heading" in block:
        add_text(doc, block["heading"], bold_all=True, keep_with_next=True)
        return "heading"

    if "subheading" in block:
        add_text(doc, block["subheading"], align=WD_ALIGN_PARAGRAPH.LEFT,
                 bold_all=True, keep_with_next=True)
        return "subheading"

    if "p" in block:
        add_text(doc, block["p"])
        return "p"

    if "note" in block:
        add_text(doc, block["note"], align=WD_ALIGN_PARAGRAPH.CENTER, size=10.5)
        return "note"

    if "equation" in block:
        spec = block["equation"]
        add_image(doc, resolve(spec["path"], base_dir), spec.get("width_cm", 7.0))
        return "equation"

    if "exhibit" in block:
        spec = block["exhibit"]
        p = add_text(doc, spec["caption"], align=WD_ALIGN_PARAGRAPH.CENTER,
                     keep_with_next=True)
        p.paragraph_format.space_after = Pt(4)
        add_image(doc, resolve(spec["image"], base_dir), spec.get("width_cm", TEXT_W))
        return "exhibit"

    if "figure" in block:
        spec = block["figure"]
        img = add_image(doc, resolve(spec["image"], base_dir), spec.get("width_cm", TEXT_W))
        if spec.get("caption"):
            img.paragraph_format.keep_with_next = True   # 图题在下，别被分页切开
            p = add_text(doc, spec["caption"], align=WD_ALIGN_PARAGRAPH.CENTER)
            p.paragraph_format.space_before = Pt(4)
        return "figure"

    if "author" in block:
        spec = block["author"]
        if spec.get("photo"):
            add_image(doc, resolve(spec["photo"], base_dir), 4.2)
        else:
            add_text(doc, "【作者照片】", align=WD_ALIGN_PARAGRAPH.CENTER)
        add_blank(doc, WD_ALIGN_PARAGRAPH.CENTER)
        add_text(doc, spec.get("text", ""), align=WD_ALIGN_PARAGRAPH.CENTER, line=1.5)
        return "author"

    raise SystemExit("未知 block 类型: %r" % (block,))


# ---------------------------------------------------------------- audit
def count_words(chunks):
    text = "".join(chunks)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9\.\-/%,]*", text))
    return cjk + latin


def body_text(doc):
    """正文 = 1. 研究背景 到 3. 研究结论与贡献 之间（不含图表题）。"""
    out, inside = [], False
    for p in doc.paragraphs:
        t = p.text.strip()
        if t.startswith("1.") and "研究背景" in t:
            inside = True
            continue
        if t.startswith("4.") and "本期作者" in t:
            inside = False
            continue
        if not inside or not t:
            continue
        if re.match(r"^[表图]\d+:", t):
            continue
        out.append(t)
    return out


def audit(doc, spec, body_only=False):
    all_chunks = [p.text for p in doc.paragraphs]
    text = "".join(all_chunks)
    words = count_words(all_chunks)
    body_words = count_words(body_text(doc))
    gate = body_words if body_only else words

    problems, warnings = [], []
    if gate > 2500:
        problems.append("字数 %d 超过上限 2500%s"
                        % (gate, "（仅正文口径）" if body_only else ""))
    elif gate < 1000:
        warnings.append("字数 %d 低于下限 1000%s"
                        % (gate, "（仅正文口径）" if body_only else ""))

    rec_body = spec.get("recommend", "").replace("【推荐理由】", "")
    if len(rec_body) > 120:
        problems.append("推荐理由 %d 字符，超过 120" % len(rec_body))

    if "（" in text or "）" in text:
        problems.append("存在全角括号，需改为英文半角")

    n_exhibit = sum(1 for b in spec.get("blocks", []) if "exhibit" in b or "figure" in b)
    if n_exhibit > 3:
        problems.append("图表 %d 张，超过 3 张上限" % n_exhibit)

    head = spec.get("headline", "")
    if not head.startswith(HEADLINE_PREFIX):
        problems.append("标题未以【笔墨之林】开头")
    if "：" in head:
        problems.append("标题含中文冒号，应为英文冒号 + 空格")
    if "——" not in head:
        warnings.append("标题没有中文破折号 ——")

    n_heading = sum(1 for b in spec.get("blocks", []) if "heading" in b)
    if n_heading != 4:
        problems.append("节标题 %d 个，应为 4 个（1/2/3/4）" % n_heading)

    # —— 结构与表达抽查（提示性，不阻断）——
    for bad in ("我们", "同时", "与此同时", "较多", "几天", "颠覆"):
        if bad in text:
            warnings.append("出现「%s」，核对是否违反表达规范" % bad)

    blocks = spec.get("blocks", [])
    for b in blocks:
        if "exhibit" in b:
            cap = b["exhibit"].get("caption", "")
            if not re.match(r"^[表图]\d+: ", cap):
                problems.append("图/表题应为「表1: ……」（英文冒号+空格）：%s" % cap[:24])

    n_eq = sum(1 for b in blocks if "equation" in b)
    if n_eq > 2:
        problems.append("公式 %d 个，超过 2 个上限（只需两个回归方程）" % n_eq)
    elif n_eq < 2:
        warnings.append("公式 %d 个；规范要求 2.2 给出两个回归方程" % n_eq)

    for i, b in enumerate(blocks):
        if "exhibit" not in b or i == 0:
            continue
        prev = blocks[i - 1]
        if "p" in prev and "(第" not in prev["p"]:
            warnings.append("图表前一段没有列号引用：%s"
                            % b["exhibit"].get("caption", "")[:20])

    return words, body_words, problems, warnings, n_exhibit


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True, help="JSON 稿件描述文件")
    ap.add_argument("--out", required=True, help="输出 .docx 路径")
    ap.add_argument("--strict", action="store_true", help="有问题时以非零码退出")
    ap.add_argument("--body-only", action="store_true",
                    help="字数只统计 1–3 节正文（不含标题、原文信息、推荐理由、图表题）")
    args = ap.parse_args()

    with open(args.spec, encoding="utf-8-sig") as fh:
        spec = json.load(fh)
    base_dir = os.path.dirname(os.path.abspath(args.spec))

    doc = setup_document()
    emit_meta(doc, spec.get("meta", {}))

    cover = spec.get("cover")
    if cover:
        add_blank(doc, WD_ALIGN_PARAGRAPH.CENTER)
        add_image(doc, resolve(cover["path"], base_dir), cover.get("width_cm", TEXT_W))
        if cover.get("note"):
            add_text(doc, cover["note"], align=WD_ALIGN_PARAGRAPH.CENTER, size=10.5)

    add_blank(doc, WD_ALIGN_PARAGRAPH.CENTER)
    add_text(doc, spec.get("headline", ""), bold_all=True)
    add_blank(doc)
    add_text(doc, spec.get("recommend", ""))

    prev = "recommend"
    for block in spec.get("blocks", []):
        kind = next(iter(block))
        if kind == "heading":
            add_blank(doc)
            add_blank(doc)
        elif kind == "subheading":
            if prev != "heading":
                add_blank(doc)
        elif prev != "recommend":
            add_blank(doc)
        emit_content(doc, block, base_dir)
        if kind in ("heading", "subheading"):
            add_blank(doc)
        prev = kind

    body = doc.element.body
    sect = body.find(qn("w:sectPr"))
    if sect is not None:
        body.remove(sect)
        body.append(sect)

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    doc.save(args.out)

    words, body_words, problems, warnings, n_exhibit = audit(doc, spec, args.body_only)
    print("saved: %s" % args.out)
    print("字数(全文口径): %d" % words)
    print("字数(正文口径): %d" % body_words)
    print("图表: %d 张" % n_exhibit)
    print("计分口径: %s" % ("正文" if args.body_only else "全文"))
    for w in warnings:
        print("WARN: %s" % w)
    for p in problems:
        print("ERROR: %s" % p)
    if problems and args.strict:
        sys.exit(1)


if __name__ == "__main__":
    main()
