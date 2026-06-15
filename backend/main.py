# -*- coding: utf-8 -*-
"""
书籍管理系统 - FastAPI后端服务

功能说明：
- 提供书籍的增删改查(CRUD)接口
- 支持用户登录认证(JWT)
- 提供登录页面和书籍管理页面

API接口：
- GET / - 登录页面
- GET /books - 书籍管理页面
- POST /api/login - 用户登录
- GET /api/books - 获取书籍列表（支持分页）
- GET /api/books/search - 搜索书籍
- GET /api/books/{book_id} - 获取单本书籍
- POST /api/books - 创建新书籍
- PUT /api/books/{book_id} - 更新书籍
- DELETE /api/books/{book_id} - 删除书籍
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse

from pydantic import BaseModel
import pymysql
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os
from fastapi.middleware.cors import CORSMiddleware

# 获取脚本所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# JWT配置
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'HYZ666@',
    'database': 'qidian_rank',
    'charset': 'utf8mb4',
}

# 创建FastAPI应用
app = FastAPI(
    title="书籍管理系统",
    description="基于FastAPI的书籍CRUD管理系统",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载前端静态文件服务
frontend_dir = os.path.join(os.path.dirname(BASE_DIR), "frontend")
app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")

# 首页路由 - 返回登录页面
@app.get("/", response_class=HTMLResponse, summary="首页")
async def index():
    index_path = os.path.join(frontend_dir, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# 用户首页路由
@app.get("/home", response_class=HTMLResponse, summary="用户首页")
async def home_page():
    home_path = os.path.join(frontend_dir, "home.html")
    with open(home_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# 管理员后台路由
@app.get("/admin", response_class=HTMLResponse, summary="管理员后台")
async def admin_page():
    admin_path = os.path.join(frontend_dir, "admin.html")
    with open(admin_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# 重定向规则 - 处理 .html 后缀
@app.get("/home.html", response_class=RedirectResponse)
async def home_html_redirect():
    return RedirectResponse(url="/home")

@app.get("/admin.html", response_class=RedirectResponse)
async def admin_html_redirect():
    return RedirectResponse(url="/admin")

@app.get("/index.html", response_class=RedirectResponse)
async def index_html_redirect():
    return RedirectResponse(url="/")

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# 模拟用户数据库（直接存储明文密码用于演示）
fake_users_db = {
    "admin": {
        "username": "admin",
        "password": "123456",
        "disabled": False,
    }
}

# 书籍数据模型
class BookCreate(BaseModel):
    name: str
    author: str
    status: str = "连载"
    tags: str | None = None
    intro: str | None = None

class BookResponse(BookCreate):
    model_config = {"from_attributes": True}
    id: int

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    phone: Optional[str] = None
    role: str = "user"

class UserCreate(BaseModel):
    username: str
    phone: Optional[str] = None
    password: str
    role: str = "user"

class UserResponse(User):
    model_config = {"from_attributes": True}
    id: int
    created_at: Optional[datetime] = None

class UserInDB(UserResponse):
    password: str

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(e)}")

def get_user_from_db(username: str):
    """从数据库获取用户"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user:
            return UserInDB(**user)
        return None
    finally:
        conn.close()

