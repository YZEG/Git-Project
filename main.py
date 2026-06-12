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
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pymysql
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

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

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

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

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

class UserInDB(User):
    password: str

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(e)}")

def get_user(db, username: str):
    """获取用户"""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    """认证用户"""
    user = get_user(fake_db, username)
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
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """获取当前活跃用户"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="用户已禁用")
    return current_user

# 登录页面
@app.get("/", response_class=HTMLResponse, summary="登录页面")
async def login_page():
    """返回登录页面"""
    with open("templates/login.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# 书籍管理页面
@app.get("/books", response_class=HTMLResponse, summary="书籍管理页面")
async def books_page():
    """返回书籍管理页面"""
    with open("templates/books.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# 登录请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

# 用户登录API
@app.post("/api/login", response_model=Token, summary="用户登录")
async def login(login_data: LoginRequest):
    """用户登录，返回JWT令牌"""
    user = authenticate_user(fake_users_db, login_data.username, login_data.password)
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
    return {"access_token": access_token, "token_type": "bearer"}

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
async def create_book(book: BookCreate, current_user: User = Depends(get_current_active_user)):
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
async def update_book(book_id: int, book: BookCreate, current_user: User = Depends(get_current_active_user)):
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
async def delete_book(book_id: int, current_user: User = Depends(get_current_active_user)):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)