/**
 * Competitor Campaign Tracker - Frontend JavaScript
 * 
 * Story 2.3: Website Display Integration
 * - Displays campaigns in Marriott section
 * - Responsive design
 * - Filter by category
 * - Visual indicators for recent updates
 */

// ==================== Constants ====================
const API_BASE = '/api';
const ITEMS_PER_PAGE = 12;

// ==================== State ====================
let state = {
    campaigns: [],
    categories: [],
    stats: null,
    logs: [],
    currentSection: 'dashboard',
    filters: {
        category: 'all',
        status: 'all',
        search: ''
    },
    pagination: {
        offset: 0,
        total: 0,
        hasMore: false
    },
    isLoading: false
};

// ==================== DOM Elements ====================
const elements = {
    // Navigation
    navItems: document.querySelectorAll('.nav-item'),
    sections: document.querySelectorAll('.content-section'),
    pageTitle: document.getElementById('page-title'),
    pageSubtitle: document.getElementById('page-subtitle'),
    
    // Stats
    totalCampaigns: document.getElementById('total-campaigns'),
    activeCampaigns: document.getElementById('active-campaigns'),
    inactiveCampaigns: document.getElementById('inactive-campaigns'),
    newCampaigns: document.getElementById('new-campaigns'),
    categoryStats: document.getElementById('category-stats'),
    
    // Campaigns
    recentCampaigns: document.getElementById('recent-campaigns'),
    campaignsGrid: document.getElementById('campaigns-grid'),
    loadMoreBtn: document.getElementById('load-more-btn'),
    loadMoreContainer: document.getElementById('load-more-container'),
    
    // Filters
    categoryFilter: document.getElementById('category-filter'),
    statusFilter: document.getElementById('status-filter'),
    searchInput: document.getElementById('search-input'),
    clearFiltersBtn: document.getElementById('clear-filters'),
    
    // Logs
    logsTableBody: document.getElementById('logs-table-body'),
    
    // Actions
    refreshBtn: document.getElementById('refresh-btn'),
    lastUpdated: document.getElementById('last-updated'),
    
    // Modal
    modalOverlay: document.getElementById('modal-overlay'),
    modalTitle: document.getElementById('modal-title'),
    modalBody: document.getElementById('modal-body'),
    modalClose: document.getElementById('modal-close'),
    
    // Toast
    toastContainer: document.getElementById('toast-container')
};

// ==================== API Functions ====================
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'API request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function loadStats() {
    try {
        const response = await fetchAPI('/stats');
        state.stats = response.data;
        renderStats();
    } catch (error) {
        showToast('error', 'Error', 'Failed to load statistics');
    }
}

