"""命令行入口。

用法：
    python -m beatbar_score 文件... [选项]

    --bpm 129.2       指定 BPM（配合 CSV 的 per8 列使用）
    --total 862       该作品的总 Beat 数（用于消除计时误差）
    --name 参考2      覆盖作品名
    --json out.json   把指标写成 JSON
    --table           多个文件时只输出汇总表

示例：
    python -m beatbar_score data/ref1.csv
    python -m beatbar_score data/ref2.csv --bpm 129.2 --total 862
    python -m beatbar_score charts/*.rbarproj --table
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

from . import card, data, i18n, model


def score_one(path, bpm=None, total=None, name=None):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".rbarproj",):
        d = data.load_rbarproj(path)
        grid, raw = model.rate_from_notes(d["times"], d["T"])
        nm = name or d["name"]
    elif ext in (".csv", ".txt"):
        d = data.load_csv(path)
        grid, raw = model.rate_from_intervals(
            d["rows"], bpm or d["bpm"],
            total if total is not None else d["total"])
        nm = name or d["name"]
    else:
        raise ValueError(f"不支持的文件类型：{ext}")
    r = model.cap_rate(raw)
    m = model.metrics(r, raw)
    m["file"] = path
    return nm, m


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="beatbar_score",
        description="BeatBar / HMV 实战难度评分")
    ap.add_argument("files", nargs="+", help="CSV 分段表或 .rbarproj 工程")
    ap.add_argument("--bpm", type=float, help="BPM（配合 per8 列）")
    ap.add_argument("--total", type=float, help="总 Beat 数（消除计时误差）")
    ap.add_argument("--name", help="覆盖作品名")
    ap.add_argument("--json", help="输出 JSON 路径")
    ap.add_argument("--table", action="store_true", help="只输出汇总表")
    ap.add_argument("--lang", choices=list(i18n.LANGS), default="en",
                    help="输出语言：zh / en / ja")
    args = ap.parse_args(argv)

    paths = []
    for pat in args.files:
        hit = sorted(glob.glob(pat))
        if hit:
            # 通配时自动跳过自动保存副本
            paths.extend(p for p in hit if ".autosave" not in p.lower())
        else:
            paths.append(pat)

    rows, out = [], []
    for p in paths:
        try:
            nm, m = score_one(p, args.bpm, args.total, args.name)
        except Exception as e:
            print(f"[跳过] {p}: {e}", file=sys.stderr)
            continue
        rows.append((nm, m))
        out.append(m)

    if not rows:
        print("没有可评分的文件", file=sys.stderr)
        return 1

    if args.table or len(rows) > 1:
        print(card.table(rows, args.lang))
    else:
        print(card.render(rows[0][1], rows[0][0], args.lang))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1, default=str)
        print(f"\n已写入 {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


