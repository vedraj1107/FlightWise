from pathlib import Path
import pandas as pd

def find_data():
    here = Path(__file__).resolve().parent
    roots = [here, Path.cwd(), Path.home() / "Downloads", Path.home() / "Desktop"]
    for root in roots:
        for pattern in ("Clean_Dataset*.csv", "Clean_Dataset*.zip"):
            try:
                for f in root.rglob(pattern):
                    if f.is_file():
                        return f
            except OSError:
                pass
    raise FileNotFoundError("Clean_Dataset.csv not found. Keep it in the Flightwise folder.")

def load_data():
    df = pd.read_csv(find_data())
    df = df.drop(columns=["Unnamed: 0", "flight"], errors="ignore")
    df = df.drop_duplicates().dropna()
    df["stops"] = df["stops"].map({"zero": 0, "one": 1, "two_or_more": 2})
    return df

if __name__ == "__main__":
    df = load_data()
    print(df.shape)
    print(df.head())