import os
import sys
from sqlalchemy import text

# Add the project root to sys.path
sys.path.append(os.getcwd())

from api.core.database import SessionLocal
from api.models.assets_v2 import EnterpriseCertificate, EnterpriseCase, EnterprisePersonnel, AssetChunk
from utils.embedding_engine import EmbeddingEngine

def reembed_table(db, model, column_name, text_field_names, batch_size=50):
    """
    Re-embed rows where the embedding column is NULL.
    """
    print(f"--- Re-embedding table: {model.__tablename__} ---", flush=True)
    
    # Initialize embedding engine
    ee = EmbeddingEngine()
    
    # Query rows where embedding is NULL
    rows = db.query(model).filter(getattr(model, column_name) == None).all()
    
    if not rows:
        print(f"No rows with NULL embeddings found for {model.__tablename__}.", flush=True)
        return

    total = len(rows)
    print(f"Found {total} rows to re-embed.", flush=True)
    
    for i in range(0, total, batch_size):
        batch = rows[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(total+batch_size-1)//batch_size}...", flush=True)
        
        texts_to_embed = []
        valid_rows = []
        
        for row in batch:
            text = " ".join([str(getattr(row, field)) for field in text_field_names if getattr(row, field)])
            if text:
                texts_to_embed.append(text)
                valid_rows.append(row)
        
        if texts_to_embed:
            try:
                embeddings = ee.embed_documents(texts_to_embed)
                for row, emb in zip(valid_rows, embeddings):
                    setattr(row, column_name, emb)
            except Exception as e:
                print(f"Error embedding batch starting at row {valid_rows[0].id}: {e}", flush=True)
        
        db.commit()
        print(f"Committed batch {i//batch_size + 1}", flush=True)
            
    print(f"Successfully re-embedded {model.__tablename__}.", flush=True)

def main():
    db = SessionLocal()
    try:
        # Re-embed each table
        reembed_table(db, EnterpriseCertificate, 'embedding', ['cert_type', 'cert_level', 'raw_name', 'certification_scope'])
        reembed_table(db, EnterpriseCase, 'embedding', ['project_name', 'industry', 'description', 'compliance_keywords'])
        reembed_table(db, EnterprisePersonnel, 'embedding', ['name', 'role', 'level', 'resume_text'])
        reembed_table(db, AssetChunk, 'embedding', ['content'])
        
        print("\nAll re-embedding tasks completed.")
    except Exception as e:
        print(f"Critical error during re-embedding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
