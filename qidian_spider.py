# -*- coding: utf-8 -*-
"""
起点中文网月票排行榜爬虫程序

功能说明：
- 爬取起点中文网月票排行榜数据
- 获取书籍名称、作者、真实状态、标签和简介信息
- 将结果写入MySQL数据库

使用方法：
- 直接运行此脚本即可
- 确保已安装 requests 和 pymysql 库
  - pip install requests
  - pip install pymysql
- 数据库：qidian_rank
"""

# 导入所需模块
import requests  # 用于发送HTTP请求
import re        # 用于正则表达式匹配
import pymysql   # 用于MySQL数据库操作
import time      # 用于设置请求间隔

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',      # 数据库主机
    'port': 3306,             # 数据库端口
    'user': 'root',           # 数据库用户名
    'password': 'HYZ666@',    # 数据库密码
    'charset': 'utf8mb4',     # 字符编码
}

def init_database():
    """
    初始化数据库，创建数据库和书籍信息表
    
    返回值：
        pymysql.Connection: 数据库连接对象
    """
    # 先连接MySQL服务器（不指定数据库）
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 创建数据库（如果不存在）
    cursor.execute('CREATE DATABASE IF NOT EXISTS qidian_rank CHARACTER SET utf8mb4')
    cursor.execute('USE qidian_rank')
    
    # 创建书籍信息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            author VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL,
            tags VARCHAR(100),
            intro TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # 清空旧数据（每次运行重新爬取）
    cursor.execute('DELETE FROM books')
    
    conn.commit()
    return conn

def get_book_status(bid):
    """
    根据书籍ID获取书籍的真实状态
    
    参数：
        bid: 书籍ID
        
    返回值：
        str: 书籍状态（连载/完结）
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'Referer': 'https://m.qidian.com/rank/yuepiao',
    }
    
    try:
        # 访问书籍详情页
        url = f'https://m.qidian.com/book/{bid}'
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code != 200:
            return '未知'
        
        # 统计"完本"和"连载"的出现次数
        wanben_count = r.text.count('完本')
        lianzai_count = r.text.count('连载')
        
        # 优先级1: 查找"连载中"标识（表示正在连载）
        if '连载中' in r.text:
            return '连载'
        
        # 优先级2: 如果"完本"出现次数多于"连载"，且没有"连载中"，则判断为完结
        if wanben_count > lianzai_count:
            return '完结'
        
        # 优先级3: 默认返回连载（月票榜书籍大多是连载状态）
        return '连载'
    
    except Exception as e:
        print(f"获取书籍状态失败(bid={bid}): {e}")
        return '未知'

def get_book_info():
    """
    获取起点月票排行榜书籍信息
    
    返回值：
        list: 包含书籍信息的字典列表，每个字典包含 name, author, status, tags, intro 字段
        None: 获取失败时返回None
    """
    # 设置请求头，模拟iPhone浏览器访问移动端网站
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://m.qidian.com/',
    }

    try:
        # 发送GET请求获取移动端月票排行榜页面
        r = requests.get('https://m.qidian.com/rank/yuepiao', headers=headers, timeout=15)
        
        # 检查请求是否成功
        if r.status_code != 200:
            print(f"请求失败，状态码: {r.status_code}")
            return None

        # 定义正则表达式模式匹配书籍记录（包含bid字段）
        pattern = r'\{"catId":\d+,"rankCnt":"[^"]+","bName":"([^"]+)","rankNum":\d+,"cat":"([^"]+)","cnt":"[^"]+","subCatId":\d+,"bid":"([^"]+)","subCat":"([^"]+)","bAuth":"([^"]+)","desc":"([^"]+)"'
        
        # 查找所有匹配的书籍记录
        matches = re.findall(pattern, r.text)
        
        # 构建书籍信息列表（最多50本）
        books = []
        for i, match in enumerate(matches[:50]):
            book_info = {
                'name': match[0],                                  # 书名
                'bid': match[2],                                   # 书籍ID
                'author': match[4],                                # 作者
                'tags': f"{match[1]},{match[3]}",                  # 标签（分类+子分类）
                'intro': match[5].replace('“', '"').replace('”', '"').strip()  # 简介
            }
            
            # 获取真实状态（每获取5本书暂停1秒，避免请求过快）
            book_info['status'] = get_book_status(match[2])
            if (i + 1) % 5 == 0:
                time.sleep(1)
            
            books.append(book_info)
            print(f"已获取第{i+1}本书: {match[0]} - {book_info['status']}")
        
        return books

    except Exception as e:
        # 捕获所有异常并输出错误信息
        print(f"爬取过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def write_to_database(books, conn):
    """
    将书籍信息写入MySQL数据库
    
    参数：
        books: 书籍信息列表
        conn: 数据库连接对象
    
    返回值：
        None
    """
    try:
        cursor = conn.cursor()
        
        # 插入书籍数据
        for book in books:
            cursor.execute('''
                INSERT INTO books (name, author, status, tags, intro)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                book.get('name', '未知'),
                book.get('author', '未知'),
                book.get('status', '未知'),
                book.get('tags', '无'),
                book.get('intro', '无简介')
            ))
        
        conn.commit()
        print(f"成功写入MySQL数据库: qidian_rank，共 {len(books)} 条记录")
        
    except Exception as e:
        print(f"写入数据库时发生错误: {e}")
        conn.rollback()

def query_database(conn):
    """
    查询数据库中的书籍信息并显示
    
    参数：
        conn: 数据库连接对象
    
    返回值：
        None
    """
    cursor = conn.cursor()
    
    # 查询所有书籍
    cursor.execute('SELECT name, author, status, tags FROM books ORDER BY id')
    rows = cursor.fetchall()
    
    print("\n=== MySQL数据库中的书籍信息 ===")
    for row in rows:
        print(f"书名: {row[0]} | 作者: {row[1]} | 状态: {row[2]} | 标签: {row[3]}")

if __name__ == '__main__':
    """
    程序入口
    """
    print("开始爬取起点月票排行榜...")
    
    try:
        # 初始化数据库
        conn = init_database()
        
        # 获取书籍信息
        books = get_book_info()
        
        # 如果成功获取到书籍信息，则写入数据库
        if books:
            print(f"成功获取 {len(books)} 本书的信息")
            write_to_database(books, conn)
            # 显示数据库中的数据
            query_database(conn)
        else:
            print("未能获取书籍信息")
        
        # 关闭数据库连接
        conn.close()
        
    except pymysql.Error as e:
        print(f"数据库连接错误: {e}")
        print("请确保MySQL服务器已启动，并检查数据库配置是否正确")
    except Exception as e:
        print(f"程序运行错误: {e}")