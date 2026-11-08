import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.paths import CSV_DIR

# ---------------------------------------------------------
# 1. Чтение данных
# ---------------------------------------------------------

file_path = CSV_DIR / "consumption_on_lightweight_35bar.csv"
df = pd.read_csv(file_path)

# Столбец с процентом облегчения
lightening = df["Lightening, %"].to_numpy()

# Все остальные столбцы соответствуют нагрузкам
load_columns = [col for col in df.columns if col != "Lightening, %"]

# Из названий вида "10 kg ; 35 bar" получаем только число 10
loads = np.array([
    float(col.split("kg")[0].strip())
    for col in load_columns
])

# Матрица значений:
# строки    -> Lightening, %
# столбцы  -> Load, kg
Z = df[load_columns].to_numpy()


# ---------------------------------------------------------
# 2. Создание координат столбиков
# ---------------------------------------------------------

X, Y = np.meshgrid(loads, lightening)

x = X.ravel()
y = Y.ravel()
z = np.zeros_like(x)

dz = Z.ravel()


# ---------------------------------------------------------
# 3. Размер столбиков
# ---------------------------------------------------------

# Ширина по нагрузке
dx = 7.0

# Ширина по проценту облегчения
dy = 0.7


# ---------------------------------------------------------
# 4. Построение
# ---------------------------------------------------------

fig = plt.figure(figsize=(16, 10))
ax = fig.add_subplot(111, projection="3d")

ax.bar3d(
    x - dx / 2,
    y - dy / 2,
    z,
    dx,
    dy,
    dz,
    shade=True,
    edgecolor="black",
    linewidth=0.6
)


# ---------------------------------------------------------
# 5. Оформление
# ---------------------------------------------------------

ax.set_xlabel("Load, kg", labelpad=12)
ax.set_ylabel("Lightening, %", labelpad=12)
ax.set_zlabel("Consumption change, %", labelpad=12)

ax.set_title(
    "Consumption change vs. load and lightening\nPressure = 35 bar",
    pad=20
)

# Немного более удобный угол обзора
ax.view_init(elev=25, azim=-135)

plt.tight_layout()
plt.show()
