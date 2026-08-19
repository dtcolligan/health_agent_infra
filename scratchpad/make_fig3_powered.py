#!/usr/bin/env python3
"""Generate fig3_powered (Section 5.1, the within-family powered run).

Two panels, both with the runtime OFF (the only cells where behaviour lives):
  (a) Telling substitutes for enforcing: cell B (told) vs cell D (withheld),
      per family and pooled -> the +24-point headline.
  (b) Capability does not decide it: cell B strong vs weak within each family
      -> the null-to-negative contrast.

Numbers are the ground-truth cell counts from the paired result
(runs/pilot/ladder/2026-07-18T1115Z/paired_result.json), rounded to the
nearest point for display; effects are computed from the unrounded rates,
matching Section 5.1. Enforced cells A and C were 100% safe on all 488 runs
and are not drawn. Style matches fig1_result.pdf: greyscale + hatch
(colour-blind-safe), value labels above bars, cleaned spines.

Writes paper/figures/fig3_powered.pdf and .png.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# --- style, matched to fig1 -------------------------------------------------
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.edgecolor": "#333333",
        "axes.linewidth": 0.8,
        "figure.dpi": 150,
    }
)

DARK = "#333333"   # solid: told (a) / capable (b)
LIGHT = "#d9d9d9"  # hatched: withheld (a) / weak (b)
TEXT = "#111111"
GREY = "#666666"

# --- ground-truth numbers ---------------------------------------------------
# (a) telling effect, runtime off: family-pooled cell B (told) vs cell D (withheld).
#     Percentages are count-pooled across both siblings within a family.
a_families = ["Qwen2.5", "Qwen3", "Llama3.1", "Mistral", "Pooled"]
a_told = [28, 27, 93, 90, 59]        # cell B, told + off
a_withheld = [20, 12, 57, 53, 35]    # cell D, withheld + off
a_delta = [8, 14, 36, 37, 24]        # effect of telling (from unrounded rates)

# (b) capability contrast in cell B (told, off): strong vs weak sibling.
#     Heights use the exact fractional rates; labels are the paper's rounded
#     integers; contrasts are from the unrounded rates (Section 5.1).
b_families = ["Qwen2.5", "Qwen3", "Llama3.1", "Mistral"]
b_strong_exact = [9 / 32, 7 / 32, 28 / 32, 27 / 32]           # capable rate
b_weak_exact = [9 / 32, 10 / 31, 27 / 27, 29 / 30]            # weak rate
b_strong_lab = [28, 22, 88, 84]
b_weak_lab = [28, 32, 100, 97]
b_contrast = [0, -10, -12, -12]  # strong - weak, from unrounded rates

fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.0, 4.4))

# =========================== panel (a) ======================================
x = list(range(len(a_families)))
w = 0.38
barsA1 = axA.bar(
    [i - w / 2 for i in x], a_told, w,
    color=DARK, edgecolor=DARK, label="Told (cell B)",
)
barsA2 = axA.bar(
    [i + w / 2 for i in x], a_withheld, w,
    color=LIGHT, edgecolor=DARK, hatch="///", label="Withheld (cell D)",
)

for bars, vals in ((barsA1, a_told), (barsA2, a_withheld)):
    for bar, v in zip(bars, vals):
        axA.text(bar.get_x() + bar.get_width() / 2, v + 1.5, f"{v}",
                 ha="center", va="bottom", fontsize=8.5, color=TEXT)

# +delta above each family group
for i, d in enumerate(a_delta):
    top = max(a_told[i], a_withheld[i])
    axA.text(i, top + 8.5, f"+{d}", ha="center", va="bottom",
             fontsize=9, color=DARK, fontweight="bold")

# dotted divider separating the four families from the pooled summary
axA.axvline(3.5, color=GREY, linestyle=":", linewidth=1.0)
axA.text(1.5, 108, "by family", ha="center", va="bottom",
         fontsize=9, color=GREY, style="italic")
axA.text(4.0, 108, "pooled", ha="center", va="bottom",
         fontsize=9, color=GREY, style="italic")

axA.set_ylabel("% of runs safe (first action)")
axA.set_title("(a)  Telling substitutes for enforcing", loc="left",
              fontsize=11, fontweight="bold")
axA.set_xticks(x)
axA.set_xticklabels(a_families, fontsize=9)
axA.set_ylim(0, 118)
axA.set_yticks(range(0, 101, 20))
axA.legend(loc="upper left", frameon=False, fontsize=8.5, handlelength=1.6,
           bbox_to_anchor=(0.005, 0.83))

# =========================== panel (b) ======================================
x2 = list(range(len(b_families)))
barsB1 = axB.bar(
    [i - w / 2 for i in x2], [r * 100 for r in b_strong_exact], w,
    color=DARK, edgecolor=DARK, label="Capable (strong)",
)
barsB2 = axB.bar(
    [i + w / 2 for i in x2], [r * 100 for r in b_weak_exact], w,
    color=LIGHT, edgecolor=DARK, hatch="///", label="Weak",
)

for bars, vals, exact in (
    (barsB1, b_strong_lab, b_strong_exact),
    (barsB2, b_weak_lab, b_weak_exact),
):
    for bar, v in zip(bars, vals):
        axB.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                 f"{v}", ha="center", va="bottom", fontsize=8.5, color=TEXT)

# contrast (strong - weak) above each family group
for i, c in enumerate(b_contrast):
    top = max(b_strong_exact[i], b_weak_exact[i]) * 100
    label = "0" if c == 0 else f"−{abs(c)}"
    axB.text(i, top + 8.5, f"Δ {label}", ha="center", va="bottom",
             fontsize=9, color=DARK, fontweight="bold")

axB.set_title("(b)  Capability does not decide it", loc="left",
              fontsize=11, fontweight="bold")
axB.set_xticks(x2)
axB.set_xticklabels(b_families, fontsize=9)
axB.set_ylim(0, 118)
axB.set_yticks(range(0, 101, 20))
axB.legend(loc="upper left", frameon=False, fontsize=8.5, handlelength=1.6,
           bbox_to_anchor=(0.005, 0.99))
axB.text(0.035, 0.70, "cell B: told, runtime off",
         transform=axB.transAxes, ha="left", va="top",
         fontsize=8.5, color=GREY, style="italic")

# --- shared cosmetics -------------------------------------------------------
for ax in (axA, axB):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#e5e5e5", linewidth=0.8)
    ax.tick_params(length=0)

fig.text(
    0.5, 0.01,
    "Runtime off in both panels; the enforced cells A and C were 100% safe on"
    " all 488 runs and are not shown. (a) pools both siblings per family;"
    " (b) splits them. Effects are computed from unrounded rates.",
    ha="center", va="bottom", fontsize=7.5, color=GREY,
)

fig.tight_layout(rect=(0, 0.045, 1, 1))

out_dir = Path(__file__).resolve().parents[1] / "paper" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(out_dir / "fig3_powered.pdf")
fig.savefig(out_dir / "fig3_powered.png", dpi=200)
print("wrote", out_dir / "fig3_powered.pdf")
print("wrote", out_dir / "fig3_powered.png")
