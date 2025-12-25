import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def plot_smile(log_m, vols, maturity):
    plt.figure(figsize=(8, 5))
    plt.plot(log_m, vols, marker="o")
    plt.title(f"Volatility Smile (T={maturity:.2f}y)")
    plt.xlabel("Log-Moneyness")
    plt.ylabel("Implied Vol")
    plt.grid(True)
    plt.show()


def plot_surface(K, T, IV):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(K, T, IV, cmap="viridis")
    ax.set_xlabel("Strike")
    ax.set_ylabel("Maturity")
    ax.set_zlabel("Implied Vol")
    plt.show()
