const API_BASE_URL = 'http://localhost:5001';

let currentBook = null;
let favorites = [];

document.addEventListener('DOMContentLoaded', function() {
    checkLogin();
    
    document.getElementById('username').textContent = localStorage.getItem('username') || '用户';
    
    const navBtns = document.querySelectorAll('.nav-btn');
    navBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });
    
    loadBooks();
    loadFavorites();
});

function checkLogin() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html';
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('username');
    window.location.href = 'index.html';
}

function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab-content');
    const btns = document.querySelectorAll('.nav-btn');
    
    tabs.forEach(tab => tab.classList.remove('active'));
    btns.forEach(btn => btn.classList.remove('active'));
    
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    if (tabName === 'favorites') {
        renderFavorites();
    }
}

async function loadBooks() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/books`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            document.getElementById('totalBooks').textContent = data.total;
            renderBooks(data.books, 'booksGrid');
        }
    } catch (error) {
        console.error('加载书籍失败:', error);
    }
}

function renderBooks(books, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    if (books.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#999;padding:40px;">暂无书籍</p>';
        return;
    }
    
    books.forEach(book => {
        const isFavorited = favorites.includes(book.id);
        const card = createBookCard(book, isFavorited);
        container.appendChild(card);
    });
}

function createBookCard(book, isFavorited) {
    const card = document.createElement('div');
    card.className = 'book-card';
    card.onclick = () => showBookDetail(book);
    
    const tags = book.tags ? book.tags.split(',').slice(0, 3) : [];
    
    card.innerHTML = `
        <div class="book-cover">
            <i class="fas fa-book"></i>
            <span class="favorite-badge${isFavorited ? ' favorited' : ''}" onclick="event.stopPropagation(); toggleFavoriteCard(${book.id})">
                <i class="fas fa-heart${isFavorited ? '' : '-o'}"></i>
            </span>
        </div>
        <div class="book-info">
            <h3 class="book-title">${book.name}</h3>
            <p class="book-author">${book.author}</p>
            <div class="book-tags">
                ${tags.map(tag => `<span class="tag">${tag.trim()}</span>`).join('')}
            </div>
            <span class="book-status ${book.status === '连载' ? 'serializing' : 'completed'}">${book.status}</span>
        </div>
    `;
    
    return card;
}

async function showBookDetail(book) {
    currentBook = book;
    const isFavorited = favorites.includes(book.id);
    
    document.getElementById('modalTitle').textContent = book.name;
    document.getElementById('modalAuthor').textContent = book.author;
    document.getElementById('modalStatus').textContent = book.status;
    document.getElementById('modalStatus').className = `status ${book.status === '连载' ? 'serializing' : 'completed'}`;
    
    const tags = book.tags ? book.tags.split(',').map(tag => `<span class="tag">${tag.trim()}</span>`).join('') : '';
    document.getElementById('modalTags').innerHTML = tags;
    
    document.getElementById('modalIntro').textContent = book.intro || '暂无简介';
    
    const favBtn = document.getElementById('favoriteBtn');
    if (isFavorited) {
        favBtn.classList.add('favorited');
        favBtn.innerHTML = '<i class="fas fa-heart"></i><span>已收藏</span>';
    } else {
        favBtn.classList.remove('favorited');
        favBtn.innerHTML = '<i class="fas fa-heart"></i><span>收藏</span>';
    }
    
    document.getElementById('bookModal').classList.add('show');
}

function closeModal() {
    document.getElementById('bookModal').classList.remove('show');
    currentBook = null;
}

async function toggleFavorite() {
    if (!currentBook) return;
    
    const isFavorited = favorites.includes(currentBook.id);
    
    try {
        const token = localStorage.getItem('token');
        const url = `${API_BASE_URL}/api/favorites/${currentBook.id}`;
        
        if (isFavorited) {
            await fetch(url, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            favorites = favorites.filter(id => id !== currentBook.id);
        } else {
            await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            favorites.push(currentBook.id);
        }
        
        const favBtn = document.getElementById('favoriteBtn');
        if (favorites.includes(currentBook.id)) {
            favBtn.classList.add('favorited');
            favBtn.innerHTML = '<i class="fas fa-heart"></i><span>已收藏</span>';
        } else {
            favBtn.classList.remove('favorited');
            favBtn.innerHTML = '<i class="fas fa-heart"></i><span>收藏</span>';
        }
        
        updateFavCount();
        refreshFavoriteBadge(currentBook.id);
    } catch (error) {
        console.error('操作失败:', error);
    }
}

async function toggleFavoriteCard(bookId) {
    const isFavorited = favorites.includes(bookId);
    
    try {
        const token = localStorage.getItem('token');
        const url = `${API_BASE_URL}/api/favorites/${bookId}`;
        
        if (isFavorited) {
            await fetch(url, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            favorites = favorites.filter(id => id !== bookId);
        } else {
            await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            favorites.push(bookId);
        }
        
        updateFavCount();
        refreshFavoriteBadge(bookId);
        
        if (document.getElementById('favorites').classList.contains('active')) {
            loadFavorites();
        }
    } catch (error) {
        console.error('操作失败:', error);
    }
}

function refreshFavoriteBadge(bookId) {
    const badges = document.querySelectorAll('.favorite-badge');
    badges.forEach(badge => {
        const card = badge.closest('.book-card');
        if (card) {
            const bookName = card.querySelector('.book-title').textContent;
            const book = [...document.querySelectorAll('.book-card')].find(c => 
                c.querySelector('.book-title').textContent === bookName
            );
            if (book) {
                const isFavorited = favorites.includes(bookId);
                const badgeEl = book.querySelector('.favorite-badge');
                const icon = book.querySelector('.favorite-badge i');
                
                if (isFavorited) {
                    badgeEl.classList.add('favorited');
                    icon.classList.remove('fa-heart-o');
                    icon.classList.add('fa-heart');
                } else {
                    badgeEl.classList.remove('favorited');
                    icon.classList.remove('fa-heart');
                    icon.classList.add('fa-heart-o');
                }
            }
        }
    });
}

async function loadFavorites() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/favorites`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            favorites = data.map(f => f.book_id);
            updateFavCount();
        }
    } catch (error) {
        console.error('加载收藏失败:', error);
    }
}

