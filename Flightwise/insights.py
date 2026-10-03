from cleaner import load_data
df = load_data()
eco = df[df["class"] == "Economy"]
bus = df[df["class"] == "Business"]

print("Class share %:\n", (df["class"].value_counts(normalize=True) * 100).round(1))
print("Avg price by class:\n", df.groupby("class")["price"].mean().round(0))
print("Eco corr days_left vs price:", round(eco["days_left"].corr(eco["price"]), 2))
print("Eco price at days 1-2:", round(eco[eco["days_left"] <= 2]["price"].mean()))
print("Eco price at 21+ days:", round(eco[eco["days_left"] >= 21]["price"].mean()))
print("Eco price at 15 vs 20 days:", round(eco[eco["days_left"] == 15]["price"].mean()), round(eco[eco["days_left"] == 20]["price"].mean()))
print("Eco by stops:\n", eco.groupby("stops")["price"].mean().round(0))
print("Eco by airline:\n", eco.groupby("airline")["price"].mean().sort_values().round(0))
print("Business by airline:\n", bus.groupby("airline")["price"].mean().round(0))
r = eco.groupby(["source_city", "destination_city"])["price"].mean().sort_values().round(0)
print("Cheapest eco routes:\n", r.head(3))
print("Priciest eco routes:\n", r.tail(3))
print("Duration corr (all, eco):", round(df["duration"].corr(df["price"]), 2), round(eco["duration"].corr(eco["price"]), 2))