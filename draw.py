import numpy as np
import matplotlib.pyplot as plt

apps = ["Adder", "BV", "QAOA", "RCS", "QFT", "SQRT"]

Duan = [0.061838, 0.071853, 0.06079, 0.483242, 1.0830579999999999, 0.605043]
Trout = [0.037753999999999996, 0.035439, 0.04183, 0.205668, 0.44051399999999996, 0.259271]
PM = [0.07891999999999999, 0.025764, 0.11577399999999999, 0.144489, 0.24185399999999999, 0.22388899999999998]
WXC = [2.967, 0.856, 1.564, 1.704, 24.820, 46.554]

Duan32 = [0.061022, 0.118029, 0.039486, 0.31473, 0.99005, 0.9400379999999999]
Trout32 = [0.037177999999999996, 0.052717, 0.028446, 0.13070199999999998, 0.39257, 0.38101399999999996]
PM32 = [0.07740799999999999, 0.026862999999999998, 0.071502, 0.060009999999999994, 0.14237, 0.20699599999999999]
WXC32 = [3.252, 0.987, 1.357, 0.856, 33.876, 40.817]

ideal_fidelity = [0.57968369259211, 0.9379749638258457, 0.08035822393544446, 0.5710490410244006, 0.017703067576554966, 0.35753774467029337]
aom16_fidelity = [0.5591289704841048, 0.9203036971871787, 0.06765559673329859, 0.042226213767718485, 0.004014820587238055, 0.1068872633335483]
aom32_fidelity = [0.5739071156251596, 0.9323602306932246, 0.0795574502179452, 0.3523683679148921, 0.013020722312027914, 0.3306954628363673]

xticks = np.arange(len(apps))

fig, ax = plt.subplots(figsize=(10, 7))

ax.bar(xticks, ideal_fidelity, width=0.25, label="ideal_fidelity", color="lightcoral", alpha=0.5)

ax.bar(xticks + 0.25, aom16_fidelity, width=0.25, label="aom16_fidelity", color="darkviolet", alpha=0.5)

ax.bar(xticks + 0.5, aom32_fidelity, width=0.25, label="aom32_fidelity", color="grey", alpha=0.5)

plt.yscale('log')
ax.set_title("Success rate on different application", fontsize=15)
ax.set_xlabel("Application", size=16)
ax.set_ylabel("Success rate", size=16)
ax.legend(['ideal_fidelity', 'aom16_fidelity', 'aom32_fidelity'], loc='upper right', prop={'size': 16})

ax.set_xticks(xticks + 0.25)
ax.set_xticklabels(apps, size=13)
ax.tick_params(axis='both', which='major', labelsize=13)
plt.show()