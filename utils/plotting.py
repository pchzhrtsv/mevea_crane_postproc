import matplotlib.pyplot as plt
import pandas as pd

def plot_variables(datasets: dict, lightening: int, payload: int, variables: list[str]):

    key = (lightening, payload)

    if key not in datasets:
        raise KeyError(
            f"Dataset {lightening}_{payload} not found"
        )

    df = datasets[key]

    if "Time" not in df.columns:
        raise KeyError("'Time' column not found")

    plt.figure(figsize=(10, 6))

    for variable in variables:

        if variable not in df.columns:
            raise KeyError(f"Variable '{variable}' not found")
        plt.plot(df["Time"], df[variable], label=variable)

    plt.xlabel("Time, s")
    plt.ylabel("Value")

    plt.title(f"Lightening={lightening}% | Payload={payload} kg")

    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.show()

def plot_series(series: pd.DataFrame, keys: list, title: str = "", ylabel: str = "Value", singleshot=False, xrange=None, yrange=None):

    if singleshot: plt.figure(figsize=(16.5, 10.8))


    for seria_key in keys:
        plt.plot(series["Time"], series[seria_key], label=seria_key)

    plt.xlabel("Time, s", fontsize=18)
    plt.ylabel(ylabel, fontsize=18)
    if title:
        plt.title(title, fontsize=18)

    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    if xrange:
        plt.xlim(xrange)
    if yrange:
        plt.ylim(yrange)
    plt.grid(True)
    plt.legend(fontsize=16)
    plt.tight_layout()
    if singleshot: plt.show()

def plot_smthng(df: pd.DataFrame, x: str, y: list, title: str = "", ylabel: str = "Value", xlabel = None, loc_labels = None, styles = None, colors = None, singleshot=False):
    if singleshot: plt.figure(figsize=(16.5, 10.8))
    for i, y_ in enumerate(y):
        if loc_labels:
            lbl = loc_labels[i]
        else:
            lbl = y_
        loc_style = "-" if styles is None else styles[i]
        if colors:
            loc_color = colors[i]
            plt.plot(df[x], df[y_], label=lbl, linestyle=loc_style, color=loc_color)
        else:
            plt.plot(df[x], df[y_], label=lbl, linestyle=loc_style)
    if xlabel is None:
        xlabel = x
    plt.xlabel(xlabel,  fontsize=18)
    plt.ylabel(ylabel,  fontsize=18)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.title(title, fontsize=18)
    plt.grid(True)
    plt.legend(fontsize=16)
    if singleshot: plt.show()
