#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Render a LaTeX equation to a white-background PNG (screenshot style).

用法:
    python render_equation.py --tex "Y_{ict}=\\beta R_{ct}+X_{ct}\\gamma" --out build/eq1.png

    --tex      数学表达式，不含 $ 定界符；用标准 LaTeX 语法
    --out      输出 PNG（白底、已裁边）
    --dpi      渲染分辨率，默认 600
    --scale    相对自然尺寸的放大倍数，默认 1.33（≈ 正文 12pt 的视觉大小）
    --font     newtx（默认，Times 风格）或 cm（Computer Modern）

输出末尾会打印 natural size 与推荐的插入宽度（cm），直接抄进 JSON 的 width_cm。

需要 TeXLive：pdflatex、pdftoppm 在 PATH 上，或设置环境变量 TEXBIN。
"""
import argparse
import os
import shutil
import subprocess
import sys
import uuid

from PIL import Image, ImageChops


def texbin_dir():
    env = os.environ.get("TEXBIN")
    if env:
        return env
    for exe in ("pdflatex", "pdflatex.exe"):
        found = shutil.which(exe)
        if found:
            return os.path.dirname(found)
    for guess in (r"C:\texlive\2026\bin\windows", r"C:\texlive\2025\bin\windows",
                  "/usr/bin", "/usr/local/bin"):
        if os.path.exists(os.path.join(guess, "pdflatex.exe")) or \
           os.path.exists(os.path.join(guess, "pdflatex")):
            return guess
    raise SystemExit("找不到 pdflatex：安装 TeXLive 或设置 TEXBIN 指向其 bin 目录")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--scale", type=float, default=1.33)
    ap.add_argument("--font", default="newtx", choices=["newtx", "cm"])
    args = ap.parse_args()

    texbin = texbin_dir()
    pdflatex = os.path.join(texbin, "pdflatex.exe")
    if not os.path.exists(pdflatex):
        pdflatex = os.path.join(texbin, "pdflatex")
    pdftoppm = os.path.join(texbin, "pdftoppm.exe")
    if not os.path.exists(pdftoppm):
        pdftoppm = os.path.join(texbin, "pdftoppm")

    extra = ""
    if args.font == "newtx":
        extra = "\\usepackage{newtxtext}\n\\usepackage{newtxmath}\n"

    body = ("\\documentclass[border=4pt,varwidth=false]{standalone}\n"
            "\\usepackage{amsmath}\n" + extra +
            "\\begin{document}\n$" + args.tex + "$\n\\end{document}\n")

    workdir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(workdir, exist_ok=True)
    tmp = os.path.join(workdir, "bmzl_eqtmp_" + uuid.uuid4().hex[:8])
    os.makedirs(tmp, exist_ok=True)

    tex_path = os.path.join(tmp, "eq.tex")
    with open(tex_path, "w", encoding="utf-8") as fh:
        fh.write(body)

    env = dict(os.environ, PATH=texbin + os.pathsep + os.environ.get("PATH", ""))
    for cmd in ([pdflatex, "-interaction=nonstopmode", "-halt-on-error", "eq.tex"],
                [pdftoppm, "-png", "-r", str(args.dpi), "-singlefile", "eq.pdf", "eq_raw"]):
        proc = subprocess.run(cmd, cwd=tmp, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout.decode("utf-8", "ignore")[-3000:])
            shutil.rmtree(tmp, ignore_errors=True)
            raise SystemExit("编译失败：%s" % cmd[0])

    raw = Image.open(os.path.join(tmp, "eq_raw.png")).convert("RGB")
    bbox = ImageChops.difference(raw, Image.new("RGB", raw.size, (255, 255, 255))).getbbox()
    if bbox is None:
        shutil.rmtree(tmp, ignore_errors=True)
        raise SystemExit("渲染出空白图片，检查公式是否合法")
    pad = 18
    box = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
           min(raw.size[0], bbox[2] + pad), min(raw.size[1], bbox[3] + pad))
    img = raw.crop(box)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    img.save(args.out, "PNG")
    shutil.rmtree(tmp, ignore_errors=True)

    w_cm = img.width / args.dpi * 2.54
    h_cm = img.height / args.dpi * 2.54
    print("saved: %s" % args.out)
    print("natural size: %.2f x %.2f cm @ %d dpi" % (w_cm, h_cm, args.dpi))
    print("suggested width_cm: %.2f" % round(w_cm * args.scale, 2))


if __name__ == "__main__":
    main()
