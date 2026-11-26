# BeatBar Difficulty Scorer

A repeatable, checkable **difficulty rating for BeatBar / FapHero / HMV works**.

No frame-by-frame video analysis needed — a table of beat counts per segment is enough.

[English documentation](beatbar_score/README_EN.md) · [中文说明](beatbar_score/README.md)

---

## What it gives you

| Metric | Meaning |
|---|---|
| **`S`** | **Main score.** `100` = exactly exhausts the reference player at the rule-defined endpoint of SBT 06 (12:20) |
| `S_peak` | Damage dealt by the hardest 60 seconds alone |
| `R60` / `T_hi` | Rate of the hardest minute, and how long that intensity lasts |
| `N_ch` | Number of peak challenges (≥4 Hz sustained ≥10 s) |
| `W` | Escalation: rising waves vs. flat |
| `φ` | Pass threshold — how much capacity you need relative to the reference run |

Scores are unbounded: `S = 250` means "needs 2.5× the reference margin".

## Download

Grab `BeatBarScore-folder.zip` from the **Releases** page, unzip, run
`BeatBarScore.exe`. No Python required. UI in **English / 中文 / 日本語**.

## Quick start

1. Count beats per segment (or read the on-screen `BEAT n` counter every 7.5 s).
2. Fill a CSV — see [`examples/template.csv`](beatbar_score/examples/template.csv)
   and [`examples/example-Bigmoney.xlsx`](beatbar_score/examples/example-Bigmoney.xlsx).
3. Drop it into the app, press **Score**.

Command line users:

```bash
python -m beatbar_score data/ref1.csv
python -m beatbar_score data/*.csv --table --lang en
```

`.rbarproj` files from
[RhythmBar-Studio-for-FapHero](https://github.com/Tez192780/RhythmBar-Studio-for-FapHero)
are also accepted directly.

## Documentation

- [`beatbar_score/README_EN.md`](beatbar_score/README_EN.md) — usage, input formats, metrics
- [`beatbar_score/README.md`](beatbar_score/README.md) — same, in Chinese
- [`docs/Difficulty Framework v0.9 (EN).md`](docs/Difficulty%20Framework%20v0.9%20%28EN%29.md) — full derivation, parameters, calibration, limitations
- [`docs/Difficulty Framework v0.9 (ZH).md`](docs/Difficulty%20Framework%20v0.9%20%28ZH%29.md) — 中文版

## Status

Model v0.9. The calibration rests on a single anchor (SBT 06 at 740 s), and several
parameters (`β`, `α`, `ρ`) are definitional or deliberately pessimistic rather than
fitted. See the "Known issues" section of the framework document before treating any
score as absolute.

## License

MIT

