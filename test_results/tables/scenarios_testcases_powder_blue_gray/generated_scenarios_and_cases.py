import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# -----------------------------
# Data
# -----------------------------
data = {
    "Model": [
        "Qwen-2.5-1M (XML)",
        "LLaMa3.3-70B (Req)",
        "LLaMa3.3-70B (Code)",
        "Codestral-22B (Code)",
        "Codestral-22B (Req)",
        "Qwen3-Coder-30B (Req)",
        "Qwen3-Coder-30B (Code)",
        "Gemini2.5-Flash (Req)",
        "Gemini2.5-Flash (Code)",
        "Gemini2.5-Pro (Code)",
        "Gemini2.5-Pro (Req)",
        "GPT-OSS-20B (Req)",
        "GPT-OSS-20B (Code)",
        "LLaMa3.2-3B (Req)",
        "LLaMa3.2-3B (Code)"
    ],
    "Scenarios": [7, 8, 8, 5, 5, 8, 8, 7, 7, 7, 7, 6, 5, 8, 7],
    "Test Cases": [49, 64, 64, 38, 36, 64, 64, 55, 35, 50, 53, 48, 40, 64, 56]
}

df = pd.DataFrame(data)

# -----------------------------
# Extract source type
# -----------------------------
def extract_source(label):
    if "(XML)" in label:
        return "XML"
    elif "(Req)" in label:
        return "Req"
    elif "(Code)" in label:
        return "Code"
    return "Other"

df["Source"] = df["Model"].apply(extract_source)

# Sıralama
df = df.sort_values(by=["Test Cases", "Scenarios"], ascending=[True, True]).reset_index(drop=True)

# -----------------------------
# Powder palette
# -----------------------------
source_colors = {
    "XML": "#D8D3D0",   # pudra gri
    "Req": "#BFD7EA",   # pudra mavi
    "Code": "#AEB8C2"   # gri-mavi / koyu pudra ton
}

bar_colors = [source_colors[s] for s in df["Source"]]

# -----------------------------
# Plot
# -----------------------------
fig, (ax1, ax2) = plt.subplots(
    ncols=2,
    figsize=(12, 8),
    sharey=True
)

y = range(len(df))

# Left panel: Scenarios
ax1.barh(
    y, df["Scenarios"],
    color=bar_colors,
    edgecolor="black",
    linewidth=0.6
)
ax1.set_xlabel("Number of Scenarios", fontsize=11)
ax1.set_title("Scenarios", fontsize=12, fontweight="bold")
ax1.set_yticks(y)
ax1.set_yticklabels(df["Model"], fontsize=9)
ax1.grid(axis="x", linestyle="--", alpha=0.35)
ax1.set_axisbelow(True)

for i, v in enumerate(df["Scenarios"]):
    ax1.text(v + 0.08, i, str(v), va="center", fontsize=9)

# Right panel: Test Cases
ax2.barh(
    y, df["Test Cases"],
    color=bar_colors,
    edgecolor="black",
    linewidth=0.6
)
ax2.set_xlabel("Number of Test Cases", fontsize=11)
ax2.set_title("Test Cases", fontsize=12, fontweight="bold")
ax2.grid(axis="x", linestyle="--", alpha=0.35)
ax2.set_axisbelow(True)

for i, v in enumerate(df["Test Cases"]):
    ax2.text(v + 0.4, i, str(v), va="center", fontsize=9)

# Style cleanup
for ax in (ax1, ax2):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# Legend
legend_handles = [
    Patch(facecolor=source_colors["XML"], edgecolor="black", label="XML"),
    Patch(facecolor=source_colors["Req"], edgecolor="black", label="Requirement (Req)"),
    Patch(facecolor=source_colors["Code"], edgecolor="black", label="Code")
]

fig.legend(
    handles=legend_handles,
    loc="lower center",
    ncol=3,
    frameon=False,
    fontsize=10,
    bbox_to_anchor=(0.5, -0.01)
)

fig.suptitle(
    "Generated Scenarios and Test Cases Across Model–Artefact Combinations",
    fontsize=13,
    fontweight="bold"
)

plt.tight_layout(rect=[0, 0.03, 1, 0.96])

# Save
plt.savefig("scenarios_testcases_powder_blue_gray.png", dpi=300, bbox_inches="tight")
plt.savefig("scenarios_testcases_powder_blue_gray.pdf", bbox_inches="tight")

plt.show()