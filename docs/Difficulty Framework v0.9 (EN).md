# BeatBar / HMV Difficulty Framework — v0.9

> This is the reference document for the scoring model used by `BeatBarScore`.
> It defines every quantity, gives the value of every parameter and where it came
> from, and lists what is still unverified.

---

## 1. What this measures

**Difficulty = how fast a challenger's margin is drained to zero.**

The model has two state variables — `E` (ejaculatory arousal, 1 = point of no
return) and `r_th` (the neutral stroke rate, above which arousal accumulates and
below which it decays) — plus a counter `n` for brake corrections.

Three sentences summarise it:

1. **Stimulation** (`r ≥ r_th`) raises `E`, super-linearly in the rate.
2. **Recovery** (`r < r_th`) lowers `E` at a rate proportional to `(1 − r/r_th)`
   and **completely independent of `E`**.
3. **The threshold itself falls**: slowly as arousal accumulates, and instantly
   as `E` approaches 1 — which is why one more stroke at the edge is fatal.

---

## 2. Formulas

```
Initial:
    E    = 0.50          (start of the plateau, half the margin spent)
    r_th = 1.40 Hz → replaced by the dynamic form below
    K    = 0.000736 /s   (calibrated, see §4)

Each step dt:
    ① Threshold
        r_th = max(0, 1.0 − 2.0·(E − 0.5))

    ② Accumulation (r ≥ r_th)
        E += K · [ (r − r_th)/(3.0 − r_th) ]^1.2 · dt

    ③ Recovery (r < r_th, only while E < 1)
        E −= 2K · 0.85^n · (1 − r/r_th) · dt
        floor: E ≥ 0.5

    ④ Brake tier n
        a rest episode counts only if it lasts ≥ 1.5 s
        the intro (before the first stimulation) never counts
        cumulative rest < 10 s      → n = 0
        cumulative rest ≥ 10 s      → n = 1 + ⌊(cumulative − 10)/20⌋

    ⑤ Main score
        S = 100 · (E_final − 0.5) / 0.5
```

**Reserved but disabled term**

```
A += α·(E − 0.5)·dt          (α = 0 in this version, so A ≡ 0)
r_th = max(0, 1.4 − A − β·(E − 0.5))
```

`A` is a long-term downward drift of the threshold with a floor `γ`. It is kept as
an interface for very long, low-intensity works (e.g. a 20-minute HMV) and is not
active in v0.9.

### 2.1 Why the threshold must reach zero

With `β = 2.0` and `r_th0 = 1.0`, at `E = 1` we get `1.0 − 2.0 × 0.5 = 0`.
This is not a coincidence to be tuned — it is the minimal expression of the fact
that **the last stroke before the threshold is always the one you cannot stop**.

### 2.2 Why recovery ignores `E`

The relaxation after stopping is a fixed physiological process. It should not speed
up because you happen to be more aroused — earlier versions used a term
proportional to `(E − floor)`, which made recovery *faster* near the threshold,
the opposite of what is reported by actual challengers.

### 2.3 Why recovery is proportional to the distance below the threshold

At `r = 0` the full recovery rate applies; as `r` approaches `r_th` it goes to zero.
This removes the discontinuity of "anything below the threshold is treated as a
complete stop", which used to classify a 1.07 Hz section as rest.

---

## 3. Parameters

| Parameter | Value | Source |
|---|---:|---|
| `E(0)` | 0.50 | Assumption: start of plateau, half the margin spent |
| `r_th0` | 1.00 Hz | A 1.33 Hz HMV can still finish, only slowly → neutral point must be below 1.33 |
| `β` | 2.00 | Makes the threshold reach zero exactly at `E = 1` |
| `q` | 1.20 | Super-linearity of rate → load |
| `r_ref` | 3.00 Hz | Reference rate for normalisation |
| `ρ` | 0.85 | Pessimistic value; see §3.2 |
| `K` | 0.000736 /s | Calibration: SBT 06 exhausts the margin at 740 s |
| `T_ref` | 679 s | Equivalent "seconds you can sustain at 3 Hz" |

### 3.1 The Bustos data (basis for the recovery law)

