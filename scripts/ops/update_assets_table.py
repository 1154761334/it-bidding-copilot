import sys
import os
# Add the project root to sys.path
sys.path.append(os.getcwd())

from api.core.database import engine
from api.models.assets_v2 import Base, CompanyAsset

from sqlalchemy import text

def update_schema():
    print("Checking if 'company_assets' table needs to be created...")
    try:
        # Enable pgvector at the database level directly
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("pgvector extension ensured.")
            
        # This will create tables that don't exist
        Base.metadata.create_all(bind=engine)
        print("Schema update completed successfully.")
    except Exception as e:
        print(f"Error during schema update: {e}")

if __name__ == "__main__":
    update_schema()
