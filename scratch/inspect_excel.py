import pandas as pd

excel_path = "data/validation/dataset_validacion_consolidado_final.xlsx"
xls = pd.ExcelFile(excel_path)

print("Sheet names:", xls.sheet_names)

for sheet in xls.sheet_names:
    df_sheet = pd.read_excel(excel_path, sheet_name=sheet)
    print(f"\n--- Sheet: {sheet} (Shape: {df_sheet.shape}) ---")
    print("Columns:", list(df_sheet.columns))
    print(df_sheet.head(3))
