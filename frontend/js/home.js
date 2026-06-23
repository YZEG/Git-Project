const API_BASE_URL = 'http://localhost:5001';

let currentBook = null;
let favorites = [];
let selectedTagsList = [];

document.addEventListener('DOMContentLoaded', function() {
    checkLogin();
    
    document.getElementById('username').textContent = localStorage.getItem('username') || '用户';
    
    const navBtns = document.querySelectorAll('.nav-btn');
    navBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });
    
    document.getElementById('tagInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTagFromInput();
        }
    });
    
    initPage();
});

function initPage() {
    loadBooks();
    loadFavorites().then(() => {
        refreshFavoriteBadgeForAll();
    });
    setTimeout(() => {
        loadHotTags();
    }, 500);
}

function refreshFavoriteBadgeForAll() {
    const cards = document.querySelectorAll('.book-card');
    cards.forEach(card => {
        const titleElement = card.querySelector('.book-title');
        if (!titleElement) return;
        
        const currentBookId = parseInt(titleElement.dataset.bookId);
        if (isNaN(currentBookId)) return;
        
        const badgeEl = card.querySelector('.favorite-badge');
        const icon = card.querySelector('.favorite-badge i');
        if (!badgeEl || !icon) return;
        
        const isFavorited = favorites.includes(currentBookId);
        
        if (isFavorited) {
            badgeEl.classList.add('favorited');
            icon.classList.remove('fa-heart-o');
            icon.classList.add('fa-heart');
        } else {
            badgeEl.classList.remove('favorited');
            icon.classList.remove('fa-heart');
            icon.classList.add('fa-heart-o');
        }
    });
    updateFavCount();
}

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
            <h3 class="book-title" data-book-id="${book.id}">${book.name}</h3>
            <p class="book-author">${book.author}</p>
            <div class="book-tags">
                ${tags.map(tag => `<span class="tag">${tag.trim()}</span>`).join('')}
            </div>
            <span class="book-status ${book.status === '连载' ? 'serializing' : 'completed'}">${book.status}</span>
        </div>
    `;
    
    const titleElement = card.querySelector('.book-title');
    titleElement.onclick = (e) => {
        e.stopPropagation();
        showBookDetail(book);
    };
    
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
    const cards = document.querySelectorAll('.book-card');
    cards.forEach(card => {
        const titleElement = card.querySelector('.book-title');
        const currentBookId = parseInt(titleElement.dataset.bookId);
        const badgeEl = card.querySelector('.favorite-badge');
        const icon = card.querySelector('.favorite-badge i');
        
        const isFavorited = favorites.includes(currentBookId);
        
        if (isFavorited) {
            badgeEl.classList.add('favorited');
            icon.classList.remove('fa-heart-o');
            icon.classList.add('fa-heart');
        } else {
            badgeEl.classList.remove('favorited');
            icon.classList.remove('fa-heart');
            icon.classList.add('fa-heart-o');
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
        document.getElementById('searchResults').innerHTML = '<p style="text-align:center;color:#999;padding:40px;">请输入搜索关键词</p>';
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
            renderBooks(data.books, 'searchResults');
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
    if (e.target.classList.contains('modal-overlay')) {
        closeModal();
    }
});

async function loadHotTags() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/tags/hot?limit=20`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            renderHotTags(data.tags);
        }
    } catch (error) {
        console.error('加载热门标签失败:', error);
    }
}

function renderHotTags(tags) {
    const container = document.getElementById('hotTagsList');
    container.innerHTML = '';

    tags.forEach(tag => {
        const tagEl = document.createElement('span');
        tagEl.className = 'hot-tag';
        tagEl.innerHTML = `${tag.name} <span class="tag-count">${tag.count}</span>`;
        tagEl.onclick = () => selectTag(tag.name);
        container.appendChild(tagEl);
    });

    // Also render in sidebar
    const sidebarContainer = document.getElementById('sidebarTags');
    if (sidebarContainer) {
        sidebarContainer.innerHTML = '';
        tags.slice(0, 10).forEach(tag => {
            const tagEl = document.createElement('span');
            tagEl.className = 'sidebar-tag';
            tagEl.textContent = tag.name;
            tagEl.onclick = () => selectTag(tag.name);
            sidebarContainer.appendChild(tagEl);
        });
    }
}