def authenticate_user_db(username: str, password: str):
    """从数据库认证用户"""
    user = get_user_from_db(username)
    if not user:
        return False
    if password != user.password:
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_from_db(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    """获取当前活跃用户"""
    return current_user

async def get_current_admin(current_user: UserInDB = Depends(get_current_user)):
    """获取当前管理员用户（仅管理员可访问）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限")
    return current_user

async def get_current_user_or_admin(target_user_id: int = None):
    """获取当前用户（允许用户访问自己的数据或管理员访问所有数据）"""
    async def checker(current_user: UserInDB = Depends(get_current_user)):
        if current_user.role == "admin":
            return current_user
        if target_user_id is not None and current_user.id != target_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此资源")
        return current_user
    return checker

# 登录请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

# 用户登录API
@app.post("/api/login", response_model=Token, summary="用户登录")
async def login(login_data: LoginRequest):
    """用户登录，返回JWT令牌（仅管理员可登录）"""
    user = authenticate_user_db(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

# 获取所有书籍（支持分页）
@app.get("/api/books", response_model=dict, summary="获取书籍列表")
async def get_books(page: int = 1, page_size: int = 10, current_user: User = Depends(get_current_active_user)):
    """获取书籍列表（支持分页）"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取总记录数
        cursor.execute("SELECT COUNT(*) as total FROM books")
        total = cursor.fetchone()["total"]
        
        # 计算分页参数
        offset = (page - 1) * page_size
        
        # 获取当前页数据
        cursor.execute("SELECT * FROM books ORDER BY id LIMIT %s OFFSET %s", (page_size, offset))
        books = cursor.fetchall()
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        return {"books": books, "total": total, "total_pages": total_pages, "current_page": page}
    finally:
        conn.close()

# 搜索书籍（支持多条件）
@app.get("/api/books/search", response_model=dict, summary="搜索书籍")
async def search_books(
    keyword: str = None,
    name: str = None,
    author: str = None,
    status: str = None,
    tag: str = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "id",
    sort_order: str = "asc",
    current_user: User = Depends(get_current_active_user)
):
    """
    根据多条件搜索书籍
    
    参数：
    - keyword: 关键词（同时搜索书名、作者、标签、简介）
    - name: 书名（精确匹配）
    - author: 作者（精确匹配）
    - status: 状态（连载/完结）
    - tag: 标签（包含匹配）
    - page: 页码，默认1
    - page_size: 每页数量，默认10
    - sort_by: 排序字段，可选 id/name/author/status，默认id
    - sort_order: 排序顺序，可选 asc/desc，默认asc
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 构建查询条件
        conditions = []
        params = []
        
        # 关键词搜索（模糊匹配书名、作者、标签、简介）
        if keyword and keyword.strip():
            conditions.append("(name LIKE %s OR author LIKE %s OR tags LIKE %s OR intro LIKE %s)")
            keyword_pattern = f"%{keyword.strip()}%"
            params.extend([keyword_pattern, keyword_pattern, keyword_pattern, keyword_pattern])
        
        # 书名精确搜索
        if name and name.strip():
            conditions.append("name = %s")
            params.append(name.strip())
        
        # 作者模糊搜索
        if author and author.strip():
            conditions.append("author LIKE %s")
            params.append(f"%{author.strip()}%")
        
        # 状态筛选
        if status and status.strip() and status.strip() in ["连载", "完结"]:
            conditions.append("status = %s")
            params.append(status.strip())
        
        # 标签包含搜索
        if tag and tag.strip():
            conditions.append("tags LIKE %s")
            params.append(f"%{tag.strip()}%")
        
        # 构建SQL语句
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        else:
            where_clause = ""
        
        # 验证排序字段
        valid_sort_fields = ["id", "name", "author", "status"]
        if sort_by not in valid_sort_fields:
            sort_by = "id"
        
        # 验证排序顺序
        if sort_order not in ["asc", "desc"]:
            sort_order = "asc"
        
        # 先获取总记录数
        count_sql = f"SELECT COUNT(*) as total FROM books {where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()["total"]
        
        # 计算分页参数
        offset = (page - 1) * page_size
        
        # 获取当前页数据
        query_sql = f"""
            SELECT * FROM books {where_clause} 
            ORDER BY {sort_by} {sort_order} 
            LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])
        cursor.execute(query_sql, params)
        books = cursor.fetchall()
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "books": books, 
            "total": total, 
            "total_pages": total_pages, 
            "current_page": page,
            "search_params": {
                "keyword": keyword,
                "name": name,
                "author": author,
                "status": status,
                "tag": tag
            }
        }
    finally:
        conn.close()

