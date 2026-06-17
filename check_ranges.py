import pandas as pd

df = pd.read_csv('dataset/Final_Healthcare_Delay_Risk_Dataset.csv')
df_filtered = df[(df['Age'] >= 18) & (df['Age'] <= 60)]

print('\n' + '='*100)
print('NUMERICAL FEATURES - ORIGINAL DATASET RANGES (Age 18-60, n=3836)')
print('='*100 + '\n')

numerical_cols = [
    'Age', 'Health_Awareness_Score', 'Symptom_Severity', 
    'Distance_to_Healthcare_km', 'Fear_of_Cost', 'Fear_of_Hospital', 
    'Delay_in_Seeking_Care_Days'
]

for col in numerical_cols:
    min_val = df_filtered[col].min()
    max_val = df_filtered[col].max()
    mean_val = df_filtered[col].mean()
    std_val = df_filtered[col].std()
    print(f'{col:40s} | min: {min_val:8.2f} | max: {max_val:8.2f} | mean: {mean_val:8.2f} | std: {std_val:8.2f}')

print('\n' + '='*100)
print('CATEGORICAL FEATURES - UNIQUE VALUES')
print('='*100 + '\n')

categorical_cols = ['Gender', 'Residence', 'Education_Level', 'Income_Level', 'Insurance_Status']

for col in categorical_cols:
    unique_vals = df_filtered[col].unique().tolist()
    print(f'{col:40s} | {unique_vals}')

print('\n' + '='*100)
print('TARGET VARIABLE - HEALTH_RISK_SCORE')
print('='*100 + '\n')

target_col = 'Health_Risk_Score'
print(f'{target_col:40s} | min: {df_filtered[target_col].min():8.2f} | max: {df_filtered[target_col].max():8.2f} | mean: {df_filtered[target_col].mean():8.2f} | std: {df_filtered[target_col].std():8.2f}')
