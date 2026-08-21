import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Data
# -----------------------------
data = {
    "Model": [
        "LLaMa3.2-3B",
        "Gemini2.5-Pro",
        "Gemini2.5-Flash",
        "GPT-OSS-20B",
        "LLaMa3.3-70B",
        "Qwen3-Coder-30B",
        "Codestral-22B"
    ],
    "Total Generated Test Cases": [169, 152, 139, 137, 177, 177, 123]
}

df = pd.DataFrame(data)

# Sort descending
df = df.sort_values("Total Generated Test Cases", ascending=True).reset_index(drop=True)

# -----------------------------
# Powder blue / powder gray palette
# -----------------------------
# Same soft academic style
base_colors = [
    "#D8D3D0",  # powder gray
    "#BFD7EA",  # powder blue
    "#AEB8C2",  # gray-blue
    "#D8D3D0",
    "#BFD7EA",
    "#AEB8C2",
    "#D8D3D0"
]

# Match color count to row count
bar_colors = base_colors[:len(df)]

# -----------------------------
# Plot
# -----------------------------
fig, ax = plt.subplots(figsize=(9, 5.5))

bars = ax.barh(
    df["Model"],
    df["Total Generated Test Cases"],
    color=bar_colors,
    edgecolor="black",
    linewidth=0.6
)

# Value labels
for bar in bars:
    width = bar.get_width()
    ax.text(
        width + 1.5,
        bar.get_y() + bar.get_height() / 2,
        f"{int(width)}",
        va="center",
        fontsize=10
    )

# Labels and title
ax.set_xlabel("Total Generated Test Cases", fontsize=11)
ax.set_ylabel("Model", fontsize=11)
ax.set_title(
    "Total Generated Test Cases by Model",
    fontsize=12,
    fontweight="bold"
)

# Grid and style
ax.grid(axis="x", linestyle="--", alpha=0.35)
ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Add some right margin for labels
ax.set_xlim(0, df["Total Generated Test Cases"].max() * 1.12)

plt.tight_layout()

# Save
plt.savefig("total_generated_test_cases_by_model.png", dpi=300, bbox_inches="tight")
plt.savefig("total_generated_test_cases_by_model.pdf", bbox_inches="tight")

plt.show()