# 获取单本书籍
@app.get("/api/books/{book_id}", response_model=BookResponse, summary="获取单本书籍")
async def get_book(book_id: int, current_user: User = Depends(get_current_active_user)):
    """根据ID获取书籍详情"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()
        
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        return book
    finally:
        conn.close()

# 创建新书籍
@app.post("/api/books", response_model=BookResponse, status_code=201, summary="创建新书籍")
async def create_book(book: BookCreate, current_user: UserInDB = Depends(get_current_admin)):
    """创建一本新书籍"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 检查书籍是否已存在
        cursor.execute("SELECT id FROM books WHERE name = %s", (book.name,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="书籍已存在")
        
        # 插入新书籍
        cursor.execute(
            "INSERT INTO books (name, author, status, tags, intro) VALUES (%s, %s, %s, %s, %s)",
            (book.name, book.author, book.status, book.tags, book.intro)
        )
        conn.commit()
        
        # 获取新插入书籍的ID
        book_id = cursor.lastrowid
        
        # 返回创建的书籍信息
        cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        new_book = cursor.fetchone()
        
        return new_book
    finally:
        conn.close()

# 更新书籍信息
@app.put("/api/books/{book_id}", response_model=BookResponse, summary="更新书籍信息")
async def update_book(book_id: int, book: BookCreate, current_user: UserInDB = Depends(get_current_admin)):
    """更新指定书籍的信息"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 检查书籍是否存在
        cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        existing_book = cursor.fetchone()
        
        if not existing_book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 更新书籍信息
        cursor.execute(
            "UPDATE books SET name = %s, author = %s, status = %s, tags = %s, intro = %s WHERE id = %s",
            (book.name, book.author, book.status, book.tags, book.intro, book_id)
        )
        conn.commit()
        
        # 返回更新后的书籍信息
        cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        updated_book = cursor.fetchone()
        
        return updated_book
    finally:
        conn.close()

# 删除书籍
@app.delete("/api/books/{book_id}", status_code=204, summary="删除书籍")
async def delete_book(book_id: int, current_user: UserInDB = Depends(get_current_admin)):
    """删除指定书籍"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 检查书籍是否存在
        cursor.execute("SELECT id FROM books WHERE id = %s", (book_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 删除书籍
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()
        
        return None
    finally:
        conn.close()

# 用户管理API

@app.get("/api/users", response_model=dict, summary="获取用户列表")
async def get_users(
    page: int = 1, 
    page_size: int = 10, 
    current_user: UserInDB = Depends(get_current_admin)
):
    """获取用户列表（支持分页）"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total = cursor.fetchone()["total"]
        
        offset = (page - 1) * page_size
        
        cursor.execute("SELECT id, username, phone, role, created_at FROM users ORDER BY id LIMIT %s OFFSET %s", (page_size, offset))
        users = cursor.fetchall()
        
        total_pages = (total + page_size - 1) // page_size
        
        return {"users": users, "total": total, "total_pages": total_pages, "current_page": page}
    finally:
        conn.close()

@app.get("/api/users/{user_id}", response_model=UserResponse, summary="获取单个用户")
async def get_user(user_id: int, current_user: UserInDB = Depends(get_current_admin)):
    """根据ID获取用户详情"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id, username, phone, role, created_at FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return user
    finally:
        conn.close()

@app.post("/api/users", response_model=UserResponse, status_code=201, summary="创建用户")
async def create_user(user: UserCreate, current_user: UserInDB = Depends(get_current_admin)):
    """创建新用户"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        if user.phone:
            cursor.execute("SELECT id FROM users WHERE phone = %s", (user.phone,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="手机号已被使用")
        
        if user.role not in ["admin", "user"]:
            raise HTTPException(status_code=400, detail="无效的角色类型")
        
        cursor.execute(
            "INSERT INTO users (username, phone, password, role) VALUES (%s, %s, %s, %s)",
            (user.username, user.phone, user.password, user.role)
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        
        cursor.execute("SELECT id, username, phone, role, created_at FROM users WHERE id = %s", (user_id,))
        new_user = cursor.fetchone()
        
        return new_user
    finally:
        conn.close()

@app.put("/api/users/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(user_id: int, user: UserCreate, current_user: UserInDB = Depends(get_current_admin)):
    """更新用户信息"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        existing_user = cursor.fetchone()
        
        if not existing_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        if user.username != existing_user['username']:
            cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (user.username, user_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="用户名已存在")
        
        if user.phone and user.phone != existing_user['phone']:
            cursor.execute("SELECT id FROM users WHERE phone = %s AND id != %s", (user.phone, user_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="手机号已被使用")
        
        if user.role not in ["admin", "user"]:
            raise HTTPException(status_code=400, detail="无效的角色类型")
        
        if user.password == '******':
            cursor.execute(
                "UPDATE users SET username = %s, phone = %s, role = %s WHERE id = %s",
                (user.username, user.phone, user.role, user_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET username = %s, phone = %s, password = %s, role = %s WHERE id = %s",
                (user.username, user.phone, user.password, user.role, user_id)
            )
        conn.commit()
        
        cursor.execute("SELECT id, username, phone, role, created_at FROM users WHERE id = %s", (user_id,))
        updated_user = cursor.fetchone()
        
        return updated_user
    finally:
        conn.close()

@app.delete("/api/users/{user_id}", status_code=204, summary="删除用户")
async def delete_user(user_id: int, current_user: UserInDB = Depends(get_current_admin)):
    """删除用户"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="用户不存在")
        
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        
        return None
    finally:
        conn.close()

# 用户收藏书籍API

# 简化的用户收藏API（用户操作自己的收藏）
@app.get("/api/favorites", summary="获取当前用户收藏")
async def get_my_favorites(current_user: UserInDB = Depends(get_current_user)):
    """获取当前登录用户的收藏书籍"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT book_id FROM user_favorites WHERE user_id = %s", (current_user.id,))
        results = cursor.fetchall()
        return [{"book_id": r["book_id"]} for r in results]
    finally:
        conn.close()

@app.post("/api/favorites/{book_id}", status_code=204, summary="添加收藏")
async def add_my_favorite(book_id: int, current_user: UserInDB = Depends(get_current_user)):
    """当前用户添加收藏书籍"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM books WHERE id = %s", (book_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        try:
            cursor.execute("INSERT INTO user_favorites (user_id, book_id) VALUES (%s, %s)", (current_user.id, book_id))
            conn.commit()
        except pymysql.IntegrityError:
            raise HTTPException(status_code=400, detail="该书籍已被收藏")
        
        return None
    finally:
        conn.close()

@app.delete("/api/favorites/{book_id}", status_code=204, summary="取消收藏")
async def remove_my_favorite(book_id: int, current_user: UserInDB = Depends(get_current_user)):
    """当前用户取消收藏书籍"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM user_favorites WHERE user_id = %s AND book_id = %s", (current_user.id, book_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="收藏记录不存在")
        
        return None
    finally:
        conn.close()

@app.get("/api/users/{user_id}/favorites", response_model=dict, summary="获取用户收藏")
async def get_user_favorites(
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    current_user: UserInDB = Depends(get_current_user)
):
    """获取用户收藏的书籍（用户可查看自己的收藏，管理员可查看所有）"""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此资源")
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT COUNT(*) as total FROM user_favorites WHERE user_id = %s", (user_id,))
        total = cursor.fetchone()["total"]
        
        offset = (page - 1) * page_size
        
        cursor.execute("""
            SELECT b.* FROM user_favorites f
            JOIN books b ON f.book_id = b.id
            WHERE f.user_id = %s
            ORDER BY f.created_at DESC
            LIMIT %s OFFSET %s
        """, (user_id, page_size, offset))
        books = cursor.fetchall()
        
        total_pages = (total + page_size - 1) // page_size
        
        return {"books": books, "total": total, "total_pages": total_pages, "current_page": page}
    finally:
        conn.close()

@app.post("/api/users/{user_id}/favorites/{book_id}", status_code=204, summary="添加收藏")
async def add_favorite(
    user_id: int,
    book_id: int,
    current_user: UserInDB = Depends(get_current_user)
):
    """为用户添加收藏书籍（用户可收藏自己的书籍，管理员可管理所有）"""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此资源")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="用户不存在")
        
        cursor.execute("SELECT id FROM books WHERE id = %s", (book_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        try:
            cursor.execute("INSERT INTO user_favorites (user_id, book_id) VALUES (%s, %s)", (user_id, book_id))
            conn.commit()
        except pymysql.IntegrityError:
            raise HTTPException(status_code=400, detail="该书籍已被收藏")
        
        return None
    finally:
        conn.close()

@app.delete("/api/users/{user_id}/favorites/{book_id}", status_code=204, summary="取消收藏")
async def remove_favorite(
    user_id: int,
    book_id: int,
    current_user: UserInDB = Depends(get_current_user)
):
    """取消用户对书籍的收藏（用户可取消自己的收藏，管理员可管理所有）"""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此资源")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM user_favorites WHERE user_id = %s AND book_id = %s", (user_id, book_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="收藏记录不存在")
        
        return None
    finally:
        conn.close()

# 健康检查接口
@app.get("/api/health", summary="健康检查")
async def health_check():
    """检查服务是否正常运行"""
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def release_port(port):
    """检测并释放指定端口"""
    import subprocess
    import re
    
    try:
        result = subprocess.run(
            ["netstat", "-ano", "|", "findstr", f":{port}"],
            capture_output=True,
            text=True,
            shell=True
        )
        output = result.stdout
        
        pids = re.findall(r'LISTENING\s+(\d+)', output)
        if pids:
            for pid in pids:
                try:
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                    print(f"已释放端口 {port}，终止进程 PID: {pid}")
                except Exception as e:
                    print(f"终止进程 {pid} 失败: {e}")
    except Exception as e:
        print(f"检测端口 {port} 状态时出错: {e}")

if __name__ == "__main__":
    import uvicorn
    
    PORT = 5001
    release_port(PORT)
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)