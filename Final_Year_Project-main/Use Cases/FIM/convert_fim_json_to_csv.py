import json
import pandas as pd

# Load JSON file
with open("fim_logs.json", "r") as file:
    data = [json.loads(line) for line in file]

# Convert JSON data to Pandas DataFrame
df = pd.json_normalize(data)

# Save as CSV
df.to_csv("fim_logs.csv", index=False)

print("FIM logs have been successfully saved as fim_logs.csv")

