# -*- coding: utf-8 -*-
"""共享数据库配置模块 - 优先从环境变量读取，否则交互式输入"""

import os
import getpass


def get_db_config(database='qidian_rank'):
    """获取数据库配置，返回配置字典。优先从环境变量读取。"""
    host = os.environ.get('DB_HOST')
    port = os.environ.get('DB_PORT')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    db = os.environ.get('DB_NAME')

    if host and user and password:
        return {
            'host': host or 'localhost',
            'port': int(port) if port else 3306,
            'user': user,
            'password': password,
            'database': db or database,
            'charset': 'utf8mb4',
        }

    print("=== 数据库连接配置 ===")
    host = input("数据库主机 [localhost]: ").strip() or 'localhost'
    port_input = input("数据库端口 [3306]: ").strip()
    port = int(port_input) if port_input else 3306
    user = input("数据库用户名 [root]: ").strip() or 'root'
    password = getpass.getpass("数据库密码: ")
    db = input(f"数据库名 [{database}]: ").strip() or 'qidian_rank'

    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': db,
        'charset': 'utf8mb4',
    }
