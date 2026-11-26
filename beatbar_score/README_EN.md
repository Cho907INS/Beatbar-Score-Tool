# BeatBar Difficulty Scorer

A repeatable, checkable difficulty rating for **BeatBar / FapHero / HMV** works.

You do **not** need to analyse the video frame by frame. A segment table of beat
counts (or a RhythmBar Studio project file) is enough.

> Model v0.9 · GUI in 中文 / English / 日本語 · one-file Windows executable

---

## What it gives you

| Metric | Meaning |
|---|---|
| **`S`** | **Main score.** `100` = exactly exhausts the reference player (SBT 06 at 12:20) |
| `S_peak` | Damage dealt by the hardest 60 seconds alone |
| `R60` | Average rate of the hardest minute (Hz) |
| `T_hi` | Total time at or above `0.85·R60` (s) |
| `N_ch` | Number of peak challenges (≥4 Hz sustained ≥10 s) |
| `W` | Escalation: last two challenges ÷ first two. >2.5 = rising waves, <1.2 = flat |
| `rest` | Effective rest (episodes ≥1.5 s, intro excluded) |
| `φ` | Pass threshold: `S / 100`, i.e. how many times the reference player's capacity you need |

**Tiers**: <20 practice · 20–40 normal · 40–60 hard · 60–100 top tier · >100 beyond classic.

Pass thresholds map directly onto actual performance on the reference work:

| Survived SBT 06 until | Capacity φ | Works you can take (20 % margin) |
|---|---:|---:|
| 2:30 | 0.14 | up to S ≈ 11 |
| 4:05 | 0.23 | 18 |
| 5:20 | 0.35 | 28 |
| 7:00 | 0.48 | 38 |
| 9:15 | 0.69 | 55 |
| 12:20 | 1.00 | 80 |
| to the end | 1.13 | 90 |

---

## Quick start

### Option A — the folder release (no Python needed)

The release is a **folder**. Unzip it and double-click `BeatBarScore.exe` inside.

1. The UI opens in English; switch between **English / 中文 / 日本語** at the top right.
2. Press **Choose files…** and pick one or more `.csv` segment tables or `.rbarproj`
   projects.
3. If the table has a `per8` column, enter the track's BPM (e.g. `129.2`) — it makes
   the result more accurate. You can also enter the total beat count in the Total box.
4. Press **Score**. A score card appears for a single file, or a summary table for
   several.
5. Use **Copy result** or **Save as text** to keep it.

> Example files live in `examples/` next to the exe: `example-Bigmoney.xlsx`
> (a real work you can copy the layout from), `template.csv`, and the segment
> tables of the three reference works.

### Option B — the command line

```bash
# one work -> score card
python -m beatbar_score data/ref1.csv

# several works -> summary table
python -m beatbar_score data/*.csv --table

# a RhythmBar Studio project
python -m beatbar_score "path/to/xxx.rbarproj"

# English output
python -m beatbar_score data/ref2.csv --lang en

# export JSON
python -m beatbar_score data/ref2.csv --json out.json
```

Requires Python 3.10+ and numpy.

---

## Input formats

### 1. Segment table (recommended — works for other people's videos)

CSV with a header:

```csv
start,end,beats,per8
0,15,0,
15,46,64,
46,76,76,
76,92,32,8.5
```

| Column | Meaning | Required |
|---|---|---|
| `start` / `end` | segment boundaries (seconds) | ✅ |
| `beats` | beats inside the segment | ✅ |
| `per8` | **how many beats fall inside each 8-beat phrase** (e.g. 13) | optional, more accurate |

**Why `per8` is better**: a stopwatch is only accurate to a second, and the error
accumulates. Counting notes per 8-beat phrase and converting with the BPM has no
accumulated error: `Hz = per8 × BPM / 480`.

Optional metadata lines at the top:

```csv
# name: Bigmoney
# bpm: 129.2
# total: 862
```

- `bpm` — used together with `per8` (the `--bpm` flag wins)
- `total` — total beat count; the whole curve is rescaled so its integral matches

### 2. Project file (your own charts)