async function loadCategories() {
    try {
        const response = await fetchAPI('/categories');
        state.categories = response.data;
        renderCategoryFilter();
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

async function loadCampaigns(append = false) {
    if (state.isLoading) return;
    
    state.isLoading = true;
    
    try {
        const params = new URLSearchParams({
            limit: ITEMS_PER_PAGE,
            offset: append ? state.pagination.offset : 0
        });
        
        if (state.filters.category !== 'all') {
            params.append('category', state.filters.category);
        }
        
        if (state.filters.status !== 'all') {
            params.append('is_active', state.filters.status === 'active');
        }
        
        if (state.filters.search) {
            params.append('search', state.filters.search);
        }
        
        const response = await fetchAPI(`/campaigns?${params}`);
        
        if (append) {
            state.campaigns = [...state.campaigns, ...response.data];
        } else {
            state.campaigns = response.data;
        }
        
        state.pagination = {
            offset: (append ? state.pagination.offset : 0) + response.data.length,
            total: response.total,
            hasMore: (append ? state.pagination.offset : 0) + response.data.length < response.total
        };
        
        renderCampaigns();
        renderRecentCampaigns();
    } catch (error) {
        showToast('error', 'Error', 'Failed to load campaigns');
    } finally {
        state.isLoading = false;
    }
}

async function loadLogs() {
    try {
        const response = await fetchAPI('/scrape/logs');
        state.logs = response.data;
        renderLogs();
    } catch (error) {
        showToast('error', 'Error', 'Failed to load scrape logs');
    }
}

async function triggerScrape(useDemo = false) {
    try {
        elements.refreshBtn.disabled = true;
        elements.refreshBtn.classList.add('loading');
        elements.refreshBtn.innerHTML = '<i class="fas fa-spinner"></i><span>Scraping...</span>';
        
        const response = await fetchAPI('/scrape', {
            method: 'POST',
            body: JSON.stringify({ use_demo: useDemo })
        });
        
        showToast(
            'success',
            'Scrape Complete',
            `Found ${response.data.campaigns_found} campaigns, ${response.data.new_campaigns} new`
        );
        
        // Reload data
        await Promise.all([loadStats(), loadCampaigns(), loadLogs()]);
        updateLastUpdated();
        
    } catch (error) {
        showToast('error', 'Scrape Failed', error.message);
    } finally {
        elements.refreshBtn.disabled = false;
        elements.refreshBtn.classList.remove('loading');
        elements.refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i><span>Run Scraper</span>';
    }
}

// ==================== Render Functions ====================
function renderStats() {
    if (!state.stats) return;
    
    elements.totalCampaigns.textContent = state.stats.total_campaigns || 0;
    elements.activeCampaigns.textContent = state.stats.active_campaigns || 0;
    elements.inactiveCampaigns.textContent = state.stats.inactive_campaigns || 0;
    
    // Count campaigns from last 7 days (approximation)
    const newCount = state.campaigns.filter(c => {
        const days = c.days_since_update;
        return days !== null && days <= 7;
    }).length;
    elements.newCampaigns.textContent = newCount;
    
    // Render category breakdown
    if (state.stats.categories) {
        elements.categoryStats.innerHTML = Object.entries(state.stats.categories)
            .map(([category, count]) => `
                <div class="category-item">
                    <div class="category-count">${count}</div>
                    <div class="category-name">${getCategoryLabel(category)}</div>
                </div>
            `).join('');
    }
}

function renderCategoryFilter() {
    elements.categoryFilter.innerHTML = '<option value="all">All Categories</option>' +
        state.categories.map(cat => `
            <option value="${cat}">${getCategoryLabel(cat)}</option>
        `).join('');
}

function renderRecentCampaigns() {
    const recent = state.campaigns.slice(0, 5);
    
    if (recent.length === 0) {
        elements.recentCampaigns.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>No Campaigns Found</h3>
                <p>Click "Run Scraper" to fetch campaign data</p>
            </div>
        `;
        return;
    }
    
    elements.recentCampaigns.innerHTML = recent.map(campaign => `
        <div class="campaign-list-item" data-id="${campaign.id}">
            <div class="campaign-indicator ${campaign.category}"></div>
            <div class="campaign-content">
                <h4>${escapeHtml(campaign.campaign_name)}</h4>
                <p>${escapeHtml(campaign.campaign_info || 'No description available')}</p>
            </div>
            <div class="campaign-meta">
                <span class="campaign-badge ${campaign.is_active ? 'active' : 'inactive'}">
                    ${campaign.is_active ? 'Active' : 'Inactive'}
                </span>
                <span class="campaign-date">${formatDate(campaign.last_seen_date)}</span>
            </div>
        </div>
    `).join('');
    
    // Add click handlers
    elements.recentCampaigns.querySelectorAll('.campaign-list-item').forEach(item => {
        item.addEventListener('click', () => {
            const campaign = state.campaigns.find(c => c.id === parseInt(item.dataset.id));
            if (campaign) openModal(campaign);
        });
    });
}

function renderCampaigns() {
    if (state.campaigns.length === 0) {
        elements.campaignsGrid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <i class="fas fa-search"></i>
                <h3>No Campaigns Found</h3>
                <p>Try adjusting your filters or run the scraper to fetch new data</p>
                <button class="btn btn-primary" onclick="triggerScrape(true)">
                    <i class="fas fa-plus"></i> Load Demo Data
                </button>
            </div>
        `;
        elements.loadMoreContainer.style.display = 'none';
        return;
    }
    
    elements.campaignsGrid.innerHTML = state.campaigns.map(campaign => {
        const updateClass = getUpdateIndicatorClass(campaign.days_since_update);
        
        return `
            <div class="campaign-card ${campaign.category}" data-id="${campaign.id}">
                <div class="update-indicator ${updateClass}" title="${getUpdateTitle(campaign.days_since_update)}"></div>
                <div class="campaign-card-header">
                    <h3>${escapeHtml(campaign.campaign_name)}</h3>
                    <div class="campaign-card-badges">
                        <span class="badge category">${getCategoryLabel(campaign.category)}</span>
                        <span class="badge status-${campaign.is_active ? 'active' : 'inactive'}">
                            ${campaign.is_active ? 'Active' : 'Inactive'}
                        </span>
                        ${campaign.days_since_update <= 1 ? '<span class="badge recent">New</span>' : ''}
                    </div>
                </div>
                <div class="campaign-card-body">
                    <p>${escapeHtml(campaign.campaign_info || 'No description available')}</p>
                </div>
                <div class="campaign-card-footer">
                    <span class="date">
                        <i class="fas fa-calendar-alt"></i>
                        Discovered: ${formatDate(campaign.scraped_date)}
                    </span>
                    <a href="${campaign.source_url}" target="_blank" class="link" onclick="event.stopPropagation();">
                        <i class="fas fa-external-link-alt"></i> Source
                    </a>
                </div>
            </div>
        `;
    }).join('');
    
    // Show/hide load more button
    elements.loadMoreContainer.style.display = state.pagination.hasMore ? 'flex' : 'none';
    
    // Add click handlers
    elements.campaignsGrid.querySelectorAll('.campaign-card').forEach(card => {
        card.addEventListener('click', () => {
            const campaign = state.campaigns.find(c => c.id === parseInt(card.dataset.id));
            if (campaign) openModal(campaign);
        });
    });
}

function renderLogs() {
    if (state.logs.length === 0) {
        elements.logsTableBody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px;">
                    No scrape logs available
                </td>
            </tr>
        `;
        return;
    }
    
    elements.logsTableBody.innerHTML = state.logs.map(log => `
        <tr>
            <td>${formatDateTime(log.scrape_date)}</td>
            <td>${escapeHtml(log.competitor_name)}</td>
            <td>
                <span class="status-badge ${log.status}">${log.status}</span>
            </td>
            <td>${log.campaigns_found}</td>
            <td>${log.new_campaigns}</td>
            <td>${escapeHtml(log.error_message || '-')}</td>
        </tr>
    `).join('');
}

// ==================== UI Functions ====================
function switchSection(sectionId) {
    state.currentSection = sectionId;
    
    // Update nav
    elements.navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.section === sectionId);
    });
    
    // Update sections
    elements.sections.forEach(section => {
        section.classList.toggle('active', section.id === `${sectionId}-section`);
    });
    
    // Update header
    const titles = {
        dashboard: ['Dashboard', 'Overview of competitor marketing campaigns'],
        marriott: ['Marriott Campaigns', 'Current promotions from Marriott China'],
        logs: ['Scrape History', 'View past scraping activity and results']
    };
    
    const [title, subtitle] = titles[sectionId] || ['Dashboard', ''];
    elements.pageTitle.textContent = title;
    elements.pageSubtitle.textContent = subtitle;
    
    // Load section-specific data
    if (sectionId === 'logs') {
        loadLogs();
    }
}

function openModal(campaign) {
    elements.modalTitle.textContent = campaign.campaign_name;
    elements.modalBody.innerHTML = `
        <div class="modal-detail-row">
            <label>Category</label>
            <p><span class="badge category">${getCategoryLabel(campaign.category)}</span></p>
        </div>
        <div class="modal-detail-row">
            <label>Status</label>
            <p>
                <span class="badge status-${campaign.is_active ? 'active' : 'inactive'}">
                    ${campaign.is_active ? 'Active' : 'Inactive'}
                </span>
            </p>
        </div>
        <div class="modal-detail-row">
            <label>Description</label>
            <p>${escapeHtml(campaign.campaign_info || 'No description available')}</p>
        </div>
        <div class="modal-detail-row">
            <label>Source URL</label>
            <p><a href="${campaign.source_url}" target="_blank">${escapeHtml(campaign.source_url)}</a></p>
        </div>
        <div class="modal-detail-row">
            <label>First Discovered</label>
            <p>${formatDateTime(campaign.scraped_date)}</p>
        </div>
        <div class="modal-detail-row">
            <label>Last Seen</label>
            <p>${formatDateTime(campaign.last_seen_date)} (${campaign.days_since_update} days ago)</p>
        </div>
        <div class="modal-detail-row">
            <label>Competitor</label>
            <p>${escapeHtml(campaign.competitor_name)}</p>
        </div>
    `;
    elements.modalOverlay.classList.add('active');
}

function closeModal() {
    elements.modalOverlay.classList.remove('active');
}

function showToast(type, title, message) {
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="${icons[type]}"></i>
        <div class="toast-message">
            <strong>${escapeHtml(title)}</strong>
            <span>${escapeHtml(message)}</span>
        </div>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });
    
    // Remove after delay
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function updateLastUpdated() {
    const now = new Date();
    elements.lastUpdated.querySelector('span').textContent = 
        `Updated: ${now.toLocaleTimeString()}`;
}

// ==================== Helper Functions ====================
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getCategoryLabel(category) {
    const labels = {
        family: '亲子/家庭',
        dining: '餐饮美食',
        seasonal: '季节限定',
        rewards: '会员积分',
        travel: '旅行度假',
        business: '商务出行',
        spa: '水疗养生',
        wedding: '婚礼婚宴',
        promotion: '促销优惠',
        general: '综合'
    };
    return labels[category] || category;
}

function getUpdateIndicatorClass(days) {
    if (days === null || days === undefined) return 'old';
    if (days <= 1) return 'recent';
    if (days <= 7) return 'week';
    return 'old';
}

function getUpdateTitle(days) {
    if (days === null || days === undefined) return 'Unknown';
    if (days <= 1) return 'Updated today';
    if (days <= 7) return 'Updated this week';
    return `Updated ${days} days ago`;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== Event Handlers ====================
function setupEventListeners() {
    // Navigation
    elements.navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchSection(item.dataset.section);
        });
    });
    
    // View All links
    document.querySelectorAll('.view-all').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            switchSection(link.dataset.section);
        });
    });
    
    // Filters
    elements.categoryFilter.addEventListener('change', () => {
        state.filters.category = elements.categoryFilter.value;
        state.pagination.offset = 0;
        loadCampaigns();
    });
    
    elements.statusFilter.addEventListener('change', () => {
        state.filters.status = elements.statusFilter.value;
        state.pagination.offset = 0;
        loadCampaigns();
    });
    
    elements.searchInput.addEventListener('input', debounce(() => {
        state.filters.search = elements.searchInput.value;
        state.pagination.offset = 0;
        loadCampaigns();
    }, 300));
    
    elements.clearFiltersBtn.addEventListener('click', () => {
        state.filters = { category: 'all', status: 'all', search: '' };
        elements.categoryFilter.value = 'all';
        elements.statusFilter.value = 'all';
        elements.searchInput.value = '';
        state.pagination.offset = 0;
        loadCampaigns();
    });
    
    // Load More
    elements.loadMoreBtn.addEventListener('click', () => {
        loadCampaigns(true);
    });
    
    // Refresh/Scrape
    elements.refreshBtn.addEventListener('click', () => {
        // First time or empty, use demo data; otherwise try live scrape
        const useDemo = state.stats?.total_campaigns === 0;
        triggerScrape(useDemo);
    });
    
    // Modal
    elements.modalClose.addEventListener('click', closeModal);
    elements.modalOverlay.addEventListener('click', (e) => {
        if (e.target === elements.modalOverlay) closeModal();
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
}

// ==================== Initialization ====================
async function init() {
    setupEventListeners();
    
    // Load initial data
    await Promise.all([
        loadStats(),
        loadCategories(),
        loadCampaigns()
    ]);
    
    updateLastUpdated();
    
    // Show welcome message if no data
    if (state.campaigns.length === 0) {
        showToast(
            'info',
            'Welcome!',
            'Click "Run Scraper" to fetch campaign data'
        );
    }
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
