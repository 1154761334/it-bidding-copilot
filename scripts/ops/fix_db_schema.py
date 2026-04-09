import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from api.core.database import engine

def fix_migration():
    with engine.begin() as conn:
        print("Adding columns to companies table...")
        # Check and add columns
        cols = [
            ("unified_social_credit_code", "VARCHAR"),
            ("registered_capital", "VARCHAR"),
            ("address", "VARCHAR"),
            ("legal_representative", "VARCHAR")
        ]
        
        for col_name, col_type in cols:
            try:
                conn.execute(text(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type};"))
                print(f"Added {col_name}")
            except Exception as e:
                print(f"Column {col_name} already exists.")

        # Update personnel columns too
        try:
            conn.execute(text("ALTER TABLE enterprise_personnel ADD COLUMN level VARCHAR;"))
            conn.execute(text("ALTER TABLE enterprise_personnel ADD COLUMN years_of_experience INTEGER;"))
            print("Added personnel columns")
        except Exception:
            pass

if __name__ == "__main__":
    fix_migration()
