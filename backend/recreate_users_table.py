import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'HYZ666@',
    'database': 'qidian_rank',
    'charset': 'utf8mb4',
}

def recreate_users_table():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS user_collections;")
        print("已删除 user_collections 表")
        
        cursor.execute("DROP TABLE IF EXISTS user_favorites;")
        print("已删除 user_favorites 表")
        
        cursor.execute("DROP TABLE IF EXISTS users;")
        print("已删除旧的 users 表")

        create_users_table = """
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            phone VARCHAR(20) UNIQUE,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        create_favorites_table = """
        CREATE TABLE user_favorites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            book_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            UNIQUE KEY unique_favorite (user_id, book_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        cursor.execute(create_users_table)
        print("users表创建成功")
        
        cursor.execute(create_favorites_table)
        print("user_favorites表创建成功")

        conn.commit()
        print("所有表创建成功")
        
    except pymysql.Error as e:
        print(f"创建表时出错: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    recreate_users_table()