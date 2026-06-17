"""
Data Range Inspector - Determines valid input ranges for prediction pipeline
This script analyzes the filtered dataset (Age 18-60) to extract exact numerical ranges
"""

import pandas as pd

# Load and filter dataset
df = pd.read_csv('dataset/Final_Healthcare_Delay_Risk_Dataset.csv')
print(f"Total dataset: {len(df)} rows")

# Filter to Age 18-60 per paper methodology
df_filtered = df[(df['Age'] >= 18) & (df['Age'] <= 60)]
print(f"After Age 18-60 filtering: {len(df_filtered)} rows\n")

# Numerical features to analyze
numerical_features = [
    'Age',
    'Health_Awareness_Score',
    'Symptom_Severity',
    'Distance_to_Healthcare_km',
    'Fear_of_Cost',
    'Fear_of_Hospital',
    'Delay_in_Seeking_Care_Days'
]

print("="*100)
print("NUMERICAL FEATURE RANGES (RAW VALUES - Age 18-60 Dataset)")
print("="*100 + "\n")

# Display ranges in format for code
print("# For VALID_RANGES in predict_risk.py:")
print("VALID_RANGES = {")

valid_ranges_dict = {}
for feature in numerical_features:
    min_val = df_filtered[feature].min()
    max_val = df_filtered[feature].max()
    valid_ranges_dict[feature] = (min_val, max_val)
    
    print(f"    '{feature}': ({min_val}, {max_val}),  # min: {min_val:.2f}, max: {max_val:.2f}")

print("}")

print("\n" + "="*100)
print("DETAILED STATISTICS")
print("="*100 + "\n")

for feature in numerical_features:
    print(f"\n{feature}:")
    print(f"  Min:    {df_filtered[feature].min():.4f}")
    print(f"  Max:    {df_filtered[feature].max():.4f}")
    print(f"  Mean:   {df_filtered[feature].mean():.4f}")
    print(f"  Std:    {df_filtered[feature].std():.4f}")
    print(f"  Median: {df_filtered[feature].median():.4f}")
    print(f"  Q1:     {df_filtered[feature].quantile(0.25):.4f}")
    print(f"  Q3:     {df_filtered[feature].quantile(0.75):.4f}")

# Categorical features
categorical_features = ['Gender', 'Residence', 'Education_Level', 'Income_Level', 'Insurance_Status']

print("\n" + "="*100)
print("CATEGORICAL FEATURES - VALID VALUES")
print("="*100 + "\n")

print("# For VALID_CATEGORIES in predict_risk.py:")
print("VALID_CATEGORIES = {")

for feature in categorical_features:
    unique_vals = df_filtered[feature].unique().tolist()
    print(f"    '{feature}': {unique_vals},")

print("}")

# Target variable range
print("\n" + "="*100)
print("TARGET VARIABLE - HEALTH_RISK_SCORE")
print("="*100 + "\n")

target = 'Health_Risk_Score'
print(f"{target}:")
print(f"  Min:    {df_filtered[target].min():.4f}")
print(f"  Max:    {df_filtered[target].max():.4f}")
print(f"  Mean:   {df_filtered[target].mean():.4f}")
print(f"  Std:    {df_filtered[target].std():.4f}")

# Risk category distribution
print("\n" + "="*100)
print("RISK CATEGORY DISTRIBUTION")
print("="*100 + "\n")

if 'Risk_Category' in df_filtered.columns:
    print(df_filtered['Risk_Category'].value_counts())
