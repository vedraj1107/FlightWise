from cleaner import load_data
import analysis as an
import advisor as ad

def main():
    df = load_data()
    eco = df[df["class"] == "Economy"]
    while True:
        print("\n=== FlightWise ===")
        print("1. Overall stats")
        print("2. Airline-wise avg price (Economy)")
        print("3. Best booking window (Economy)")
        print("4. Booking advisor (route)")
        print("5. Budget recommender")
        print("6. Dashboard (charts)")
        print("7. Cheapest destinations from a city")
        print("8. Stops vs price (route)")
        print("9. Savings calculator")
        print("0. Exit")
        ch = input("Choice: ").strip()

        if ch == "1":
            for k, v in an.stats(df).items():
                print(f"{k}: {v:.0f}")
            print("Duration-price correlation:", round(an.corr_duration_price(df), 2))
        elif ch == "2":
            print(an.airline_avg(eco).round(0))
        elif ch == "3":
            print(an.booking_window(eco).round(0))
        elif ch == "4":
            s = input("From: "); d = input("To: "); c = input("Class (Economy/Business): ")
            res = ad.advise(df, s, d, c)
            if res is None:
                print("No data for this route.")
            else:
                for k, v in res.items():
                    print(f"{k}: {v}")
        elif ch == "5":
            s = input("From: "); d = input("To: ")
            b = int(input("Budget: "))
            res = ad.recommend(df, s, d, b)
            if res.empty:
                print("No flights in this budget.")
            else:
                print(res.to_string(index=False))
        elif ch == "6":
            an.show_dashboard(eco)
        elif ch == "7":
            s = input("From: ")
            res = ad.cheapest_destinations(df, s)
            if res.empty:
                print("No data.")
            else:
                print(res)
        elif ch == "8":
            s = input("From: "); d = input("To: ")
            res = ad.stops_vs_price(df, s, d)
            print("No data." if res.empty else res)
        elif ch == "9":
            s = input("From: "); d = input("To: ")
            n = int(input("Days left before flight (1-49): "))
            res = ad.savings(df, s, d, n)
            if res is None:
                print("No data for this input.")
            else:
                for k, v in res.items():
                    print(f"{k}: {v}")
        elif ch == "0":
            break
        else:
            print("Invalid choice")

main()