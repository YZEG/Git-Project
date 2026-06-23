# -*- coding: utf-8 -*-
"""起点中文网月票排行榜爬虫"""

import re
import time
import traceback

import pymysql
import requests
from db_config import get_db_config

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) '
                  'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 '
                  'Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
              'image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://m.qidian.com/',
}

BOOK_PATTERN = re.compile(
    r'\{"catId":\d+,"rankCnt":"[^"]+","bName":"([^"]+)","rankNum":\d+,'
    r'"cat":"([^"]+)","cnt":"[^"]+","subCatId":\d+,"bid":"([^"]+)",'
    r'"subCat":"([^"]+)","bAuth":"([^"]+)","desc":"([^"]+)"'
)


def init_database():
    """创建数据库和表，清空旧数据，返回连接。"""
    config = get_db_config()
    config.pop('database', None)
    conn = pymysql.connect(**config)
    cursor = conn.cursor()

    cursor.execute('CREATE DATABASE IF NOT EXISTS qidian_rank CHARACTER SET utf8mb4')
    cursor.execute('USE qidian_rank')
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
    cursor.execute('DELETE FROM books')

    conn.commit()
    return conn


def get_book_status(bid):
    """根据书籍ID获取真实状态（连载/完结）。"""
    try:
        r = requests.get(
            f'https://m.qidian.com/book/{bid}',
            headers=HEADERS,
            timeout=10,
        )
        if r.status_code != 200:
            return '未知'

        if '连载中' in r.text:
            return '连载'
        if r.text.count('完本') > r.text.count('连载'):
            return '完结'
        return '连载'

    except Exception as e:
        print(f"获取书籍状态失败(bid={bid}): {e}")
        return '未知'


def get_book_info():
    """获取起点月票排行榜书籍信息，返回字典列表或 None。"""
    try:
        r = requests.get(
            'https://m.qidian.com/rank/yuepiao',
            headers=HEADERS,
            timeout=15,
        )
        if r.status_code != 200:
            print(f"请求失败，状态码: {r.status_code}")
            return None

        matches = BOOK_PATTERN.findall(r.text)

        books = []
        for i, match in enumerate(matches[:50]):
            book = {
                'name': match[0],
                'bid': match[2],
                'author': match[4],
                'tags': f"{match[1]},{match[3]}",
                'intro': match[5].replace('“', '"').replace('”', '"').strip(),
            }
            book['status'] = get_book_status(match[2])
            if (i + 1) % 5 == 0:
                time.sleep(1)

            books.append(book)
            print(f"已获取第{i+1}本书: {match[0]} - {book['status']}")

        return books

    except Exception as e:
        print(f"爬取过程中发生错误: {e}")
        traceback.print_exc()
        return None


def write_to_database(books, conn):
    """将书籍信息写入数据库。"""
    try:
        cursor = conn.cursor()
        for book in books:
            cursor.execute(
                'INSERT INTO books (name, author, status, tags, intro) VALUES (%s, %s, %s, %s, %s)',
                (book.get('name', '未知'), book.get('author', '未知'),
                 book.get('status', '未知'), book.get('tags', '无'),
                 book.get('intro', '无简介')),
            )
        conn.commit()
        print(f"成功写入MySQL数据库: qidian_rank，共 {len(books)} 条记录")
    except Exception as e:
        print(f"写入数据库时发生错误: {e}")
        conn.rollback()


if __name__ == '__main__':
    print("开始爬取起点月票排行榜...")
    try:
        conn = init_database()
        books = get_book_info()

        if books:
            print(f"成功获取 {len(books)} 本书的信息")
            write_to_database(books, conn)
        else:
            print("未能获取书籍信息")

        conn.close()

    except pymysql.Error as e:
        print(f"数据库连接错误: {e}")
        print("请确保MySQL服务器已启动，并检查数据库配置是否正确")
    except Exception as e:
        print(f"程序运行错误: {e}")