`.rbarproj` is the project format of
**[RhythmBar-Studio-for-FapHero](https://github.com/Tez192780/RhythmBar-Studio-for-FapHero)**.
Only the chart note data is read; nothing is modified.

Open it with **Choose files…** — note times are exact to the millisecond, which makes
this the most accurate of the four input types.

---

## Collecting data

**Method A — read the on-screen counter** (easiest, when the bar has one)

1. Pause every 7.5 s and note `BEAT n`.
2. Subtract consecutive readings → beats per 7.5 s.
3. Fill in `start,end,beats`.

> Some authors' counters wrap back to 1 at a maximum — watch for that.

**Method B — count phrases** (no counter)

Group by musical phrases (usually 2–4 bars), count the beats, and note how many
beats per 8-beat phrase.

**Method C — project file**

For your own charts, just drop the `.rbarproj` in.

---

## Measured works

| Work | Length | S | Notes |
|---|---:|---:|---|
| 参考1-SBT 06 | 835 s | **113.2** | Calibration anchor; rule endpoint 12:20 = 100 |
| 参考3-Rezorecta | 360 s | **58.1** | 7.5 s counter readings |
| PornoR | 277 s | 48 | Burst type (92 % of load from challenges) |
| TAPA FULL Middle | 409 s | 45 | Long mid-tempo chart |
| 参考2-Bigmoney | 298 s | **42.4** | per8 measurements |
| TAPA FULL SLOW | 409 s | 33 | |
| Custom1 | 247 s | 28 | |
| Pilot2 | 153 s | 24 | |
| Here | 164 s | 18 | High peaks but never sustained ≥10 s |
| Pilot | 150 s | 14 | |

---

## The model (v0.9)

```
r_th = max(0, 1.0 − 2.0·(E − 0.5))          neutral threshold follows arousal
r ≥ r_th:  dE/dt = +K·[(r−r_th)/(3−r_th)]^1.2
r < r_th:  dE/dt = −2K·0.85^n·(1 − r/r_th)   recovery is independent of E
S = 100·(E_end − 0.5) / 0.5
```

- `K = 0.000736 /s`, calibrated so that **SBT 06 exhausts the margin exactly at 740 s**
- Rates above the sustainable ceiling `4.6 + 3.1·e^(−τ/12)` are **clamped**, never rewarded
- Brake correction: first tier at 10 s of cumulative rest, then one per 20 s

Three properties that matter:

1. **The threshold drops as arousal rises** — at `E = 1` it reaches 0, which is why
   "one more stroke" near the edge is fatal.
2. **Recovery does not depend on how aroused you are** — stopping is a fixed
   physiological process, not something that speeds up when you are close.
3. **Recovery scales with the distance below the threshold** (`1 − r/r_th`), so
   "slightly slower" is not treated the same as "stopped".

A full derivation, including why each parameter has the value it does, is in
[`docs/Difficulty Framework v0.9 (EN).md`](docs/Difficulty%20Framework%20v0.9%20%28EN%29.md).

---

## Help make it more accurate

The model currently rests on **one anchor** (SBT 06 at 12:20) and very few measured
works. Every additional data point makes the rating more trustworthy. Three things
help, in order of value:

### 1. Actual challenge results — the most valuable thing you can give

> "I lasted 3:40 on *Bigmoney*" · "*Rezorecta* — cleared it" · "lost at 6:20 on *PornoR*"

- work name, how long you lasted (or "cleared"), roughly when you tried
- **several people on the same work** is worth far more than many works from one person
- anonymous is fine — no name, no personal detail needed

This is what allows the model to be **validated**. At the moment it has a single
anchor, so nobody can say whether the ordering is actually right. If the scores cannot
predict who fails first, the model is wrong and needs fixing — and that is exactly the
kind of feedback this project needs.

### 2. Segment beat tables

Any work you can measure. Use the format described above; even a coarse table
(30-second segments) is useful, and `per8` improves it further. Tables are merged into
`beatbar_score/data/` so everyone gets the scores.

### 3. Scores that feel wrong

If a score badly mismatches your experience, open an issue and say which work and why.
Outliers are how modelling errors surface — a single counter-example is more useful
than ten agreements.

**How to submit:** open an [issue](../../../issues) (templates are provided) or send a
pull request adding your CSV to `beatbar_score/data/`. Data is used only for
calibration; nothing personal is stored.

## Known limitations

| Item | Note |
|---|---|
| Single anchor | Calibrated from one reference work (SBT 06) |
| `β`, `α`, `ρ` | Definitional or deliberately pessimistic, not fitted |
| Holds (`dur`) | Semantics unclear; currently counted as a single hit |
| Multi-lane / doubles | Treated as one stroke per note |
| Content intensity | Not modelled — a more arousing video is harder, but that is not in the chart |
| Segment granularity | Rhythm changes shorter than the segment size get averaged out |

---

## Layout

```
beatbar_score/
  __main__.py     entry point
  cli.py          command line
  gui.py          tkinter GUI
  model.py        the model (pure functions)
  data.py         loaders
  card.py         score card renderer
  i18n.py         zh / en / ja strings
  data/
    ref1.csv      SBT 06 (58 segments)
    ref2.csv      Bigmoney (32 segments, with per8)
    ref3.csv      Rezorecta (48 counter readings)
build_exe.bat     one-click PyInstaller build
```

## Building the executable

```bat
build_exe.bat
```

Produces `dist\BeatBarScore.exe` (single file, no Python required).

## License

MIT