function addTagFromInput() {
    const input = document.getElementById('tagInput');
    const tag = input.value.trim();
    if (tag) {
        selectTag(tag);
        input.value = '';
    }
}

function selectTag(tagName) {
    if (selectedTagsList.includes(tagName)) {
        return;
    }
    selectedTagsList.push(tagName);
    renderSelectedTags();
}

function removeTag(tagName) {
    selectedTagsList = selectedTagsList.filter(t => t !== tagName);
    renderSelectedTags();
}

function renderSelectedTags() {
    const container = document.getElementById('selectedTags');
    container.innerHTML = '';
    
    if (selectedTagsList.length === 0) {
        container.innerHTML = '<span class="no-tag-tip">请选择或输入您感兴趣的小说类别</span>';
        return;
    }
    
    selectedTagsList.forEach(tag => {
        const tagEl = document.createElement('span');
        tagEl.className = 'selected-tag';
        tagEl.innerHTML = `${tag} <span class="remove-tag-btn" onclick="removeTag('${tag}')">&times;</span>`;
        container.appendChild(tagEl);
    });
}

async function recommendByTags() {
    if (selectedTagsList.length === 0) {
        alert('请至少选择一个标签');
        return;
    }
    
    const tagsStr = selectedTagsList.join(',');
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/recommend/tags?tags=${encodeURIComponent(tagsStr)}&limit=20`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            document.getElementById('recommendSubtitle').textContent = `根据您选择的"${selectedTagsList.join('、')}"，为您找到 ${data.total} 本相关小说`;
            document.getElementById('recommendResults').style.display = 'block';
            
            if (data.books && data.books.length > 0) {
                const booksWithMatch = data.books.map(book => {
                    return {
                        ...book,
                        showMatchScore: true
                    };
                });
                renderRecommendBooks(booksWithMatch, 'recommendGrid');
            } else {
                document.getElementById('recommendGrid').innerHTML = '<p style="text-align:center;color:#999;padding:40px;">没有找到匹配的小说，请尝试其他标签</p>';
            }
        }
    } catch (error) {
        console.error('推荐失败:', error);
        alert('推荐请求失败，请重试');
    }
}

function renderRecommendBooks(books, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    if (books.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#999;padding:40px;">暂无推荐书籍</p>';
        return;
    }
    
    books.forEach(book => {
        const isFavorited = favorites.includes(book.id);
        const card = createRecommendCard(book, isFavorited);
        container.appendChild(card);
    });
}

function createRecommendCard(book, isFavorited) {
    const card = document.createElement('div');
    card.className = 'book-card recommend-card';
    card.onclick = () => showBookDetail(book);
    
    const tags = book.tags ? book.tags.split(',').slice(0, 3) : [];
    const matchTags = book.matched_tags || [];
    
    card.innerHTML = `
        <div class="book-cover">
            <i class="fas fa-book"></i>
            <span class="favorite-badge${isFavorited ? ' favorited' : ''}" onclick="event.stopPropagation(); toggleFavoriteCard(${book.id})">
                <i class="fas fa-heart${isFavorited ? '' : '-o'}"></i>
            </span>
            ${book.showMatchScore ? `<span class="match-score-badge"><i class="fas fa-star"></i> 匹配度 ${Math.min(100, Math.round(book.match_score * 10))}%</span>` : ''}
        </div>
        <div class="book-info">
            <h3 class="book-title" data-book-id="${book.id}">${book.name}</h3>
            <p class="book-author">${book.author}</p>
            <div class="book-tags">
                ${tags.map(tag => {
                    const isMatched = matchTags.includes(tag.trim());
                    return `<span class="tag${isMatched ? ' matched-tag' : ''}">${tag.trim()}</span>`;
                }).join('')}
            </div>
            <span class="book-status ${book.status === '连载' ? 'serializing' : 'completed'}">${book.status}</span>
        </div>
    `;
    
    const titleElement = card.querySelector('.book-title');
    titleElement.onclick = (e) => {
        e.stopPropagation();
        showBookDetail(book);
    };
    
    return card;
}

renderSelectedTags();