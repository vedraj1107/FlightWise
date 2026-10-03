import streamlit as st
import matplotlib.pyplot as plt
from datetime import date, timedelta
from cleaner import load_data
import analysis as an
import advisor as ad

st.set_page_config(page_title="FlightWise", page_icon="✈️", layout="wide")

@st.cache_data
def get_data():
    return load_data()

def bar(series, title, horizontal=False):
    vals = series.values
    cols = ["#8DB9F5"] * len(vals)
    cols[int(vals.argmin())] = "#13A89E"
    cols[int(vals.argmax())] = "#E5484D"
    labels = [str(i).replace("_", " ") for i in series.index]
    fig, ax = plt.subplots(figsize=(4.5, 2.6))
    if horizontal:
        bars = ax.barh(labels, vals, color=cols, height=0.6)
        for b, v in zip(bars, vals):
            ax.text(v, b.get_y() + b.get_height() / 2, f" ₹{v:,.0f}", va="center", fontsize=7)
        ax.set_xticks([])
        ax.set_xlim(0, vals.max() * 1.22)
    else:
        bars = ax.bar(labels, vals, color=cols, width=0.6)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v, f"₹{v:,.0f}", ha="center", va="bottom", fontsize=7)
        ax.set_yticks([])
        ax.set_ylim(0, vals.max() * 1.15)
        plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, labelsize=7)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title(title, fontsize=9, fontweight="bold", loc="left")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=False)
    plt.close(fig)
df = get_data()
cities = sorted(df["source_city"].unique())

st.title("✈️ FlightWise")
st.caption("Flight Price Analyzer & Booking Advisor")

st.sidebar.header("Trip Details")
src = st.sidebar.selectbox("From", cities, index=cities.index("Delhi"))
dst = st.sidebar.selectbox("To", [c for c in cities if c != src])
cls = st.sidebar.radio("Class", ["Economy", "Business"])
travel_date = st.sidebar.date_input(
    "Travel date", date.today() + timedelta(days=20), min_value=date.today())

days_left = (travel_date - date.today()).days
if days_left > 49:
    st.sidebar.warning("Dataset covers up to 49 days ahead. Using 49 days.")
    days_left = 49
days_left = max(days_left, 1)
st.sidebar.info(f"Days until departure: {days_left}")

sub = df[df["class"] == cls]
route_df = sub[(sub["source_city"] == src) & (sub["destination_city"] == dst)]

t1, t2, t3, t4, t5 = st.tabs(["🎯 Advisor", "✈️ Flights & Budget", "📉 Savings", "📊 Insights", "💡 Key Findings"])
with t1:
    res = ad.advise(df, src, dst, cls)
    if res is None:
        st.warning("No data available for this route.")
    else:
        book_on = max(date.today(), travel_date - timedelta(days=res["best_days_left"]))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Flights found", res["flights_found"])
        c2.metric("Lowest fare airline", res["lowest_fare_airline"])
        c3.metric("Cheapest on average", res["cheapest_on_average"])
        c4.metric("Best departure time", res["best_time"].replace("_", " "))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Book on", book_on.strftime("%d %b %Y"))
        c2.metric("Min price", f"₹{res['min_price']}")
        c3.metric("Avg price", f"₹{res['avg_price']}")
        c4.metric("Max price", f"₹{res['max_price']}")
        st.subheader("Stops vs price")
        bar(ad.stops_vs_price(df, src, dst, cls), "Avg price by stops")
        st.subheader("Price trend for this route")
        st.line_chart(route_df.groupby("days_left")["price"].mean())
with t2:
    st.write(f"{src} → {dst} | {travel_date.strftime('%d %b %Y')}")
    day_df = route_df[route_df["days_left"] == days_left]
    if day_df.empty:
        st.warning("No data available for this date.")
    else:
        c1, c2, c3 = st.columns(3)
        lo, hi = int(day_df["price"].min()), int(day_df["price"].max())
        budget = c1.slider("Max budget (₹)", lo, hi, hi, step=100)
        airlines = sorted(day_df["airline"].unique())
        pick = c2.multiselect("Airlines", airlines, default=airlines)
        order = c3.selectbox("Sort by price", ["Low to high", "High to low"])

        r = day_df[(day_df["price"] <= budget) & (day_df["airline"].isin(pick))]
        r = r.sort_values("price", ascending=(order == "Low to high")).head(15)
        r = r[["airline", "departure_time", "arrival_time", "stops", "duration", "price"]]
        r = r.reset_index(drop=True)
        r.index = r.index + 1
        if r.empty:
            st.warning("No flights match these filters.")
        else:
            st.dataframe(r, use_container_width=True)
            st.download_button("Download results (CSV)", r.to_csv().encode(), "flights.csv", "text/csv")
with t3:
    s = ad.savings(df, src, dst, days_left, cls)
    if s is None:
        st.warning("No data available for this selection.")
    else:
        st.write(f"Booking now ({days_left} days before departure) vs booking 30+ days in advance:")
        c1, c2, c3 = st.columns(3)
        c1.metric("Price now", f"₹{s['avg_price_now']}")
        c2.metric("If booked 30+ days before", f"₹{s['avg_price_if_booked_30+_days_before']}")
        c3.metric("You save", f"₹{s['you_save']}", f"{s['saving_percent']}%")

with t4:
    c1, c2 = st.columns(2)
    with c1:
        bar(an.airline_avg(sub), "Avg price by airline", horizontal=True)
        bar(an.time_avg(sub), "Avg price by departure time")
    with c2:
        bar(an.booking_window(sub), "Price vs days before flight")
        bar(ad.cheapest_destinations(df, src, cls), f"Cheapest destinations from {src}")
        
with t5:
    eco = df[df["class"] == "Economy"]
    bus = df[df["class"] == "Business"]
    st.subheader("Key findings from 297,940 fares")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Economy avg ({len(eco)/len(df)*100:.0f}% of flights)", f"₹{eco['price'].mean():,.0f}")
    c2.metric(f"Business avg ({len(bus)/len(df)*100:.0f}% of flights)", f"₹{bus['price'].mean():,.0f}")
    c3.metric("Business vs Economy", f"{bus['price'].mean()/eco['price'].mean():.1f}x")
    c4.metric("Days left vs price (corr)", f"{eco['days_left'].corr(eco['price']):.2f}")

    st.markdown("**1. Class is the main price driver.** Always compare Economy and Business separately.")
    early = eco[eco["days_left"] >= 21]["price"].mean()
    late = eco[eco["days_left"] <= 2]["price"].mean()
    st.markdown(f"**2. Book early.** Economy costs about ₹{late:,.0f} when booked 1-2 days ahead versus about ₹{early:,.0f} when booked 21+ days ahead ({late/early:.1f}x).")
    p15 = eco[eco["days_left"] == 15]["price"].mean()
    p20 = eco[eco["days_left"] == 20]["price"].mean()
    st.markdown(f"**3. Practical deadline.** Fares drop from about ₹{p15:,.0f} at 15 days left to about ₹{p20:,.0f} at 20 days left.")

    st.markdown("**4. Stops raise the fare (Economy).**")
    stops = eco.groupby("stops")["price"].mean().round(0)
    stops.index = ["Non-stop", "1 stop", "2+ stops"]
    bar(stops, "Economy avg fare by stops")

    st.markdown("**5. Airlines (Economy, cheapest to costliest).**")
    bar(an.airline_avg(eco), "Economy avg fare by airline", horizontal=True)

    d = df["duration"].corr(df["price"])
    st.markdown(f"**6. Duration has a weak effect.** Correlation with price is {d:.2f}; stops and booking time matter far more.")
