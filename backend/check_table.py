import pymysql
from db_config import get_db_config

def check_table():
    config = get_db_config()
    try:
        conn = pymysql.connect(**config)
        cursor = conn.cursor()

        cursor.execute("DESCRIBE users;")
        print("users表结构:")
        for row in cursor.fetchall():
            print(row)
        
    except pymysql.Error as e:
        print(f"查询表结构时出错: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_table()