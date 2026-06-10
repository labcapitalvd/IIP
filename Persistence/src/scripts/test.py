import os
import pandas as pd
from shared_db import Base

# 🔥 This is the missing piece that hooks up the metadata!
from shared_models import __all__ as model_names
from shared_utils import print_list

OUTPUT_DIR = "/api/scripts/extracted"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("🚀 Starting extraction of SQLAlchemy models...")

# Diagnostic check to see exactly what found
print_list("Tables Found in Metadata", list(Base.metadata.tables.keys()))

# Loop through all models registered in your Base metadata
for table_name, table in Base.metadata.tables.items():
    # Get column names as headers
    columns = [column.name for column in table.columns]

    # Create an empty DataFrame with these columns
    df = pd.DataFrame(columns=columns)

    # Define the absolute output path
    file_path = os.path.join(OUTPUT_DIR, f"{table_name}_template.csv")

    try:
        # Save to an individual Excel file
        df.to_csv(file_path, index=False, sep="|")
        print(f"  ✅ Created template: {table_name}_template.csv")
    except Exception as e:
        print(f"  ❌ Failed to write {table_name}: {str(e)}")
