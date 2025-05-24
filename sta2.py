
import pandas as pd

def get_df():
    wetter_df = pd.read_csv('wetter/bern_23.csv')
    return wetter_df

mydf = get_df()
expected_dt = 1672531200
duplicates = []
# Initialize variables
new_df = []  # List to collect matching rows
# Iterate through DataFrame
for index, row in mydf.iterrows():
    if row["dt"] == expected_dt:
        expected_dt += 3600  # Increment by 1 hour
        new_df.append(row)  # Collect matching row
    else:
        duplicates.append(str(row["dt"]))  # Log duplicate dt
        print(f"Duplicate row at index {index}: dt = {row['dt']}")  # Print duplicate row info

# Create a DataFrame from matching rows
new_df = pd.DataFrame(new_df)

# Save the DataFrame without duplicates (new_df) to a file (optional)
new_df.to_csv("no_duplicates.csv", index=False)

# If you want to modify mydf to exclude duplicates
mydf_no_duplicates = new_df.copy()  # Use new_df as it contains non-duplicate rows

# Print duplicates list (optional)
print("Duplicate dt values:", duplicates)


print(duplicates)
print(len(mydf)-1)
print(len(duplicates))
print(len(mydf)-len(duplicates))
print((len(mydf)-len(duplicates))/24)

# daten kombinieren, jede fahrt


