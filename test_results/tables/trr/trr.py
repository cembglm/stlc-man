import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# -----------------------------
# Data
# -----------------------------
rows = [
    "LLaMa3.2-3B\n(T=169)",
    "Gemini2.5-Pro\n(T=152)",
    "Gemini2.5-Flash\n(T=139)",
    "GPT-OSS-20B\n(T=137)",
    "LLaMa3.3-70B\n(T=177)",
    "Qwen3-Coder-30B\n(T=177)",
    "Codestral-22B\n(T=123)"
]

cols = [
    "LLaMa3.2-3B",
    "GPT-OSS-20B",
    "LLaMa3.3-70B",
    "Qwen3-Coder-30B",
    "Codestral-22B"
]

data = [
    [0.0828, 0.3846, 0.3787, 0.5325, 0.4313],
    [0.0197, 0.4408, 0.2565, 0.4210, 0.2697],
    [0.0071, 0.3381, 0.1727, 0.4173, 0.2237],
    [0.0511, 0.4160, 0.2846, 0.5182, 0.3577],
    [0.0000, 0.3333, 0.2259, 0.4068, 0.3051],
    [0.0282, 0.5870, 0.4971, 0.6836, 0.5531],
    [0.0081, 0.3333, 0.2276, 0.4390, 0.3008]
]

df = pd.DataFrame(data, index=rows, columns=cols)

# Convert to percentage for display
df_percent = df * 100

# -----------------------------
# Powder gray / powder blue colormap
# -----------------------------
powder_cmap = mcolors.LinearSegmentedColormap.from_list(
    "powder_blue_gray",
    [
        "#F2F0EF",  # very light powder gray
        "#D8D3D0",  # powder gray
        "#BFD7EA",  # powder blue
        "#8FAFC6"   # stronger powder blue for high values
    ]
)

# -----------------------------
# Plot
# -----------------------------
fig, ax = plt.subplots(figsize=(10, 6.5))

im = ax.imshow(
    df_percent,
    cmap=powder_cmap,
    vmin=0,
    vmax=70,
    aspect="auto"
)

# Axis labels
ax.set_xticks(np.arange(len(cols)))
ax.set_yticks(np.arange(len(rows)))

ax.set_xticklabels(cols, fontsize=10)
ax.set_yticklabels(rows, fontsize=10)

plt.setp(
    ax.get_xticklabels(),
    rotation=35,
    ha="right",
    rotation_mode="anchor"
)

# Annotate each cell
for i in range(df_percent.shape[0]):
    for j in range(df_percent.shape[1]):
        value = df_percent.iloc[i, j]

        # Use darker text for light cells, white text for high-value cells
        text_color = "white" if value >= 50 else "black"

        ax.text(
            j,
            i,
            f"{value:.1f}%",
            ha="center",
            va="center",
            fontsize=9,
            color=text_color
        )

# Grid lines between cells
ax.set_xticks(np.arange(-0.5, len(cols), 1), minor=True)
ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
ax.grid(which="minor", color="white", linestyle="-", linewidth=1.2)
ax.tick_params(which="minor", bottom=False, left=False)

# Colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label("Test Redundancy Ratio, TRR (%)", fontsize=10)
cbar.ax.tick_params(labelsize=9)

# Titles and labels
ax.set_title(
    "TRR Results for Serial Optimization Across Source–Optimizer Model Pairs",
    fontsize=12,
    fontweight="bold",
    pad=14
)

ax.set_xlabel("Optimizer Model", fontsize=11)
ax.set_ylabel("Source Model", fontsize=11)

# Style cleanup
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()

# Save
plt.savefig("trr_serial_optimization_heatmap.png", dpi=300, bbox_inches="tight")
plt.savefig("trr_serial_optimization_heatmap.pdf", bbox_inches="tight")

plt.show()