#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Crop one table or figure from a PDF, excluding the English caption and the Notes block.

只依赖 poppler（pdftotext / pdftoppm，TeXLive 自带），不需要额外 Python 包。

用法:
    # 表：表题在上、Notes 在下
    python crop_exhibit.py --pdf paper.pdf --page 14 --start "TABLE 1." \
        --end "Notes" --out build/tab1.png

    # 图：图题在下（正文 → 图 → FIGURE n.）
    python crop_exhibit.py --pdf paper.pdf --page 18 --mode figure \
        --start "FIGURE 2." --out build/fig2.png

    # 手动框选（points，原点在左上角），用于版式特殊的图
    python crop_exhibit.py --pdf paper.pdf --page 18 --mode clip \
        --clip "70,60,415,430" --out build/fig2.png

参数
    --mode      table（默认）| figure | clip
    --page      PDF 物理页码（从 1 开始）
    --start     题注起始词，如 "TABLE 1." / "FIGURE 2."
    --end       仅 table 模式：Notes 起始词，默认 "Notes"
    --clip      仅 clip 模式：x0,y0,x1,y1（PDF points）
    --pad       四周留白（pt），默认 3
    --trim      裁掉白边（figure / clip 默认开启；table 需显式加）
"""
import argparse
import os
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET

from PIL import Image

NS = "{http://www.w3.org/1999/xhtml}"


def tool(name):
    for exe in (name, name + ".exe"):
        found = shutil.which(exe)
        if found:
            return found
    for guess in (r"C:\texlive\2026\bin\windows", r"C:\texlive\2025\bin\windows",
                  "/usr/bin", "/usr/local/bin"):
        for exe in (name, name + ".exe"):
            candidate = os.path.join(guess, exe)
            if os.path.exists(candidate):
                return candidate
    raise SystemExit("找不到 %s：安装 poppler / TeXLive 并确保其在 PATH 上" % name)


def page_words(pdf, page):
    out = subprocess.run([tool("pdftotext"), "-f", str(page), "-l", str(page),
                          "-bbox", pdf, "-"],
                         stdout=subprocess.PIPE, check=True).stdout
    root = ET.fromstring(out)
    words = []
    for w in root.iter(NS + "word"):
        words.append((float(w.get("xMin")), float(w.get("yMin")),
                      float(w.get("xMax")), float(w.get("yMax")),
                      (w.text or "").strip()))
    return words


def group_lines(words, tol=2.0):
    lines = []
    for w in sorted(words, key=lambda x: (round(x[1], 1), x[0])):
        if lines and abs(lines[-1][0] - w[1]) <= tol:
            lines[-1][1].append(w)
        else:
            lines.append([w[1], [w]])
    return lines


def find_line(lines, marker):
    target = marker.replace(" ", "").lower()
    for _, words in lines:
        joined = "".join(w[4] for w in sorted(words, key=lambda x: x[0]))
        if joined.replace(" ", "").lower().startswith(target):
            return words
    return None


def span(line):
    return min(w[0] for w in line), max(w[2] for w in line)


def robust_x_range(band, min_gap=12.0, max_right_share=0.35):
    """Ignore a right-hand outlier cluster such as a page watermark."""
    xs = sorted(w[0] for w in band)
    best_gap, best_i = 0.0, -1
    for i in range(len(xs) - 1):
        gap = xs[i + 1] - xs[i]
        if gap > best_gap:
            best_gap, best_i = gap, i
    if best_gap > min_gap and best_i >= 0:
        right_count = len(xs) - best_i - 1
        if right_count <= max_right_share * len(xs):
            cut = xs[best_i + 1]
            kept = [w for w in band if w[0] < cut]
            return min(w[0] for w in kept), max(w[2] for w in kept)
    return min(w[0] for w in band), max(w[2] for w in band)


def render_page(pdf, page, dpi, workdir):
    tmp = os.path.join(workdir, "bmzl_crop_" + uuid.uuid4().hex[:8])
    os.makedirs(tmp, exist_ok=True)
    subprocess.run([tool("pdftoppm"), "-f", str(page), "-l", str(page), "-png",
                    "-r", str(dpi), "-singlefile", pdf, os.path.join(tmp, "page")],
                   check=True)
    img = Image.open(os.path.join(tmp, "page.png")).convert("RGB")
    shutil.rmtree(tmp, ignore_errors=True)
    return img


def trim_white(img, pad_px=12):
    gray = img.convert("L")
    mask = gray.point(lambda v: 255 if v < 248 else 0)
    box = mask.getbbox()
    if box is None:
        return img
    box = (max(0, box[0] - pad_px), max(0, box[1] - pad_px),
           min(img.width, box[2] + pad_px), min(img.height, box[3] + pad_px))
    return img.crop(box)


def ink_bands(img, dpi, x_frac=(0.04, 0.96), min_gap_pt=6.0, min_h_pt=16.0):
    """Return [(y0, y1)] pixel bands of non-white content inside an x window."""
    w, h = img.size
    x0, x1 = int(w * x_frac[0]), int(w * x_frac[1])
    strip = img.convert("L").crop((x0, 0, x1, h)).resize((1, h), Image.BOX)
    vals = list(strip.tobytes())
    bands, start = [], None
    for y, v in enumerate(vals):
        on = v < 250
        if on and start is None:
            start = y
        elif not on and start is not None:
            bands.append((start, y))
            start = None
    if start is not None:
        bands.append((start, h))
    gap_px = min_gap_pt / 72.0 * dpi
    merged = []
    for a, b in bands:
        if merged and a - merged[-1][1] <= gap_px:
            merged[-1] = [merged[-1][0], b]
        else:
            merged.append([a, b])
    min_h = min_h_pt / 72.0 * dpi
    return [(a, b) for a, b in merged if (b - a) >= min_h]


def save(crop, args):
    crop.save(args.out, "PNG")
    w_cm = crop.width / args.dpi * 2.54
    h_cm = crop.height / args.dpi * 2.54
    print("saved: %s" % args.out)
    print("natural size: %.2f x %.2f cm @ %d dpi" % (w_cm, h_cm, args.dpi))
    print("suggested width_cm: %.2f" % min(14.65, w_cm * 1.2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--page", type=int, required=True)
    ap.add_argument("--mode", default="table",
                    choices=["table", "figure", "clip", "band"])
    ap.add_argument("--band", type=int, default=None,
                    help="band 模式：用 --list-bands 打印的序号（从 1 开始）")
    ap.add_argument("--min-gap", type=float, default=6.0,
                    help="band 模式：合并间距小于该值（pt）的内容块；表格取 20 可整块选中")
    ap.add_argument("--list-bands", action="store_true",
                    help="打印本页所有内容块（扫描件没有文字层时用它选图/表）")
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default="Notes")
    ap.add_argument("--clip", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--pad", type=float, default=3.0)
    ap.add_argument("--trim", dest="trim", action="store_true", default=None)
    ap.add_argument("--no-trim", dest="trim", action="store_false")
    args = ap.parse_args()

    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    scale = args.dpi / 72.0

    if args.list_bands or args.mode == "band":
        img = render_page(args.pdf, args.page, args.dpi, out_dir)
        bands = ink_bands(img, args.dpi, min_gap_pt=args.min_gap)
        if args.list_bands:
            print("本页内容块（%d 个，points）：" % len(bands))
            for i, (a, b) in enumerate(bands, 1):
                print("  #%d  y %.0f–%.0f  高 %.2f cm"
                      % (i, a / scale, b / scale, (b - a) / args.dpi * 2.54))
            print("用法：--mode band --band N --out x.png")
            return
        if args.band is None:
            raise SystemExit("band 模式需要 --band N（先跑 --list-bands）")
        if not 1 <= args.band <= len(bands):
            raise SystemExit("--band %d 超出范围（本页 1–%d）" % (args.band, len(bands)))
        a, b = bands[args.band - 1]
        w = img.width
        crop = img.crop((max(0, int(w * 0.04 - args.pad * scale)),
                         max(0, int(a - args.pad * scale)),
                         min(w, int(w * 0.96 + args.pad * scale)),
                         min(img.height, int(b + args.pad * scale))))
        crop = trim_white(crop)
        return save(crop, args)

    if args.mode == "clip":
        if not args.clip:
            raise SystemExit('clip 模式需要 --clip "x0,y0,x1,y1"')
        x0, y0, x1, y1 = [float(v) for v in args.clip.split(",")]
        img = render_page(args.pdf, args.page, args.dpi, out_dir)
        crop = img.crop((int(x0 * scale), int(y0 * scale),
                         int(x1 * scale), int(y1 * scale)))
        if args.trim is not False:
            crop = trim_white(crop)
        return save(crop, args)

    if not args.start:
        raise SystemExit("%s 模式需要 --start（题注起始词）" % args.mode)

    words = page_words(args.pdf, args.page)
    if not words:
        raise SystemExit("第 %d 页没有可提取的文字（可能是扫描件），改用 --mode clip"
                         % args.page)
    lines = group_lines(words)
    cap_line = find_line(lines, args.start)
    if cap_line is None:
        raise SystemExit("未找到题注 %r（第 %d 页）。可改用 --mode clip 手动框选"
                         % (args.start, args.page))
    y_cap_top = min(w[1] for w in cap_line)

    if args.mode == "table":
        y_top = max(w[3] for w in cap_line) + 0.5
        end_line = find_line(lines, args.end) if args.end else None
        if end_line is None:
            print("WARN: 未找到 %r，裁剪将延伸到页底，可能带入正文" % args.end)
            y_bottom = max(w[3] for w in words)
        else:
            y_bottom = min(w[1] for w in end_line)
        band = [w for w in words if w[1] >= y_top and w[3] <= y_bottom + 0.5
                and (w[3] - w[1]) <= 16]
        if not band:
            raise SystemExit("题注与 %r 之间没有内容，检查 --start/--end" % args.end)
        bx0, bx1 = robust_x_range(band)
        img = render_page(args.pdf, args.page, args.dpi, out_dir)
        crop = img.crop((max(0, int((bx0 - args.pad) * scale)),
                         max(0, int((y_top - 0.2) * scale)),
                         min(img.width, int((bx1 + args.pad) * scale)),
                         min(img.height, int((y_bottom - 0.5) * scale))))
        if args.trim:
            crop = trim_white(crop)
        return save(crop, args)

    # figure：题注在图下方，向上找最近的通栏正文行作为上边界
    page_w = max(span(l)[1] for _, l in lines) - min(span(l)[0] for _, l in lines)
    y_top = None
    for _, line in reversed(lines):
        top = min(w[1] for w in line)
        if top >= y_cap_top or top < 45:      # 题注自身 / 页眉
            continue
        lx0, lx1 = span(line)
        if (lx1 - lx0) > 0.55 * page_w:       # 通栏正文行
            y_top = max(w[3] for w in line) + 6
            break
    if y_top is None:
        y_top = max(45.0, y_cap_top - 400)
        print("WARN: 未找到图上方的通栏正文行，按题注上方 400pt 截取并裁白")

    # 图往往没有文字层（坐标轴被转成曲线），横向直接用通栏正文的左右边界
    col = [span(l) for _, l in lines if (span(l)[1] - span(l)[0]) > 0.55 * page_w]
    if col:
        bx0, bx1 = min(c[0] for c in col), max(c[1] for c in col)
    else:
        bx0, bx1 = min(w[0] for w in words), max(w[2] for w in words)
    img = render_page(args.pdf, args.page, args.dpi, out_dir)
    crop = img.crop((max(0, int((bx0 - args.pad) * scale)),
                     max(0, int(y_top * scale)),
                     min(img.width, int((bx1 + args.pad) * scale)),
                     min(img.height, int((y_cap_top - 2) * scale))))
    crop = trim_white(crop)
    return save(crop, args)


if __name__ == "__main__":
    main()
