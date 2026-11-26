"""数据读取：分段 CSV 与 .rbarproj 工程。

CSV 格式（首行必须是表头）：

    start,end,beats,per8
    0,15,0,
    15,46,64,
    46,76,76,8.5

- `start` / `end`：区间起止（秒）
- `beats`：该区间的 Beat 数
- `per8`：可选，「每 8 拍有多少 Beat」。填了且给了 BPM，就用它换算频率（更准）

也可以在文件里写元数据注释行：

    # bpm: 129.2
    # total: 862
    # name: 参考2
"""
from __future__ import annotations

import csv
import io
import json
import os


def load_csv(path):
    """返回 dict(rows, bpm, total, name)。"""
    rows, bpm, total, name = [], None, None, None
    with io.open(path, encoding="utf-8-sig") as f:
        lines = [ln for ln in f if ln.strip()]
    data_lines = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("#"):
            k, _, v = s.lstrip("#").partition(":")
            k, v = k.strip().lower(), v.strip()
            if k == "bpm":
                bpm = float(v)
            elif k == "total":
                total = float(v)
            elif k == "name":
                name = v
            continue
        data_lines.append(s)
    if not data_lines:
        raise ValueError(f"{path}: 没有数据行")
    reader = csv.DictReader(io.StringIO("\n".join(data_lines)))
    need = {"start", "end", "beats"}
    if not need.issubset({c.strip() for c in reader.fieldnames or []}):
        raise ValueError(f"{path}: 表头必须包含 start,end,beats（可选 per8）")
    for row in reader:
        row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        a = float(row["start"])
        b = float(row["end"])
        n = float(row["beats"] or 0)
        p = row.get("per8")
        rows.append((a, b, n, float(p) if p else None))
    rows.sort(key=lambda x: x[0])
    return dict(rows=rows, bpm=bpm, total=total,
                name=name or os.path.splitext(os.path.basename(path))[0])


def load_rbarproj(path):
    """读取节奏条工作室工程，返回音符时间（秒）与总时长。"""
    with io.open(path, encoding="utf-8") as f:
        d = json.load(f)
    notes = d.get("chart", {}).get("notes", [])
    if not notes:
        raise ValueError(f"{path}: 工程里没有音符")
    ts = sorted(float(n["t"]) / 1000.0 for n in notes)
    dur = max(float(n.get("dur", 0.0) or 0.0) for n in notes) / 1000.0
    return dict(times=ts, T=ts[-1] + max(dur, 1.0),
                name=os.path.splitext(os.path.basename(path))[0])


def write_example_csv(path):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write("start,end,beats,per8\n0,15,0,\n15,46,64,\n46,76,76,\n")
