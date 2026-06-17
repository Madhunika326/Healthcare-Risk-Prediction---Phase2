import pandas as pd

df = pd.read_csv('dataset/Final_Healthcare_Delay_Risk_Dataset.csv')
print(f'Total rows in dataset: {len(df)}')
print(f'Age range: {df["Age"].min()} - {df["Age"].max()}')
filtered = df[(df["Age"] >= 18) & (df["Age"] <= 60)]
print(f'Rows with Age 18-60: {len(filtered)}')
print(f'\nAge statistics:')
print(df["Age"].describe())
