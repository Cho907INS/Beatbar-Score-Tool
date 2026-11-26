"""BeatBar 难度模型 v0.9 —— 纯函数实现。

给定一条需求速率曲线 r(t)，算出难度分。
不依赖任何外部状态，K 是标定好的常数。
"""
from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------- 参数
DT = 0.02          # 时间步长（秒）
E0 = 0.50          # 平台期起点
RTH0 = 1.00        # 中性阈值初值（Hz）
BETA = 2.00        # 即时压制系数
Q = 1.20           # 超线性指数
RREF = 3.00        # 参考速率
K = 0.000736       # 标定增速（1/s）
RHO = 0.85         # 刹车递减系数

REST_MIN = 1.5     # 单段休息计入的最短时长
REST_FREE = 10.0   # 累计休息的免费额度
REST_STEP = 20.0   # 之后每满多少加一档

CAP_LONG = 4.6     # 可持续速率上限的稳态值
CAP_BURST = 7.7    # 短时冲刺上限
CAP_TAU = 12.0     # 上限衰减时间常数

CH_HZ = 4.0        # 挑战段速率阈值
CH_MIN = 10.0      # 挑战段最短时长
CH_GAP = 2.0       # 挑战段合并间隔

LEVELS = [(0, "练手级"), (20, "常规"), (40, "高挑战"),
          (60, "顶级"), (100, "超出经典量级")]


# ---------------------------------------------------------------- 速率处理
def cap_rate(r):
    """把超出可持续上限的速率削平（不可能的段落不再额外加分）。"""
    out = np.empty_like(r)
    ht = 0.0
    for i, v in enumerate(r):
        if v > 3.0:
            ht += DT
            out[i] = min(v, CAP_LONG + (CAP_BURST - CAP_LONG) * np.exp(-ht / CAP_TAU))
        else:
            ht = 0.0
            out[i] = v
    return out


def rate_from_intervals(rows, bpm=None, total_beats=None):
    """[(start_s, end_s, beats, per8|None), ...] → 速率曲线。

    有 per8 且给了 BPM 时用 `per8 × BPM/480`（更准），否则用 `beats/时长`。
    给了 total_beats 时，整体缩放使积分等于该总数（消除计时误差）。
    """
    T = max(b for _a, b, _n, _p in rows)
    grid = np.arange(0.0, T, DT)
    r = np.zeros_like(grid)
    for a, b, n, per8 in rows:
        dur = b - a
        if dur <= 0:
            continue
        if per8 is not None and bpm:
            hz = per8 * bpm / 480.0
        else:
            hz = n / dur
        r[(grid >= a) & (grid < b)] = hz
    if total_beats:
        cur = float(np.trapezoid(r, dx=DT))
        if cur > 0:
            r *= total_beats / cur
    return grid, r


def rate_from_notes(times, T=None, sigma=0.15):
    """音符时刻（秒）→ 高斯核密度速率曲线。"""
    times = np.asarray(times, dtype=float)
    if T is None:
        T = float(times[-1]) + 1.0
    grid = np.arange(0.0, T, DT)
    spikes = np.zeros_like(grid)
    idx = np.round(times / DT).astype(int)
    idx = idx[(idx >= 0) & (idx < len(grid))]
    np.add.at(spikes, idx, 1.0)
    half = int(5 * sigma / DT)
    xs = np.arange(-half, half + 1) * DT
    kern = np.exp(-0.5 * (xs / sigma) ** 2)
    kern /= kern.sum() * DT
    return grid, np.convolve(spikes, kern, mode="same")


# ---------------------------------------------------------------- 模拟
def _brake_tier(total):
    if total < REST_FREE:
        return 0
    return 1 + int((total - REST_FREE) // REST_STEP)


def simulate(r):
    """返回 (E_end, 累计休息秒, 修正档位)。"""
    E, n, total = E0, 0, 0.0
    started, in_rest, rest = False, False, 0.0
    for v in r:
        th = max(0.0, RTH0 - BETA * (E - E0))
        if th <= 0 or v >= th:
            started = True
            if in_rest:
                if rest >= REST_MIN:
                    total += rest
                    n = _brake_tier(total)
                in_rest, rest = False, 0.0
            E += K * max(0.0, (v - th) / max(1e-6, RREF - th)) ** Q * DT
        elif started:
            in_rest = True
            rest += DT
            if E < 1.0:
                E = max(E0, E - 2.0 * K * RHO ** n * (1 - v / th) * DT)
    if in_rest and rest >= REST_MIN:
        total += rest
        n = _brake_tier(total)
    return E, total, n


def find_challenges(r):
    """≥4 Hz 且 ≥10 s 的挑战段。"""
    mask = r >= CH_HZ
    segs, i = [], 0
    while i < len(r):
        if not mask[i]:
            i += 1
            continue
        j = i
        while j < len(r) and mask[j]:
            j += 1
        if segs and (i - segs[-1][1]) * DT < CH_GAP:
            segs[-1] = (segs[-1][0], j)
        else:
            segs.append((i, j))
        i = j
    out = []
    for a, b in segs:
        dur = (b - a) * DT
        if dur < CH_MIN:
            continue
        seg = r[a:b]
        load = float(sum(max(0.0, (v - RTH0) / (RREF - RTH0)) ** Q
                         for v in seg) * DT)
        out.append(dict(t0=a * DT, t1=b * DT, dur=dur,
                        mean=float(seg.mean()), load=load))
    return out


# ---------------------------------------------------------------- 汇总
def metrics(r, raw_r=None):
    """输入速率曲线，输出全部指标。"""
    E, rest, n = simulate(r)
    S = 100.0 * (E - E0) / (1 - E0)

    n60 = int(60 / DT)
    if len(r) > n60:
        means = [r[i:i + n60].mean() for i in range(0, len(r) - n60, int(1 / DT))]
        k = int(np.argmax(means))
        R60 = float(means[k])
        Ep = simulate(r[k * int(1 / DT):k * int(1 / DT) + n60])[0]
        S_peak = 100.0 * (Ep - E0) / (1 - E0)
    else:
        R60 = float(r.mean())
        S_peak = S

    T_hi = float(np.sum(r >= 0.85 * R60) * DT)
    ch = find_challenges(r)
    W = None
    if len(ch) >= 4:
        loads = [c["load"] for c in ch]
        W = float(np.mean(loads[-2:]) / max(1e-9, np.mean(loads[:2])))
    elif len(ch) >= 2:
        W = 1.0

    rr = raw_r if raw_r is not None else r
    return dict(S=round(S, 1), S_peak=round(S_peak, 1),
                R60=round(R60, 2), T_hi=round(T_hi, 0),
                n_chal=len(ch), challenges=ch,
                W=round(W, 2) if W else None,
                rest=round(rest, 1), brake_tier=n,
                T=round(len(r) * DT, 1),
                mean_rate=round(float(rr.mean()), 2),
                max_rate=round(float(rr.max()), 2),
                max_eff=round(float(r.max()), 2))


def level_index(S):
    """返回等级序号：0 练手 / 1 常规 / 2 高挑战 / 3 顶级 / 4 超出经典。"""
    idx = 0
    for i, (th, _name) in enumerate(LEVELS):
        if S >= th:
            idx = i
    return idx


def level_of(S):
    return LEVELS[level_index(S)][1]


