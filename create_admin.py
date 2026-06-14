import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'HYZ666@',
    'database': 'qidian_rank',
    'charset': 'utf8mb4',
}

def create_admin():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            print("管理员账户已存在")
            return

        cursor.execute(
            "INSERT INTO users (username, phone, password, role) VALUES (%s, %s, %s, %s)",
            ('admin', '13800138000', '123456', 'admin')
        )
        conn.commit()
        print("管理员账户创建成功")
        print("用户名: admin")
        print("密码: 123456")
        
    except pymysql.Error as e:
        print(f"创建管理员账户时出错: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_admin()