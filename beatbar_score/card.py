"""评分卡渲染（中 / 英 / 日）。"""
from __future__ import annotations

from . import i18n, model

# 参考1-SBT 06 的 7 级表现：(累计 S, 存活秒数, 显示用 mm:ss)
REF_TIERS = [(14.2, 150, "2:30"), (23.0, 245, "4:05"), (34.6, 320, "5:20"),
             (47.6, 420, "7:00"), (68.5, 555, "9:15"), (99.7, 740, "12:20"),
             (113.2, 835, "13:55")]


def _fmt_t(sec):
    return f"{int(sec) // 60}:{int(sec) % 60:02d}"


def required_phi(S):
    return S / 100.0


def describe_requirement(S, lang="zh"):
    """用参考1 的水平描述门槛。"""
    phi = required_phi(S)
    if phi <= REF_TIERS[0][0] / 100:
        return i18n.t(lang, "c_below")
    if phi > REF_TIERS[-1][0] / 100:
        return i18n.t(lang, "c_above")
    for (s0, t0, _n0), (s1, t1, _n1) in zip(REF_TIERS, REF_TIERS[1:]):
        if s0 / 100 <= phi <= s1 / 100:
            f = (phi - s0 / 100) / (s1 / 100 - s0 / 100)
            t = t0 + f * (t1 - t0)
            return i18n.t(lang, "c_ref", t=_fmt_t(t))
    return ""


def render(m, name="", lang="zh", note=""):
    L = []
    w = 46
    L.append("═" * w)
    shown = name
    if lang != "zh":
        for k in ("参考1-", "参考2-", "参考3-"):
            shown = shown.replace(k, "")
    L.append(f"  {shown}")
    L.append("═" * w)
    L.append(f"{i18n.t(lang,'c_duration')} {m['T']:.0f} s   "
             f"{i18n.t(lang,'c_avg')} {m['mean_rate']:.2f} Hz   "
             f"{i18n.t(lang,'c_peak')} {m.get('max_eff', m['max_rate']):.2f} Hz"
             f" ({i18n.t(lang,'c_raw')} {m['max_rate']:.2f})")
    L.append("─" * w)
    L.append(f"  {i18n.t(lang,'c_s'):22s}{m['S']:8.1f}   "
             f"({i18n.t(lang, 'level_%d' % model.level_index(m['S']))})")
    L.append(f"  {i18n.t(lang,'c_speak'):22s}{m['S_peak']:8.1f}")
    L.append(f"  {i18n.t(lang,'c_r60'):22s}{m['R60']:8.2f} Hz")
    L.append(f"  {i18n.t(lang,'c_thi'):22s}{m['T_hi']:8.0f} s")
    nch = f"{m['n_chal']}"
    if m.get("W"):
        nch += f"   W={m['W']}"
    L.append(f"  {i18n.t(lang,'c_nch'):22s}{nch:>8}")
    L.append(f"  {i18n.t(lang,'c_rest'):22s}{m['rest']:8.1f} s"
             f"   ({i18n.t(lang,'c_tier')} {m['brake_tier']})")
    L.append("─" * w)
    L.append("  " + i18n.t(lang, "c_req", phi=required_phi(m["S"])))
    L.append("  " + describe_requirement(m["S"], lang))
    if note:
        L.append("─" * w)
        L.append("  " + note)
    L.append("═" * w)
    return "\n".join(L)


def table(rows, lang="zh"):
    head = (f"{i18n.t(lang,'col_name'):22s}{i18n.t(lang,'col_time'):>7}"
            f"{i18n.t(lang,'col_avg'):>7}{i18n.t(lang,'col_s'):>8}"
            f"{i18n.t(lang,'col_speak'):>8}{i18n.t(lang,'col_r60'):>7}"
            f"{i18n.t(lang,'col_thi'):>6}{i18n.t(lang,'col_n'):>4}")
    out = [head, "─" * (len(head) + 8)]
    for name, m in rows:
        out.append(f"{name[:22]:22s}{m['T']:7.0f}{m['mean_rate']:7.2f}"
                   f"{m['S']:8.1f}{m['S_peak']:8.1f}{m['R60']:7.2f}"
                   f"{m['T_hi']:6.0f}{m['n_chal']:4d}")
    return "\n".join(out)

