import numpy as np

def _route(df, src, dst, cls):
    return df[(df["source_city"].str.lower() == src.lower()) &
              (df["destination_city"].str.lower() == dst.lower()) &
              (df["class"].str.lower() == cls.lower())]

def advise(df, src, dst, cls="Economy"):
    r = _route(df, src, dst, cls)
    if r.empty:
        return None
    low = r.loc[r["price"].idxmin()]
    return {
        "flights_found": len(r),
        "lowest_fare_airline": low["airline"],
        "cheapest_on_average": r.groupby("airline")["price"].mean().idxmin(),
        "best_time": r.groupby("departure_time")["price"].mean().idxmin(),
        "best_days_left": int(r.groupby("days_left")["price"].mean().idxmin()),
        "min_price": int(np.min(r["price"])),
        "avg_price": int(np.mean(r["price"])),
        "max_price": int(np.max(r["price"])),
    }

def recommend(df, src, dst, budget, cls="Economy", top=5):
    r = _route(df, src, dst, cls)
    r = r[r["price"] <= budget]
    return r.sort_values("price").head(top)[
        ["airline", "departure_time", "stops", "duration", "days_left", "price"]]

def cheapest_destinations(df, src, cls="Economy", top=5):
    r = df[(df["source_city"].str.lower() == src.lower()) &
           (df["class"].str.lower() == cls.lower())]
    return r.groupby("destination_city")["price"].mean().sort_values().head(top).round(0)

def stops_vs_price(df, src, dst, cls="Economy"):
    r = _route(df, src, dst, cls)
    return r.groupby("stops")["price"].mean().round(0)

def savings(df, src, dst, days_left, cls="Economy"):
    r = _route(df, src, dst, cls)
    now = r[r["days_left"] == days_left]["price"]
    early = r[r["days_left"] >= 30]["price"]
    if now.empty or early.empty:
        return None
    a, b = np.mean(now), np.mean(early)
    return {
        "avg_price_now": int(a),
        "avg_price_if_booked_30+_days_before": int(b),
        "you_save": int(a - b),
        "saving_percent": round((a - b) / a * 100, 1),
    }