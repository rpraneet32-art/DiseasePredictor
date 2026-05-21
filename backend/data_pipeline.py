import pandas as pd
import random
from datetime import datetime, timedelta
import os

os.makedirs('backend/data', exist_ok=True)

regions = ["Delhi", "Maharashtra"]
start_date = datetime(2023, 1, 1)
dates = [start_date + timedelta(days=7*i) for i in range(52)]

health_records = []
climate_trends_records = []

for region in regions:
    for d in dates:
        date_str = d.strftime("%Y-%m-%d")
        cases = random.randint(10, 500)
        health_records.append([date_str, region, cases])
        
        temp = round(random.uniform(20.0, 40.0), 1)
        hum = round(random.uniform(40.0, 90.0), 1)
        rain = round(random.uniform(0.0, 150.0), 1)
        trend = random.randint(10, 100)
        climate_trends_records.append([date_str, region, temp, hum, rain, trend])

df_health = pd.DataFrame(health_records, columns=["Date", "Region", "Cases"])
df_climate = pd.DataFrame(climate_trends_records, columns=["Date", "Region", "Temperature", "Humidity", "Rainfall", "Search_Trend"])

df_health.to_csv("backend/data/raw_health_data.csv", index=False)
df_climate.to_csv("backend/data/raw_climate_data.csv", index=False)

merged_df = pd.merge(df_health, df_climate, on=["Date", "Region"])

def set_risk(c):
    if c > 300: return "High"
    if c > 150: return "Medium"
    return "Low"

merged_df["Risk"] = merged_df["Cases"].apply(set_risk)
merged_df.to_csv("backend/data/master_training_data.csv", index=False)

print(merged_df.head())