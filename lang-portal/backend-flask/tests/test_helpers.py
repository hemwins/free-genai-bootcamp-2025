import logging

def print_table_contents(db, table_name):
    """Print contents of specified table"""
    logger = logging.getLogger('test_logger_helper')
    cursor = db.cursor()
    try:
        cursor.execute(f'SELECT * FROM {table_name}')
        rows = cursor.fetchall()
        logger.info(f"=== Contents of {table_name} table ===")
        print(f"\n=== Contents of {table_name} table ===")
        if not rows:
            print("Table is empty")
            logger.info(f"Table {table_name} is empty")
            return
        for row in rows:
            logger.info(f"Row: {dict(row)}")
            print(dict(row))
    except Exception as e:
        print(f"Error reading {table_name}: {str(e)}")
        logger.error(f"Error reading {table_name}: {str(e)}")
        raise e