from invoke import task
from lib.db import db
import os
import logging

logger = logging.getLogger(__name__)

def read_sql_files(sql_dir):
    """Read SQL files from directory in sorted order"""
    sql_files = []
    for file in sorted(os.listdir(sql_dir)):
        if file.endswith('.sql'):
            with open(os.path.join(sql_dir, file), 'r') as f:
                sql_files.append(f.read())
    return sql_files

@task
def init_db(c, env="development"):
  from flask import Flask
  app = Flask(__name__)
    # Setup logging
  logger.info("Starting database initialization")
  try:
      # Get SQL scripts directory
      sql_dir = os.path.join(app.root_path, 'sql', 'setup')
      if not os.path.exists(sql_dir):
          raise FileNotFoundError(f"SQL directory not found: {sql_dir}")
      
      # Initialize database
      db.init(app)
      cursor = db.cursor()
      
      # Execute SQL scripts in order
      for sql in read_sql_files(sql_dir):
          logger.info(f"Executing SQL script...")
          cursor.executescript(sql)
      
      db.commit()
      logger.info("Database initialized successfully")
      
  except Exception as e:
    logger.error(f"Database initialization failed: {str(e)}")
    db.rollback()
    raise
