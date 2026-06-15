# 📚 书籍管理系统

一个基于 FastAPI 后端和现代前端技术的完整书籍管理平台，支持书籍的增删改查、用户认证、收藏管理等功能。

## ✨ 核心功能

### 📖 书籍管理
- ✅ 书籍的增删改查（CRUD）操作
- ✅ 多条件搜索和过滤
- ✅ 支持书籍分页展示
- ✅ 书籍标签和简介管理

### 👥 用户管理
- ✅ JWT 令牌认证
- ✅ 用户角色管理（管理员/普通用户）
- ✅ 用户创建和权限控制

### ❤️ 收藏功能
- ✅ 用户可收藏喜爱的书籍
- ✅ 收藏列表分页展示
- ✅ 快速取消收藏

### 🕷️ 数据爬取
- ✅ 起点中文网月票排行榜爬虫
- ✅ 自动获取书籍信息和真实状态
- ✅ 数据库自动初始化和更新

## 🏗️ 项目结构

```
Git-Project/
├── backend/                  # 后端服务
│   ├── main.py              # FastAPI 主应用
│   ├── qidian_spider.py      # 起点爬虫脚本
│   ├── init_db.py           # 数据库初始化
│   ├── create_admin.py      # 管理员创建脚本
│   ├── check_table.py       # 数据表检查脚本
│   └── recreate_users_table.py # 用户表重建脚本
│
├── frontend/                 # 前端页面
│   ├── index.html           # 登录页面
│   ├── home.html            # 首页
│   ├── admin.html           # 管理面板
│   ├── css/                 # 样式文件
│   └── js/                  # 脚本文件
│
└── README.md                # 项目说明
```

## 🛠️ 技术栈

| 分类 | 技术 | 占比 |
|-----|------|------|
| **后端** | Python (FastAPI) | 35.9% |
| **前端** | JavaScript | 29.9% |
| **样式** | CSS | 19.3% |
| **标记** | HTML | 14.9% |
| **数据库** | MySQL | - |
| **认证** | JWT | - |

## 🚀 快速开始

### 前置要求
- Python 3.8+
- MySQL 5.7+
- pip

### 安装依赖

```bash
# 后端依赖
pip install fastapi uvicorn pydantic pymysql python-jose passlib

# 爬虫依赖
pip install requests
```

### 数据库配置

1. 启动 MySQL 服务

2. 修改后端配置文件中的数据库连接信息：
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '你的密码',
    'database': 'qidian_rank',
    'charset': 'utf8mb4',
}
```

3. 初始化数据库：
```bash
cd backend
python init_db.py      # 初始化数据库
python create_admin.py # 创建管理员账户
python qidian_spider.py # 爬取书籍数据
```

### 启动服务

```bash
# 启动后端服务
cd backend
python main.py
# 服务将在 http://localhost:5001 启动

# 打开前端页面
# 在浏览器中打开 frontend/index.html
# 或配置 HTTP 服务器提供前端资源
```

## 📝 API 文档

### 认证
- `POST /api/login` - 用户登录，获取 JWT 令牌

### 书籍接口
- `GET /api/books` - 获取书籍列表（支持分页）
- `GET /api/books/search` - 搜索书籍（多条件）
- `GET /api/books/{book_id}` - 获取书籍详情
- `POST /api/books` - 创建新书籍（管理员）
- `PUT /api/books/{book_id}` - 更新书籍（管理员）
- `DELETE /api/books/{book_id}` - 删除书籍（管理员）

### 用户接口
- `GET /api/users` - 获取用户列表（管理员）
- `GET /api/users/{user_id}` - 获取用户详情（管理员）
- `POST /api/users` - 创建用户（管理员）
- `PUT /api/users/{user_id}` - 更新用户（管理员）
- `DELETE /api/users/{user_id}` - 删除用户（管理员）

### 收藏接口
- `GET /api/users/{user_id}/favorites` - 获取用户收藏
- `POST /api/users/{user_id}/favorites/{book_id}` - 添加收藏
- `DELETE /api/users/{user_id}/favorites/{book_id}` - 取消收藏

### 其他
- `GET /api/health` - 服务健康检查

## 🔐 默认账户

| 账户 | 密码 | 角色 |
|-----|------|------|
| admin | 123456 | 管理员 |
| test | 123456 | 普通用户 |

> ⚠️ 生产环境请修改默认密码和 JWT 密钥！

## 📊 数据库架构

### books 表
- id: 书籍ID
- name: 书籍名称
- author: 作者
- status: 状态（连载/完结）
- tags: 标签
- intro: 简介
- created_at: 创建时间

### users 表
- id: 用户ID
- username: 用户名
- phone: 电话
- password: 密码
- role: 角色（admin/user）
- created_at: 创建时间

### user_favorites 表
- id: 收藏ID
- user_id: 用户ID
- book_id: 书籍ID
- created_at: 创建时间

## 🎯 主要功能说明

### 1. 书籍搜索
支持以下搜索条件：
- 关键词（模糊搜索书名、作者、标签、简介）
- 书名（精确匹配）
- 作者（模糊搜索）
- 状态（连载/完结）
- 标签（包含匹配）
- 排序字段和顺序自定义

### 2. 爬虫功能
- 自动爬取起点中文网月票排行榜
- 获取书籍的真实连载状态
- 防止请求过快的速率限制

### 3. 权限管理
- 管理员可进行所有操作
- 普通用户仅可查看和收藏书籍
- 用户只能管理自己的收藏

## 🐛 常见问题

### 数据库连接失败
- 检查 MySQL 服务是否启动
- 验证数据库配置信息是否正确
- 检查数据库用户名和密码

### 爬虫无法获取数据
- 检查网络连接
- 对方网站可能更改了 HTML 结构
- 尝试修改请求头中的 User-Agent

### 登录失败
- 检查用户名和密码是否正确
- 确保用户已在数据库中创建
- 查看后端服务是否正常运行

## 📄 许可证

MIT License

## 👨‍💻 开发者

YZEG

---

**祝你使用愉快！** 📖✨
