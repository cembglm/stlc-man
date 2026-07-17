import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# -----------------------------
# Long-form data
# -----------------------------
data = [
    ("LLaMa3.2-3B", "LLaMa3.2-3B", 100.00),
    ("LLaMa3.2-3B", "GPT-OSS-20B", 100.00),
    ("LLaMa3.2-3B", "LLaMa3.3-70B", 100.00),
    ("LLaMa3.2-3B", "Codestral-22B", 100.00),
    ("LLaMa3.2-3B", "Qwen3-Coder-30B", 87.50),

    ("Gemini2.5-Pro", "GPT-OSS-20B", 100.00),
    ("Gemini2.5-Pro", "LLaMa3.3-70B", 100.00),
    ("Gemini2.5-Pro", "Qwen3-Coder-30B", 100.00),
    ("Gemini2.5-Pro", "Codestral-22B", 100.00),
    ("Gemini2.5-Pro", "LLaMa3.2-3B", 100.00),

    ("Gemini2.5-Flash", "LLaMa3.3-70B", 100.00),
    ("Gemini2.5-Flash", "GPT-OSS-20B", 92.86),
    ("Gemini2.5-Flash", "Qwen3-Coder-30B", 100.00),
    ("Gemini2.5-Flash", "Codestral-22B", 100.00),
    ("Gemini2.5-Flash", "LLaMa3.2-3B", 92.86),

    ("GPT-OSS-20B", "LLaMa3.2-3B", 100.00),
    ("GPT-OSS-20B", "GPT-OSS-20B", 91.67),
    ("GPT-OSS-20B", "Qwen3-Coder-30B", 91.67),
    ("GPT-OSS-20B", "Codestral-22B", 100.00),
    ("GPT-OSS-20B", "LLaMa3.3-70B", 100.00),

    ("Qwen3-Coder-30B", "LLaMa3.3-70B", 87.50),
    ("Qwen3-Coder-30B", "GPT-OSS-20B", 100.00),
    ("Qwen3-Coder-30B", "LLaMa3.2-3B", 100.00),
    ("Qwen3-Coder-30B", "Qwen3-Coder-30B", 100.00),
    ("Qwen3-Coder-30B", "Codestral-22B", 100.00),

    ("Codestral-22B", "GPT-OSS-20B", 100.00),
    ("Codestral-22B", "LLaMa3.2-3B", 100.00),
    ("Codestral-22B", "LLaMa3.3-70B", 100.00),
    ("Codestral-22B", "Qwen3-Coder-30B", 100.00),
    ("Codestral-22B", "Codestral-22B", 100.00),

    ("LLaMa3.3-70B", "LLaMa3.2-3B", 100.00),
    ("LLaMa3.3-70B", "GPT-OSS-20B", 100.00),
    ("LLaMa3.3-70B", "Qwen3-Coder-30B", 100.00),
    ("LLaMa3.3-70B", "Codestral-22B", 100.00),
    ("LLaMa3.3-70B", "LLaMa3.3-70B", 100.00),
]

df_long = pd.DataFrame(data, columns=["Source Model", "Optimization Model", "SCP (%)"])

# -----------------------------
# Desired row/column order
# -----------------------------
model_order = [
    "LLaMa3.2-3B",
    "Gemini2.5-Pro",
    "Gemini2.5-Flash",
    "GPT-OSS-20B",
    "LLaMa3.3-70B",
    "Qwen3-Coder-30B",
    "Codestral-22B"
]

optimizer_order = [
    "LLaMa3.2-3B",
    "GPT-OSS-20B",
    "LLaMa3.3-70B",
    "Qwen3-Coder-30B",
    "Codestral-22B"
]

# Pivot to matrix
df = df_long.pivot(index="Source Model", columns="Optimization Model", values="SCP (%)")
df = df.reindex(index=model_order, columns=optimizer_order)

# -----------------------------
# Powder blue / powder gray colormap
# -----------------------------
scp_cmap = mcolors.LinearSegmentedColormap.from_list(
    "powder_scp_map",
    [
        "#D8D3D0",  # powder gray (lower values)
        "#C9D8E6",
        "#BFD7EA",
        "#8FAFC6"   # stronger powder blue (higher values)
    ]
)

# -----------------------------
# Plot
# -----------------------------
fig, ax = plt.subplots(figsize=(9.5, 6.2))

# Narrow range to highlight differences
im = ax.imshow(
    df.values,
    cmap=scp_cmap,
    vmin=85,
    vmax=100,
    aspect="auto"
)

# Axis ticks
ax.set_xticks(np.arange(len(df.columns)))
ax.set_yticks(np.arange(len(df.index)))

ax.set_xticklabels(df.columns, fontsize=10)
ax.set_yticklabels(df.index, fontsize=10)

plt.setp(ax.get_xticklabels(), rotation=35, ha="right", rotation_mode="anchor")

# Cell annotations
for i in range(df.shape[0]):
    for j in range(df.shape[1]):
        value = df.iloc[i, j]
        text_color = "white" if value < 91 else "black"
        ax.text(
            j, i, f"{value:.2f}",
            ha="center", va="center",
            fontsize=9, color=text_color
        )

# White grid lines between cells
ax.set_xticks(np.arange(-0.5, len(df.columns), 1), minor=True)
ax.set_yticks(np.arange(-0.5, len(df.index), 1), minor=True)
ax.grid(which="minor", color="white", linestyle="-", linewidth=1.2)
ax.tick_params(which="minor", bottom=False, left=False)

# Colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label("Scenario Coverage Preservation (SCP %)", fontsize=10)
cbar.ax.tick_params(labelsize=9)

# Title and labels
ax.set_title(
    "Scenario Coverage Preservation Across Source–Optimization Model Pairs",
    fontsize=12,
    fontweight="bold",
    pad=14
)
ax.set_xlabel("Optimization Model", fontsize=11)
ax.set_ylabel("Source Model", fontsize=11)

# Remove frame
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()

# Save
plt.savefig("scp_heatmap.png", dpi=300, bbox_inches="tight")
plt.savefig("scp_heatmap.pdf", bbox_inches="tight")

plt.show()
