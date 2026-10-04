# FlightWise web app (Streamlit + Pandas + NumPy)
# Flow: Step 1 route -> Step 2 date and class -> Step 3 results
# Run with: python -m streamlit run app.py
import streamlit as st
from datetime import date, timedelta
from cleaner import load_data      # loads and cleans the dataset
import analysis as an              # group-by summaries
import advisor as ad               # route advice and savings

st.set_page_config(page_title="FlightWise", page_icon="✈️", layout="wide")

# ---------- CSS: only changes the look ----------
st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
.hero {background: linear-gradient(135deg, #0B2545, #1F6FEB); padding: 20px 28px;
       border-radius: 14px; margin-bottom: 14px;}
.hero h1 {margin: 0; color: white; font-size: 2rem;}
.hero p {margin: 4px 0 0; color: #DCE8FB;}
div[data-testid="stMetric"] {background: rgba(31,111,235,0.08);
       border: 1px solid rgba(31,111,235,0.25); border-radius: 12px; padding: 12px 16px;}
div[data-testid="stMetricValue"] > div {white-space: normal;}
</style>
""", unsafe_allow_html=True)

# ---------- Data ----------
@st.cache_data                      # load the 3 lakh rows only once
def get_data():
    return load_data()

df = get_data()
cities = sorted(df["source_city"].unique())

def nice(text):
    return str(text).replace("_", " ")          # Air_India -> Air India

def chart(series, title):
    st.write(f"**{title}**")
    st.bar_chart(series.rename(index=nice), sort=False)

# ---------- Remember the user's choices between clicks ----------
ss = st.session_state
pages = ["🎯 Advisor", "✈️ Flights & Budget", "📊 Insights"]
ss.setdefault("step", 1)
ss.setdefault("src", None)
ss.setdefault("dst", None)
ss.setdefault("travel_date", None)
ss.setdefault("cls", "Economy")
ss.setdefault("page", pages[0])

# Dataset covers flights 1 to 49 days ahead, so only these dates are allowed
MIN_DATE = date.today() + timedelta(days=1)
MAX_DATE = date.today() + timedelta(days=49)
if ss.travel_date is not None and not (MIN_DATE <= ss.travel_date <= MAX_DATE):
    ss.travel_date = None
    ss.step = min(ss.step, 2)

def summary_row(text, target_step):
    """Shows an earlier choice with a button to go back and change it."""
    a, b = st.columns([6, 1])
    a.markdown(f"**{text}**")
    if b.button("✏️ Change", key=f"change{target_step}"):
        ss.step = target_step
        st.rerun()

# ---------- Header ----------
st.markdown('<div class="hero"><h1>✈️ FlightWise</h1>'
            '<p>Flight Price Analyzer &amp; Booking Advisor</p></div>', unsafe_allow_html=True)
st.progress(ss.step / 3)
st.caption(f"Step {ss.step} of 3")

# ================= Step 1: route =================
if ss.step == 1:
    st.markdown("### Step 1: Where are you flying?")
    a, b = st.columns(2)
    s = a.selectbox("From", cities, index=cities.index(ss.src) if ss.src in cities else None,
                    placeholder="Select city")
    options = [c for c in cities if c != s]
    d = b.selectbox("To", options, index=options.index(ss.dst) if ss.dst in options else None,
                    placeholder="Select city")
    if st.button("Next: choose date →", type="primary", disabled=(s is None or d is None)):
        ss.src, ss.dst, ss.step = s, d, 2
        st.rerun()
    st.stop()

# ================= Step 2: date and class =================
if ss.step == 2:
    summary_row(f"📍 {ss.src} → {ss.dst}", 1)
    st.markdown("### Step 2: When and which class?")
    a, b = st.columns(2)
    d = a.date_input("Travel date", value=ss.travel_date, min_value=MIN_DATE, max_value=MAX_DATE,
                     help="Dataset covers flights up to 49 days ahead.")
    c = b.radio("Class", ["Economy", "Business"],
                index=["Economy", "Business"].index(ss.cls), horizontal=True)
    if st.button("Next: see results →", type="primary", disabled=(d is None)):
        ss.travel_date, ss.cls, ss.step = d, c, 3
        st.rerun()
    st.stop()

# ================= Step 3: results =================
src, dst, cls, travel_date = ss.src, ss.dst, ss.cls, ss.travel_date
summary_row(f"📍 {src} → {dst}", 1)
summary_row(f"📅 {travel_date.strftime('%d %b %Y')}   |   💺 {cls}", 2)

# The dataset has only "days left", so convert the chosen date into days left
days_left = (travel_date - date.today()).days
st.caption(f"⏳ {days_left} days left for departure")

# Data for the chosen class and route
sub = df[df["class"] == cls]
route_df = sub[(sub["source_city"] == src) & (sub["destination_city"] == dst)]

st.markdown("### Step 3: What do you want to see?")
cols = st.columns(3)
for col, name in zip(cols, pages):
    if col.button(name, type="primary" if ss.page == name else "secondary", use_container_width=True):
        ss.page = name
        st.rerun()
st.divider()

# ----- Page 1: Advisor -----
if ss.page == pages[0]:
    res = ad.advise(df, src, dst, cls)
    if res is None:
        st.warning("No data available for this route.")
    else:
        # best booking date = travel date minus the best "days left" found in data
        book_on = max(date.today(), travel_date - timedelta(days=res["best_days_left"]))
        st.success(f"**Tip:** On {src} → {dst}, {nice(res['cheapest_on_average'])} is cheapest on average. "
                   f"Fly {nice(res['best_time']).lower()} and book around {book_on.strftime('%d %b %Y')}.")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Flights found", f"{res['flights_found']:,}")
        m2.metric("Lowest fare airline", nice(res["lowest_fare_airline"]))
        m3.metric("Cheapest on average", nice(res["cheapest_on_average"]))
        m4.metric("Best departure time", nice(res["best_time"]))
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Book on", book_on.strftime("%d %b"))
        m2.metric("Min price", f"₹{res['min_price']:,}")
        m3.metric("Avg price", f"₹{res['avg_price']:,}")
        m4.metric("Max price", f"₹{res['max_price']:,}")
        left, right = st.columns(2)
        with left:
            stops = ad.stops_vs_price(df, src, dst, cls)
            chart(stops.rename(index={0: "Non-stop", 1: "1 stop", 2: "2+ stops"}), "Avg price by stops")
        with right:
            st.write("**Price trend (days left)**")
            st.line_chart(route_df.groupby("days_left")["price"].mean())

# ----- Page 2: Flights & Budget (with savings) -----
elif ss.page == pages[1]:
    sv = ad.savings(df, src, dst, days_left, cls)       # book now vs 30+ days ahead
    st.subheader("Book now or wait?")
    if sv is None:
        st.info("Savings comparison not available for this selection.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Price now ({days_left} days left)", f"₹{sv['avg_price_now']:,}")
        m2.metric("If booked 30+ days before", f"₹{sv['avg_price_if_booked_30+_days_before']:,}")
        m3.metric("You save", f"₹{sv['you_save']:,}", f"{sv['saving_percent']}%")

    st.subheader("Available flights")
    day_df = route_df[route_df["days_left"] == days_left]
    if day_df.empty:
        st.warning("No flights found for this date.")
    else:
        f1, f2, f3 = st.columns(3)
        low, high = int(day_df["price"].min()), int(day_df["price"].max())
        budget = f1.slider("Max budget (₹)", low, max(high, low + 1), max(high, low + 1), step=100)
        airlines = sorted(day_df["airline"].unique())
        pick = f2.multiselect("Airlines", airlines, default=airlines, format_func=nice)
        order = f3.selectbox("Sort by price", ["Low to high", "High to low"])

        r = day_df[(day_df["price"] <= budget) & (day_df["airline"].isin(pick))]
        r = r.sort_values("price", ascending=(order == "Low to high")).head(15)
        r = r[["airline", "departure_time", "arrival_time", "stops", "duration", "price"]].copy()
        for c in ["airline", "departure_time", "arrival_time"]:
            r[c] = r[c].str.replace("_", " ")
        r.columns = ["Airline", "Departure", "Arrival", "Stops", "Duration (h)", "Price (₹)"]
        r.index = range(1, len(r) + 1)
        if r.empty:
            st.warning("No flights match these filters.")
        else:
            st.caption(f"Showing {len(r)} flights")
            st.dataframe(r, use_container_width=True)

# ----- Page 3: Insights (charts + key findings) -----
else:
    st.subheader(f"{cls} fares")
    left, right = st.columns(2)
    with left:
        chart(an.airline_avg(sub), "Avg price by airline")
        chart(an.time_avg(sub), "Avg price by departure time")
    with right:
        chart(an.booking_window(sub), "Avg price by days before flight")
        chart(ad.cheapest_destinations(df, src, cls), f"Cheapest destinations from {src}")

    # Key findings: every number is calculated from the data
    st.subheader(f"Key findings from {len(df):,} fares")
    eco = df[df["class"] == "Economy"]
    bus = df[df["class"] == "Business"]
    early = eco[eco["days_left"] >= 21]["price"].mean()
    late = eco[eco["days_left"] <= 2]["price"].mean()
    p15 = eco[eco["days_left"] == 15]["price"].mean()
    p20 = eco[eco["days_left"] == 20]["price"].mean()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Economy avg", f"₹{eco['price'].mean():,.0f}")
    k2.metric("Business avg", f"₹{bus['price'].mean():,.0f}")
    k3.metric("Business vs Economy", f"{bus['price'].mean() / eco['price'].mean():.1f}x")
    k4.metric("Days left vs price (corr)", f"{eco['days_left'].corr(eco['price']):.2f}")

    st.write("1. Class is the main price driver, so compare Economy and Business separately.")
    st.write(f"2. Book early: Economy costs about ₹{late:,.0f} at 1-2 days ahead vs ₹{early:,.0f} at 21+ days ahead.")
    st.write(f"3. Practical deadline: fares fall from about ₹{p15:,.0f} at 15 days left to ₹{p20:,.0f} at 20 days left.")
    st.write("4. More stops means a higher fare.")
    st.write(f"5. Flight duration has a weak effect (correlation {df['duration'].corr(df['price']):.2f}).")
    stops = eco.groupby("stops")["price"].mean()
    chart(stops.rename(index={0: "Non-stop", 1: "1 stop", 2: "2+ stops"}), "Economy avg price by stops")
