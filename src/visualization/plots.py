import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def plot_smile(log_m, vols, maturity):
    plt.figure(figsize=(8, 5))
    plt.plot(log_m, vols, marker="o")
    plt.title(f"AAPL Volatility Skew (T={maturity:.2f}y)")
    plt.xlabel("Log-Moneyness")
    plt.ylabel("Implied Vol")
    plt.grid(True)
    plt.show()

def plot_vol_surface(K, T, IV):
    """
    Plot 3D implied volatility surface
    """
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    surf = ax.plot_surface(
        K,
        T,
        IV,
        cmap="viridis",
        linewidth=0,
        antialiased=True,
        alpha=0.95
    )

    ax.set_xlabel("Strike")
    ax.set_ylabel("Time to Maturity (years)")
    ax.set_zlabel("Implied Volatility")

    fig.colorbar(surf, shrink=0.6, aspect=12)
    plt.title("Implied Volatility Surface")
    plt.tight_layout()
    plt.show()

