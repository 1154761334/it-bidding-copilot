import os
import psycopg2
from sqlalchemy import text
from api.core.database import SessionLocal, engine
from api.models.assets_v2 import Base

def init_pgvector():
    """
    Initialize the database, creating the pgvector extension and all tables.
    """
    print("正在初始化企业级数据库与 pgvector 扩展...")
    
    # Enable pgvector at the database level directly
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    print("pgvector 扩展已就绪。正在同步数据表 Schema V2...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Schema V2 同步与清空完成。")

if __name__ == "__main__":
    init_pgvector()
