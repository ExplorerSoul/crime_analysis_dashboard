import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px
from data_prep import load_and_clean

# ---------------- Load Data ----------------
df = load_and_clean("NCRB_Table_1A.1.csv")

exclude_list = ["Total State (S)", "Total UT(S)", "Total All India"]
df = df[~df["state_ut"].isin(exclude_list)]

# Fix per-capita crime rate (population in lakhs → convert to 100k)
if "population_lakhs" in df.columns:
    df["crime_rate_per_100k"] = (df["total_crimes"] / (df["population_lakhs"] * 100000)) * 100000
else:
    df["crime_rate_per_100k"] = df["total_crimes"]

# ---------------- Streamlit Config ----------------
st.set_page_config(page_title="Crime Analytics in India", layout="wide")
st.title("📊 Crime Analysis in India (NCRB 2020–2022)")

# ---------------- Sidebar ----------------
st.sidebar.header("🔎 Filters")

all_states = sorted(df["state_ut"].unique())
select_all = st.sidebar.checkbox("Select All States/UTs", value=True)

states = (
    st.sidebar.multiselect("Select States/UTs", all_states, default=all_states)
    if select_all
    else st.sidebar.multiselect("Select States/UTs", all_states)
)

years = st.sidebar.multiselect(
    "Select Years",
    sorted(df["year"].unique()),
    default=sorted(df["year"].unique())
)

filtered_df = df[(df["state_ut"].isin(states)) & (df["year"].isin(years))]

if filtered_df.empty:
    st.info("⚠️ Please select at least one state/UT and one year to see the dashboard.")
    st.stop()

# ---------------- KPIs ----------------
st.subheader("📌 Key Insights")
col1, col2, col3 = st.columns(3)

total_crimes = int(filtered_df["total_crimes"].sum())
avg_crime_rate = round(filtered_df["crime_rate_per_100k"].mean(), 2)

state_means = filtered_df.groupby("state_ut")["crime_rate_per_100k"].mean()
worst_state = state_means.idxmax()
best_state = state_means.idxmin()

col1.metric("Total Crimes (selected)", f"{total_crimes:,}")
col2.metric("Avg. Crime Rate per 100k", avg_crime_rate)
col3.metric("Worst vs Best State", f"{worst_state} 🔴 / {best_state} 🟢")

# ---------------- Tabs for Charts ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "📈 Trends", "🌍 Heatmap", "📉 Correlation", "📋 Data"]
)

# ---------------- Tab 1: Overview ----------------
with tab1:
    st.subheader("Crime Rate per 100k (Bar Chart)")
    fig_bar = px.bar(
        filtered_df,
        x="state_ut",
        y="crime_rate_per_100k",
        color="year",
        barmode="group",
        title="Crime Rate per 100k Population"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Top & Bottom 5 States
    st.subheader("🏆 Top & Bottom States by Avg. Crime Rate")
    avg_state_rate = state_means.sort_values(ascending=False)
    col_top, col_bottom = st.columns(2)
    with col_top:
        st.write("🔝 Top 5 States")
        st.bar_chart(avg_state_rate.head(5))
    with col_bottom:
        st.write("⬇️ Bottom 5 States")
        st.bar_chart(avg_state_rate.tail(5))

# ---------------- Tab 2: Yearly Trends ----------------
with tab2:
    st.subheader("Year-on-Year Crime Trends")
    fig_line = px.line(
        filtered_df,
        x="year",
        y="crime_rate_per_100k",
        color="state_ut",
        markers=True,
        title="Crime Rate Trends Over Time"
    )
    st.plotly_chart(fig_line, use_container_width=True)

# ---------------- Tab 3: Heatmap ----------------
with tab3:
    st.subheader("🌍 Crime Rate Heatmap (India)")

    geojson_path = os.path.join(os.path.dirname(__file__), "..", "data", "india_state.geojson")

    if os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            india_geojson = json.load(f)

        # --- Fix State/UT naming mismatches ---
        rename_map = {
            "Andaman and Nicobar Islands": "Andaman and Nicobar",
            "Pondicherry": "Puducherry",
            "Odisha": "Orissa",  # GeoJSON uses "Orissa"
            "Uttarakhand": "Uttaranchal",
            "Dadra and Nagar Haveli and Daman and Diu": "Dadra and Nagar Haveli",
            "Ladakh": "Jammu and Kashmir",
            "Telangana": "Andhra Pradesh",
        }
        filtered_df["state_ut_clean"] = filtered_df["state_ut"].replace(rename_map)

        geo_states = {f["properties"]["NAME_1"] for f in india_geojson["features"]}
        df_states = set(filtered_df["state_ut_clean"].unique())
        unmatched = df_states - geo_states
        if unmatched:
            st.warning(f"⚠️ Some states not matched with map: {unmatched}")

        # Plot animated choropleth
        fig_map = px.choropleth(
            filtered_df,
            geojson=india_geojson,
            locations="state_ut_clean",
            featureidkey="properties.NAME_1",
            color="crime_rate_per_100k",
            animation_frame="year",
            color_continuous_scale="Reds",
            title="Crime Rate per 100k Population (Animated)"
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_map, use_container_width=True)

    else:
        st.warning("⚠️ India GeoJSON file not found. Add `india_state.geojson` in data/ to enable map.")

# ---------------- Tab 4: Correlation ----------------
with tab4:
    st.subheader("📉 Correlation Analysis")
    if "chargesheeting_rate_2022" in filtered_df.columns:
        fig_scatter = px.scatter(
            filtered_df,
            x="crime_rate_per_100k",
            y="chargesheeting_rate_2022",
            color="state_ut",
            size="total_crimes",
            title="Crime Rate vs Chargesheeting Rate"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Chargesheeting rate not available in dataset.")

# ---------------- Tab 5: Data Table ----------------
with tab5:
    st.subheader("📋 Data Preview & Download")
    st.dataframe(filtered_df.head(20))

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Filtered Data (CSV)", csv, "filtered_data.csv", "text/csv")
