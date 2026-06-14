import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'HYZ666@',
    'database': 'qidian_rank',
    'charset': 'utf8mb4',
}

def check_table():
    try:
        conn = pymysql.connect(**DB_CONFIG)
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