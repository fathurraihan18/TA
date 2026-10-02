"""Tekstur tampilan layar TFT (ilustrasi ECG + PPG) untuk render."""
import numpy as np, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
out = sys.argv[1]
fig = plt.figure(figsize=(9.6, 6.4), dpi=100, facecolor="#050a14")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 480); ax.set_ylim(0, 320); ax.axis("off"); ax.set_facecolor("#050a14")
# grid
for x in range(0, 481, 24): ax.plot([x, x], [0, 250], lw=0.4, color="#12304a")
for y in range(0, 251, 24): ax.plot([0, 480], [y, y], lw=0.4, color="#12304a")
def beat(t):
    g = lambda m, s, a: a * np.exp(-((t - m) ** 2) / (2 * s ** 2))
    return g(.18, .035, .12) - g(.29, .012, .15) + g(.31, .011, 1.0) - g(.335, .014, .25) + g(.52, .06, .22)
t = np.linspace(0, 4, 1600); y = beat(t % 1)
ax.plot(t / 4 * 470 + 5, 195 + y * 42, lw=1.8, color="#39ff6a")
ppg = 0.5 * (1 - np.cos(2 * np.pi * t)) ** 1.4 * 0.5 + 0.18 * np.exp(-((t % 1 - .55) ** 2) / .01)
ax.plot(t / 4 * 470 + 5, 70 + ppg * 55, lw=1.8, color="#ff5a5a")
ax.text(8, 238, "ECG", color="#39ff6a", fontsize=12, fontweight="bold"); ax.text(8, 112, "PPG", color="#ff5a5a", fontsize=12, fontweight="bold")
ax.add_patch(plt.Rectangle((0, 250), 480, 70, color="#0b1626"))
ax.text(12, 288, "ECG-PPG Monitor", color="white", fontsize=17, fontweight="bold", va="center")
ax.text(300, 290, "78", color="#39ff6a", fontsize=30, fontweight="bold", va="center"); ax.text(352, 280, "bpm", color="#39ff6a", fontsize=12, va="center")
ax.text(410, 296, "SpO2", color="#6ab7ff", fontsize=9); ax.text(412, 276, "97%", color="#6ab7ff", fontsize=14, fontweight="bold")
ax.text(12, 12, "LightGBM: NORMAL", color="#ffd34d", fontsize=13, fontweight="bold")
ax.text(470, 12, "Bat 82%", color="#9be37c", fontsize=10, ha="right")
fig.savefig(out, dpi=100, facecolor=fig.get_facecolor())
