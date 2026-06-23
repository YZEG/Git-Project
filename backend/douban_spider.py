# -*- coding: utf-8 -*-
"""
豆瓣读书排行榜爬虫
爬取 https://book.douban.com/chart?subcat=all&icn=index-topchart-popular 的前50本书
进入每本书详情页爬取内容简介和豆瓣成员常用标签
数据写入 MySQL douban_books 数据库
"""

import json
import os
import re
import sys
import time

import pymysql
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://book.douban.com/',
}


def get_connection(database='douban_books'):
    """获取数据库连接"""
    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', 3306))
    user = os.environ.get('DB_USER', 'root')
    password = os.environ.get('DB_PASSWORD', '')
    return pymysql.connect(
        host=host, port=port, user=user, password=password,
        database=database, charset='utf8mb4', autocommit=True,
    )


def init_database():
    """创建数据库和 books 总表"""
    conn = get_connection(database=None)
    cursor = conn.cursor()
    cursor.execute('CREATE DATABASE IF NOT EXISTS douban_books '
                   'DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    cursor.execute('USE douban_books')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INT PRIMARY KEY AUTO_INCREMENT,
            rank_num INT NOT NULL,
            title VARCHAR(500) NOT NULL,
            douban_id VARCHAR(50) NOT NULL UNIQUE,
            url VARCHAR(500),
            cover VARCHAR(500),
            author VARCHAR(200),
            binding VARCHAR(50),
            rating VARCHAR(10),
            rating_count INT DEFAULT 0,
            star FLOAT DEFAULT 0,
            tags TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    conn.close()


def create_comment_table(cursor, douban_id):
    """为指定书籍创建评论表"""
    table = f'comments_{douban_id}'
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS `{table}` (
            id INT PRIMARY KEY AUTO_INCREMENT,
            comment_id VARCHAR(100) UNIQUE,
            username VARCHAR(200),
            content TEXT,
            rating VARCHAR(10),
            star FLOAT DEFAULT 0,
            vote_count INT DEFAULT 0,
            comment_time VARCHAR(50),
            url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    return table


def save_books_to_db(books):
    """将书籍列表写入数据库，同时为每本书创建评论表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM books')

    for book in books:
        douban_id = ''
        m = re.search(r'/subject/(\d+)', book.get('url', ''))
        if m:
            douban_id = m.group(1)
        create_comment_table(cursor, douban_id)
        cursor.execute('''
            INSERT INTO books (rank_num, title, douban_id, url, cover, author,
                binding, rating, rating_count, star, tags, description)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (
            book['rank'], book['title'], douban_id, book['url'], book['cover'],
            book['author'], book['binding'], book['rating'], book['rating_count'],
            book['star'], ','.join(book.get('tags', [])),
            book.get('description', ''),
        ))

    conn.close()
    print(f'已写入 {len(books)} 本书到 douban_books.books')


def save_comments_to_db(douban_id, comments):
    """将评论列表写入对应书籍的评论表"""
    if not comments:
        return 0
    table = f'comments_{douban_id}'
    conn = get_connection()
    cursor = conn.cursor()
    saved = 0
    for c in comments:
        try:
            cursor.execute(f'''
                INSERT INTO `{table}`
                    (comment_id, username, content, rating, star, vote_count, comment_time, url)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ''', (
                c.get('comment_id', ''), c.get('username', ''), c.get('content', ''),
                c.get('rating', ''), c.get('star', 0), c.get('vote_count', 0),
                c.get('comment_time', ''), c.get('url', ''),
            ))
            saved += 1
        except pymysql.IntegrityError:
            pass
    conn.close()
    return saved


# ---------- 爬取逻辑 ----------

def parse_book_item(li):
    """从排行榜列表页解析单本书籍基本信息"""
    book = {}
    rank_el = li.select_one('.green-num-box')
    book['rank'] = int(rank_el.get_text(strip=True)) if rank_el else 0

    title_el = li.select_one('h2 a')
    if not title_el:
        return None
    book['title'] = title_el.get_text(strip=True)
    book['url'] = title_el.get('href', '')

    cover_el = li.select_one('img.subject-cover')
    book['cover'] = cover_el.get('src', '') if cover_el else ''

    pub_el = li.select_one('.subject-abstract')
    if pub_el:
        parts = [p.strip() for p in pub_el.get_text(strip=True).split('/')]
        book['author'] = parts[0] if len(parts) >= 1 else ''
        book['binding'] = parts[-1] if len(parts) >= 2 else ''
    else:
        book['author'] = ''
        book['binding'] = ''

    rating_el = li.select_one('.subject-rating .font-small')
    book['rating'] = rating_el.get_text(strip=True) if rating_el else ''

    rating_count_el = li.select_one('.subject-rating .color-gray')
    if rating_count_el:
        m = re.search(r'(\d+)', rating_count_el.get_text(strip=True))
        book['rating_count'] = int(m.group(1)) if m else 0
    else:
        book['rating_count'] = 0

    book['tags'] = [t.get_text(strip=True) for t in li.select('.subject-tags .tag')]

    star_el = li.select_one('.star-img')
    book['star'] = 0
    if star_el:
        for cls in star_el.get('class', []):
            if cls.startswith('allstar') and cls[7:].isdigit():
                book['star'] = int(cls[7:]) / 10
    return book


def crawl_book_detail(book):
    """进入书籍详情页，爬取内容简介和豆瓣成员常用标签"""
    url = book.get('url', '')
    if not url:
        return book

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = 'utf-8'
        if r.status_code != 200:
            print(f'    详情页请求失败: {r.status_code}')
            return book

        soup = BeautifulSoup(r.text, 'html.parser')

        # 1. 内容简介
        intro_div = soup.select_one('#link-report .intro')
        if intro_div:
            paragraphs = intro_div.find_all('p')
            description = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            book['description'] = description

        # 2. 豆瓣成员常用标签，合并到已有标签列表
        existing_tags = set(book.get('tags', []))
        tag_section = soup.select_one('#db-tags-section')
        if tag_section:
            for a in tag_section.select('.tag a, a.tag'):
                tag_text = a.get_text(strip=True)
                if tag_text:
                    existing_tags.add(tag_text)

        book['tags'] = list(existing_tags)

    except Exception as e:
        print(f'    详情页爬取出错: {e}')

    return book


def crawl_chart(target=50):
    """爬取豆瓣读书排行榜 + 每本书的详情"""
    print('=' * 60)
    print('豆瓣读书排行榜爬虫')
    print(f'目标: 爬取前 {target} 本书（含详情页）')
    print('=' * 60)

    all_books = []
    page = 1
    base_url = 'https://book.douban.com/chart'

    while len(all_books) < target:
        if page == 1:
            url = f'{base_url}?subcat=all&icn=index-topchart-popular'
        else:
            url = f'{base_url}?subcat=all&p={page}&updated_at=2026-06-01'

        print(f'\n正在爬取第 {page} 页: {url}')
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.encoding = 'utf-8'
            if r.status_code != 200:
                print(f'  请求失败，状态码: {r.status_code}')
                break

            soup = BeautifulSoup(r.text, 'html.parser')
            items = soup.select('.chart-dashed-list li')
            if not items:
                print('  未找到书籍数据，停止爬取')
                break

            new_count = 0
            for li in items:
                if len(all_books) >= target:
                    break
                book = parse_book_item(li)
                if book:
                    all_books.append(book)
                    new_count += 1

            print(f'  本页获取 {new_count} 本书 (累计: {len(all_books)})')
            if new_count == 0:
                break
            page += 1
            time.sleep(1)
        except Exception as e:
            print(f'  爬取出错: {e}')
            break

    # 爬取每本书的详情页
    print(f'\n{"=" * 60}')
    print(f'排行榜爬取完成，共 {len(all_books)} 本。开始爬取详情页...')
    print('=' * 60)

    for i, book in enumerate(all_books):
        print(f'  [{i+1}/{len(all_books)}] {book["title"][:30]}')
        crawl_book_detail(book)
        time.sleep(0.8)

    print(f'\n{"=" * 60}')
    print(f'全部爬取完成！共 {len(all_books)} 本书')
    print('=' * 60)
    return all_books


def main():
    books = crawl_chart(target=50)
    if books:
        init_database()
        save_books_to_db(books)

        print('\n--- 前5本书预览 ---')
        for b in books[:5]:
            print(f'{b["rank"]:>2}. {b["title"]}')
            print(f'    作者: {b["author"]}  评分: {b["rating"]}')
            print(f'    标签: {",".join(b.get("tags", []))}')
            desc = b.get('description', '')
            print(f'    简介: {desc[:60]}...' if len(desc) > 60 else f'    简介: {desc}')


if __name__ == '__main__':
    main()
