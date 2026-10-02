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
    fig, ax = plt.subplots(figsize=(6, 3.5))
    series.plot(kind="barh" if horizontal else "bar", ax=ax, color="#2E86DE")
    ax.set_title(title)
    plt.tight_layout()
    st.pyplot(fig)

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

t1, t2, t3, t4 = st.tabs(["🎯 Advisor", "✈️ Flights & Budget", "📉 Savings", "📊 Insights"])

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