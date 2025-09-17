import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "plots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_eda():
    df = pd.read_csv(os.path.join(BASE_DIR, "outputs", "cleaned_crime_data.csv"))

    # crime trend by year
    plt.figure(figsize=(10,5))
    sns.lineplot(data=df, x="year", y="total_crimes", hue="state_ut")
    plt.title("Crime Trends by State")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "crime_trends.png"))
    plt.close()

    # top states by crime rate
    if "population_lakhs" in df.columns:
        df["crime_rate_per_lakh"] = df["total_crimes"] / df["population_lakhs"]
        top_states = df.groupby("state_ut")["crime_rate_per_lakh"].mean().sort_values(ascending=False).head(10)

        plt.figure(figsize=(10,5))
        sns.barplot(x=top_states.index, y=top_states.values)
        plt.xticks(rotation=75)
        plt.title("Top 10 States by Crime Rate per Lakh Population")
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "top_states_crime_rate.png"))
        plt.close()

if __name__ == "__main__":
    run_eda()
    print("✅ EDA plots saved in outputs/plots/")