Bustos et al. 2023 (*Sexual Medicine*, [PMC10136197](https://pmc.ncbi.nlm.nih.gov/articles/PMC10136197/)),
481 men with premature ejaculation, an exercise with at most 5 stops:

| Start | Mean ± SD | Median (IQR) | Stop | Mean ± SD |
|---|---:|---:|---|---:|
| 1 | 92.14 ± 74.70 | 76.0 (31–136) | 1 | 25.37 ± 16.94 |
| 2 | 42.35 ± 35.52 | 31.0 (15–60) | 2 | 25.68 ± 17.60 |
| 3 | 38.16 ± 34.05 | 27.0 (13–53) | 3 | 22.99 ± 17.08 |
| 4 | 29.77 ± 30.91 | 20.0 (7–43) | 4 | 17.37 ± 24.52 |
| 5 | 20.07 ± 30.36 | 8.0 (0–30) | 5 | 9.63 ± 19.56 |
| 6 | 13.71 ± 26.93 | 0 (0–16) | | |

**Correct way to read the recovery**: the margin restored by stop *n* equals the
duration of the *next* start multiplied by the growth rate
`u = 0.5/92.14 = 0.00543/s`:

| Brake | Next start | Margin restored | Share of 0.5 | Stop length | `k_n` | ratio |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 42.35 s | 0.230 | **46 %** | 25.37 | 0.00906 | — |
| 2 | 38.16 | 0.207 | **41 %** | 25.68 | 0.00806 | 0.890 |
| 3 | 29.77 | 0.162 | **32 %** | 22.99 | 0.00703 | 0.872 |
| 4 | 20.07 | 0.109 | **22 %** | 17.37 | 0.00627 | 0.892 |
| 5 | 13.71 | 0.074 | **15 %** | 9.63 | 0.00772 | 1.231 |

Recovery declines smoothly (46 → 41 → 32 → 22 → 15 %), with no cliff.

### 3.2 Choosing ρ

`k_n` uses Start *n+1*, so each ratio depends on which starts are included:

| Ratio | Uses | Dropout rate |
|---|---|---|
| `k₂/k₁ = 0.890` | Start 1, 2, 3 | 0 / 0 / 0 |
| `k₃/k₂ = 0.872` | Start 2, 3, **4** | 0 / 0 / **13.3 %** |
| `k₄/k₃ = 0.892` | Start 3, **4**, **5** | 0 / 13.3 % / **43 %** |
| `k₅/k₄ = 1.231` | Start 4, 5, **6** | 13.3 % / 43 % / **62 %** |

**Only `0.890` is bias-free.** The other two include Start 4, whose reported mean
(29.77 s) is computed only among the 417 men who got that far — i.e. among the
slower ones — so it is **too high**, which inflates `k₃`/`k₄` and pulls the ratios
toward 1, **overestimating ρ**.

`k₅/k₄ = 1.231 > 1` is a separate artefact: the 5th stop was designed as 30 s but
averaged 9.63 s (participants ejaculated during it), a truncation bias.

Therefore: the only unbiased estimate is **ρ = 0.890** (a single ratio, no error
bars), and the true value should be **below** it. **ρ = 0.85** is used as a
pessimistic value. A reasonable interval is **0.80–0.89**.

### 3.3 Relative scaling of the recovery rate

Bustos' stimulation intensity is `u = 0.0054/s` and the recovery rate `k = 0.0085/s`.
SBT 06's average growth is only `0.00074/s`; reusing 0.0085 directly would make
recovery 11× faster than growth, exaggerating the cost of short pauses.

So the recovery rate is scaled **with the stimulation intensity**: `k_1 = 2K`.

---

## 4. Calibration

The anchor is not any person's single run, but **a work plus its rule**:

> SBT 06's rules designate **12:20 (740 s) – 12:52 as the window where ejaculation
> is allowed**. Under the original rule you had to ejaculate inside that window to
> succeed; after the semantics drifted, surviving to the end also counts.
> Either way, **740 s is the endpoint defined by the rules** → the 100-point mark.

```
Solve K such that SBT 06 exhausts the margin exactly at 740 s
→ K = 0.000736 /s,  T_ref = 679 s
```

| Work | S |
|---|---:|
| SBT 06 (full length 835 s) | **113.2** |
| Rezorecta | 58.1 |
| PornoR | 48.3 |
| TAPA FULL Middle | 44.9 |
| Bigmoney | 42.4 |
| TAPA FULL SLOW | 32.9 |

---

## 5. SBT 06 trajectory

| t (s) | 0 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | **740** | 835 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| E | 0.500 | 0.537 | 0.597 | 0.654 | 0.734 | 0.789 | 0.877 | 0.957 | **0.998** | 1.066 |
| r_th | 1.00 | 0.93 | 0.81 | 0.69 | 0.53 | 0.42 | 0.25 | 0.09 | **0.00** | 0.00 |

The threshold reaches zero exactly at 740 s — the moment the rules allow
ejaculation is also the moment the neutral rate drops to zero.

### 5.1 Structure

| Segment | Character |
|---|---|
| 0–15 s | silent intro |
| 15–480 s | mostly 2.0–2.9 Hz, with short 4.2–4.4 Hz bursts |
| 480–720 s | climbs to 3.0–4.3 Hz, one 6 s stretch at 7.5 Hz |
| 726–739 s | 8.69 Hz (clamped to ≈7.6) |
| 741–772 s | 8.26 Hz for 31 s |
| 802–835 s | silent outro |

**Six peak challenges** (≥4 Hz for ≥10 s):
138–151 (13 s, 4.38), 383–399 (16 s, 4.00), 480–495 (15 s, 4.27),
541–555 (14 s, 4.79), 710–739 (29 s, 4.33), **741–772 (31 s, 5.71)**.

Together ≈49 points (43 % of the total 113), with the strongest 3.9× the weakest —
a textbook rising-wave arrangement (`W ≈ 3`).

---

## 6. Outputs

### 6.1 Main score

```
S = 100 × (E_final − 0.5) / 0.5
```

`100` = exactly exhausts the reference margin. No upper bound.

### 6.2 Secondary metrics

| Symbol | Meaning |
|---|---|
| `S_peak` | damage dealt by the hardest 60 s alone |
| `R60` | average rate of the hardest minute |
| `T_hi` | total time at or above `0.85·R60` |
| `N_ch` | number of peak challenges (≥4 Hz, ≥10 s) |
| `W` | escalation ratio = last two challenges ÷ first two |
| `ρ` | `T_fail / T`, whether the work can be cleared |

### 6.3 Tiers

| `S` | Tier |
|---|---|
| < 20 | practice |
| 20–40 | normal |
| 40–60 | hard |
| 60–100 | top tier |
| > 100 | beyond the classic scale |

---

## 7. Challenger performance score

The same person can survive SBT 06 anywhere between 3 minutes and 34 minutes
(2.5 playthroughs). So the work score needs a companion **ruler for the challenger**.

Using SBT 06 as the measuring stick:

| Survived until | `S` | **φ** | Recommended ceiling (`80φ`) |
|---|---:|---:|---:|
| 2:30 | 14.2 | 0.14 | 11 |
| 4:05 | 23.0 | 0.23 | 18 |
| 5:20 | 34.6 | 0.35 | 28 |
| 7:00 | 47.6 | 0.48 | 38 |
| 9:15 | 68.5 | 0.69 | 55 |
| **12:20** | **99.7** | **1.00** | **80** |
| to the end | 113.1 | 1.13 | 90 |

`φ` describes **this session's state**, not a permanent ability. Measuring it
before choosing a work avoids the classic mistake of picking a 25-point work
and failing it anyway.

---

## 8. HMV quick estimate

HMV has a steady rhythm and a lower rate, so a constant-rate approximation works:

```
r̄ = N_beats / T
g  = [ max(0, (r̄ − 1.0)) / 2.0 ]^1.2
S  = 100 × (T / 679) × g
```

| Duration \ r̄ | 1.8 Hz | 2.0 Hz | 2.2 Hz | 2.5 Hz | 3.0 Hz |
|---|---:|---:|---:|---:|---:|
| 3 min | 8.8 | 11.5 | 14.4 | 18.8 | 26.5 |
| 5 min | 14.7 | 19.2 | 23.9 | 31.3 | 44.2 |
| 10 min | 29.4 | 38.4 | 47.9 | 62.6 | 88.4 |
| 20 min | 58.8 | 76.9 | 95.8 | 125.1 | 176.7 |

A typical HMV (4 min, 128 BPM, mostly quarter notes, r̄ ≈ 2.13) lands around **18**.

---

## 9. The three reference works

### 9.1 SBT 06 — 835 s, 2531 beats, 3.03 Hz average

58 segments (from the interval table). See §5.

### 9.2 Bigmoney — 298 s, 862 beats, 2.89 Hz average

32 segments; rates computed from the **beats per 8-beat phrase** column and
rescaled so the integral equals the known 862 beats.

| Metric | Constant approximation | **per8 measurement** |
|---|---:|---:|
| S | 41.5 | **42.4** |
| S_peak | 8.3 | **10.2** |
| R60 | 2.90 | **3.26** |
| T_hi | 298 | **208** |
| N_ch | 0 (artefact) | **1** |

The single challenge is **267–282 s, 15 s, 4.16 Hz average**: Bigmoney is not flat
all the way through; it has one clearly harder stretch before the end.

> One row of the source table had the Beats and per8 columns swapped
> (it read 10.5 / 21; the correct values are **21 beats and per8 = 10.5**).
> After the fix the per8 integral is 874.8 beats against a counted total of 872 (+0.3 %).

### 9.3 Rezorecta — 360 s, 1176 beats, 3.27 Hz average

48 readings from the on-screen counter at 7.5 s intervals. Average per 30 s:

| 0-30 | 30-60 | 60-90 | 90-120 | 120-150 | 150-180 | 180-210 | 210-240 | 240-270 | 270-300 | 300-330 | 330-360 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.83 | 2.57 | 2.63 | 3.07 | 4.07 | 3.23 | 4.43 | 3.50 | 4.30 | 4.90 | 2.67 | 1.83 |

Three escalating challenges (8.4 / 16.5 / 24.2 points, 63 % of the gross load) —
a **burst type**, the opposite of SBT 06's "long grind plus a tail".

---

## 10. All measured works

| Work | T (s) | **S** | S_peak | R60 | T_hi | N_ch |
|---|---:|---:|---:|---:|---:|---:|
| SBT 06 | 835 | **113** | — | 4.91 | 85 | 6 |
| Rezorecta | 360 | **58** | 16.6 | 4.44 | 135 | 3 |
| PornoR | 277 | **48** | 15.6 | 4.24 | 144 | 4 |
| TAPA FULL Middle | 409 | **45** | 9.7 | 3.14 | 153 | 7 |
| Bigmoney | 298 | **42** | 10.2 | 3.26 | 208 | 1 |
| TAPA FULL SLOW | 409 | **33** | 8.6 | 2.93 | 152 | 5 |
| Custom1 | 247 | **28** | 13.2 | 3.80 | 93 | 4 |
| Pilot2 | 153 | **24** | 12.2 | 3.60 | 76 | 4 |
| Here | 164 | **18** | 7.6 | 2.68 | 90 | 0 |
| Pilot | 150 | **14** | 7.2 | 2.63 | 78 | 2 |

**Notes**

- `Middle` (45) sits slightly above `Bigmoney` (42); both are mid-tempo long
  charts, and the ordering depends on `q` and `T_hi` — there is no strong reason
  to prefer one over the other;
- `Here` (18) peaks at 7.0 Hz but **never sustains it for 10 s**, hence `N_ch = 0`;
- `SLOW` (33) is about 3/4 of `Middle` (45), consistent with their naming.

---

## 11. Known issues

| ID | Issue | Status |
|---|---|---|
| K1 | Hold (`dur`) semantics undefined | counted as a single hit, excluded from any special term |
| K2 | Multi-lane / simultaneous notes | counted as one stroke |
| K3 | Content intensity not in the chart | optional channel, off |
| K4 | Self-judged, unobservable | compliance assumed |
| K5 | Text instructions (`DOUBLE` etc.) | lost |
| K6 | `ρ` has survivorship bias | marked pessimistic |
| K7 | Brake tiers (10 / 20 s) | no independent data; based on the observation that few works give 10 s of rest |

---

## 12. Validation

| Check | Result |
|---|---|
| Monotonic: faster / denser / longer | ✅ |
| Low-rate safety (0.8 Hz throughout) | ✅ no accumulation |
| Clamping (8.5 Hz and 7.7 Hz score the same) | ✅ |
| Anchor: SBT 06 at 740 s | ✅ 100 by construction |
| Threshold reaches zero | ✅ exactly at 740 s |
| Ordering: SBT 06 > Rezorecta > PornoR > Middle > Bigmoney | ✅ 113 > 58 > 48 > 45 > 42 |
| Load of 150–245 s | ✅ 8.8 (old model: 2.1) |
| Bigmoney per8 integral vs total | ✅ 874.8 vs 872 (+0.3 %) |

---

## Appendix: quick reference

```
E = 0.5; total_rest = 0; n = 0; started = False
for each dt:
    th = max(0, 1.0 - 2.0*(E - 0.5))
    if th <= 0 or r >= th:
        started = True
        E += K*((r-th)/(3-th))**1.2*dt
    elif started:
        E -= 2K*0.85**n*(1 - r/th)*dt        (0.5 < E < 1)
S = 100*(max(0.5, E) - 0.5)/0.5

# HMV
r_bar = N/T; g = max(0,(r_bar-1.0)/2.0)**1.2; S = 100*(T/679)*g

# challenger
phi = S_ref(t)/100; ceiling = 80*phi
```

## References

1. Masters & Johnson, *Human Sexual Response*, 1966.
   [overview](https://academic.oup.com/book/24366/chapter-abstract/187270085)
2. Bustos PL et al., *Progressive arousal…*, Sex Med 2023;11(2):qfad014.
   [PMC10136197](https://pmc.ncbi.nlm.nih.gov/articles/PMC10136197/)
3. Bancroft & Janssen, dual control model.
   [overview](https://www.sciencedirect.com/science/article/abs/pii/S1230281315000598)