function updateFavCount() {
    document.getElementById('favCount').textContent = favorites.length;
}

function renderFavorites() {
    if (favorites.length === 0) {
        document.getElementById('favoritesGrid').style.display = 'none';
        document.getElementById('emptyFavorites').style.display = 'block';
        return;
    }
    
    document.getElementById('emptyFavorites').style.display = 'none';
    document.getElementById('favoritesGrid').style.display = 'grid';
    
    loadBooksToFavorites();
}

async function loadBooksToFavorites() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/favorites`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const bookIds = data.map(f => f.book_id);
            
            const booksResponse = await fetch(`${API_BASE_URL}/api/books`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (booksResponse.ok) {
                const booksData = await booksResponse.json();
                const favoriteBooks = booksData.books.filter(book => bookIds.includes(book.id));
                renderBooks(favoriteBooks, 'favoritesGrid');
            }
        }
    } catch (error) {
        console.error('加载收藏书籍失败:', error);
    }
}

function searchBooks() {
    const keyword = document.getElementById('searchInput').value;
    const status = document.getElementById('statusFilter').value;
    
    if (!keyword && !status) {
        loadBooks();
        return;
    }
    
    fetchBooks(keyword, status);
}

async function fetchBooks(keyword = '', status = '') {
    try {
        const token = localStorage.getItem('token');
        let url = `${API_BASE_URL}/api/books/search?`;
        
        if (keyword) url += `keyword=${encodeURIComponent(keyword)}&`;
        if (status) url += `status=${encodeURIComponent(status)}&`;
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            renderBooks(data.books, 'booksGrid');
        }
    } catch (error) {
        console.error('搜索失败:', error);
    }
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});

document.getElementById('bookModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});