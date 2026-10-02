import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def airline_avg(df):
    return df.groupby("airline")["price"].mean().sort_values()

def time_avg(df):
    return df.groupby("departure_time")["price"].mean().sort_values()

def class_avg(df):
    return df.groupby("class")["price"].mean()

def booking_window(df):
    bins = [0, 3, 7, 15, 30, 50]
    labels = ["0-3", "4-7", "8-15", "16-30", "31-49"]
    d = df.copy()
    d["window"] = pd.cut(d["days_left"], bins=bins, labels=labels)
    return d.groupby("window", observed=True)["price"].mean()

def stats(df):
    p = df["price"].values
    return {"mean": np.mean(p), "median": np.median(p),
            "std": np.std(p), "min": np.min(p), "max": np.max(p)}

def corr_duration_price(df):
    return df["duration"].corr(df["price"])

def show_dashboard(df):
    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    airline_avg(df).plot(kind="barh", ax=ax[0, 0], title="Avg price by airline")
    booking_window(df).plot(kind="bar", ax=ax[0, 1], title="Price vs days before flight")
    time_avg(df).plot(kind="bar", ax=ax[1, 0], title="Price by departure time")
    ax[1, 1].hist(df["price"], bins=40)
    ax[1, 1].set_title("Price distribution")
    plt.tight_layout()
    plt.savefig("dashboard.png")
    plt.show()