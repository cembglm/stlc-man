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
    [0.89, 0.57, 0.62, 0.46, 0.55],
    [0.99, 0.46, 0.67, 0.59, 0.70],
    [0.997, 0.68, 0.82, 0.59, 0.76],
    [0.91, 0.51, 0.63, 0.49, 0.65],
    [1.00, 0.54, 0.74, 0.45, 0.63],
    [0.98, 0.30, 0.39, 0.19, 0.33],
    [0.99, 0.59, 0.79, 0.52, 0.63]
]

df = pd.DataFrame(data, index=rows, columns=cols)

# -----------------------------
# Powder gray / powder blue colormap
# Low CD = light, high CD = darker
# -----------------------------
cd_cmap = mcolors.LinearSegmentedColormap.from_list(
    "powder_cd_map",
    [
        "#F4F1F0",  # very light powder gray
        "#D8D3D0",  # powder gray
        "#BFD7EA",  # powder blue
        "#8FAFC6"   # darker powder blue
    ]
)

# -----------------------------
# Plot
# -----------------------------
fig, ax = plt.subplots(figsize=(10, 6.5))

im = ax.imshow(
    df,
    cmap=cd_cmap,
    vmin=0,
    vmax=1,
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
for i in range(df.shape[0]):
    for j in range(df.shape[1]):
        value = df.iloc[i, j]

        text_color = "white" if value >= 0.75 else "black"

        ax.text(
            j,
            i,
            f"{value:.2f}",
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
cbar.set_label("Comparison Density (CD)", fontsize=10)
cbar.ax.tick_params(labelsize=9)

# Titles and labels
ax.set_title(
    "Comparison Density for Serial Optimization Across Source–Optimizer Model Pairs",
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
plt.savefig("cd_serial_optimization_heatmap.png", dpi=300, bbox_inches="tight")
plt.savefig("cd_serial_optimization_heatmap.pdf", bbox_inches="tight")

plt.show()