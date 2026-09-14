import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/dataset_final.csv")

print(f"Shape: {df.shape}")
print(f"Columns ({len(df.columns)}): {list(df.columns)}")

print("\n--- Agente Distribution ---")
print(df["tipo_agente"].value_counts(dropna=False))

print("\n--- Summary Table of Variables ---")
summary = []
for col in df.columns:
    val_count = df[col].notna().sum()
    null_count = df[col].isna().sum()
    pct_null = (null_count / len(df)) * 100
    dtype = str(df[col].dtype)
    n_unique = df[col].nunique(dropna=False)
    
    # Sample values
    sample_vals = df[col].dropna().unique()[:3].tolist()
    
    # By group if applicable
    h_sub = df[df["tipo_agente"] == "humano"][col]
    ia_sub = df[df["tipo_agente"] == "ia"][col]
    
    h_stat = ""
    ia_stat = ""
    if pd.api.types.is_numeric_dtype(df[col]):
        if n_unique <= 2:
            h_stat = f"mean={h_sub.mean():.2f}"
            ia_stat = f"mean={ia_sub.mean():.2f}"
        else:
            h_stat = f"mean={h_sub.mean():.1f}, mdn={h_sub.median():.1f}"
            ia_stat = f"mean={ia_sub.mean():.1f}, mdn={ia_sub.median():.1f}"
    else:
        h_stat = f"{h_sub.value_counts().to_dict()}"[:40]
        ia_stat = f"{ia_sub.value_counts().to_dict()}"[:40]
        
    summary.append({
        "col": col,
        "dtype": dtype,
        "valid": val_count,
        "missing_pct": f"{pct_null:.1f}%",
        "unique": n_unique,
        "h_stat": h_stat,
        "ia_stat": ia_stat,
        "sample": str(sample_vals)[:30]
    })

sum_df = pd.DataFrame(summary)
print(sum_df.to_string())
