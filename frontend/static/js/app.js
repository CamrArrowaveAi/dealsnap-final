/**
 * DealSnap - Frontend Application
 * Dashboard with deal management, comparison, DealSnap Quick Mode, and financial modeling
 * Optimized for snappy UX with smooth transitions
 */

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

const AppState = {
    deals: [],
    activeDealId: null,
    openDealIds: [],
    currentView: 'dashboard',
    currentTab: 'info',
    categoryFilter: 'all',
    comparisonIds: [],
    selectedModel: 'standard',
    loading: false,
    notifications: []
};

// ============================================================================
// DEFAULT VALUES
// ============================================================================

function getDefaultDeal(name = 'New Deal', model = 'standard') {
    return {
        id: generateId(),
        name: name,
        model: model,
        status: 'active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        propertyName: name,
        address: '',
        propertyType: 'multifamily',
        purchasePrice: 500000,
        closingCosts: 10000,
        renovationBudget: 0,
        downPaymentPct: 25,
        interestRatePct: 6.5,
        amortYears: 30,
        loanTermYears: 30,
        loanFeesPct: 0,
        interestOnlyMonths: 0,
        entireLoanInterestOnly: false,
        units: 4,
        avgMonthlyRentPerUnit: 1200,
        otherMonthlyIncome: 0,
        vacancyPct: 5,
        rentGrowthPct: 3,
        expenseGrowthPct: 3,
        managementPctOfEGI: 8,
        capexReservePctOfEGI: 5,
        holdYears: 5,
        exitCapRatePct: 6.0,
        sellingCostsPct: 6.0,
        expenseLineItems: [
            { id: '1', label: 'Taxes', annualAmount: 7500, category: 'taxes' },
            { id: '2', label: 'Insurance', annualAmount: 3500, category: 'insurance' },
            { id: '3', label: 'Repairs & Maintenance', annualAmount: 3000, category: 'repairs' },
            { id: '4', label: 'Utilities', annualAmount: 2000, category: 'utilities' }
        ],
        targets: {
            minIRR: 12,
            minCashOnCash: 6,
            minDSCR: 1.25,
            maxEquity: 500000
        },
        results: null
    };
}

function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
}

// ============================================================================
// LOCAL STORAGE
// ============================================================================

function saveState() {
    try {
        localStorage.setItem('dealSnap_deals', JSON.stringify(AppState.deals));
        localStorage.setItem('dealSnap_openDealIds', JSON.stringify(AppState.openDealIds));
    } catch (e) {
        console.error('Error saving state:', e);
    }
}

function loadState() {
    try {
        const deals = localStorage.getItem('dealSnap_deals');
        const openIds = localStorage.getItem('dealSnap_openDealIds');

        if (deals) AppState.deals = JSON.parse(deals);
        if (openIds) AppState.openDealIds = JSON.parse(openIds);
    } catch (e) {
        console.error('Error loading state:', e);
    }
}

// ============================================================================
// NOTIFICATION SYSTEM
// ============================================================================

function showNotification(message, type = 'info', duration = 4000) {
    const container = document.getElementById('notification-container');
    if (!container) return;

    const id = generateId();
    const notification = document.createElement('div');
    notification.className = `notification notification--${type}`;
    notification.id = `notification-${id}`;
    notification.innerHTML = `
        <div class="notification__icon">${getNotificationIcon(type)}</div>
        <div class="notification__content">${message}</div>
        <button class="notification__close" onclick="closeNotification('${id}')">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
        </button>
    `;

    container.appendChild(notification);

    // Trigger animation
    requestAnimationFrame(() => {
        notification.classList.add('notification--visible');
    });

    // Auto-remove
    if (duration > 0) {
        setTimeout(() => closeNotification(id), duration);
    }

    return id;
}

function closeNotification(id) {
    const notification = document.getElementById(`notification-${id}`);
    if (notification) {
        notification.classList.remove('notification--visible');
        setTimeout(() => notification.remove(), 300);
    }
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success':
            return '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>';
        case 'error':
            return '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>';
        case 'warning':
            return '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>';
        default:
            return '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>';
    }
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'error', 6000);
}

function showWarning(message) {
    showNotification(message, 'warning', 5000);
}

// ============================================================================
// FORMATTING UTILITIES
// ============================================================================

function formatCurrency(value) {
    if (value === null || value === undefined || isNaN(value)) return '--';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function formatPercent(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) return '--%';
    return value.toFixed(decimals) + '%';
}

function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) return '--';
    return value.toFixed(decimals);
}

function formatCompactCurrency(value) {
    if (value === null || value === undefined || isNaN(value)) return '--';
    if (value >= 1000000) {
        return '$' + (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
        return '$' + (value / 1000).toFixed(0) + 'K';
    }
    return formatCurrency(value);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return 'N/A';
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch (e) {
        return 'N/A';
    }
}

function formatRelativeTime(dateString) {
    if (!dateString) return 'Never';
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return 'Never';

        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffMinutes = Math.floor(diffMs / (1000 * 60));

        if (diffMinutes < 1) return 'Just now';
        if (diffMinutes < 60) return `${diffMinutes}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays}d ago`;
        return formatDate(dateString);
    } catch (e) {
        return 'Never';
    }
}

// ============================================================================
// API CALLS
// ============================================================================

async function calculateDeal(deal) {
    AppState.loading = true;
    updateLoadingState();

    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ inputs: deal })
        });

        const data = await response.json();

        if (data.success) {
            deal.results = data.results;
            deal.updatedAt = new Date().toISOString();
            saveState();
            showSuccess('Calculation complete!');
            return data.results;
        } else {
            showError(data.error || 'Calculation failed');
            return null;
        }
    } catch (error) {
        console.error('API error:', error);
        showError('Failed to connect to API. Please check if the server is running.');
        return null;
    } finally {
        AppState.loading = false;
        updateLoadingState();
    }
}

// ============================================================================
// DEAL MANAGEMENT
// ============================================================================

function createDeal(name, model) {
    const deal = getDefaultDeal(name, model);
    AppState.deals.push(deal);
    AppState.openDealIds.push(deal.id);
    AppState.activeDealId = deal.id;
    AppState.currentView = 'deal-editor';
    AppState.currentTab = 'info';
    saveState();
    updateUI();
    showSuccess(`Deal "${name}" created`);
    return deal;
}

function openDeal(dealId) {
    if (!AppState.openDealIds.includes(dealId)) {
        AppState.openDealIds.push(dealId);
    }
    AppState.activeDealId = dealId;
    AppState.currentView = 'deal-editor';
    saveState();
    updateUI();
}

function closeDeal(dealId) {
    const index = AppState.openDealIds.indexOf(dealId);
    if (index > -1) {
        AppState.openDealIds.splice(index, 1);
    }

    if (AppState.activeDealId === dealId) {
        if (AppState.openDealIds.length > 0) {
            AppState.activeDealId = AppState.openDealIds[AppState.openDealIds.length - 1];
        } else {
            AppState.activeDealId = null;
            AppState.currentView = 'dashboard';
        }
    }
    saveState();
    updateUI();
}

function getActiveDeal() {
    return AppState.deals.find(d => d.id === AppState.activeDealId);
}

function updateDealStatus(dealId, status) {
    const deal = AppState.deals.find(d => d.id === dealId);
    if (deal) {
        deal.status = status;
        deal.updatedAt = new Date().toISOString();
        saveState();
        updateUI();
        showSuccess(`Deal status updated to ${status}`);
    }
}

function deleteDeal(dealId) {
    const deal = AppState.deals.find(d => d.id === dealId);
    if (!deal) return;

    if (!confirm(`Are you sure you want to delete "${deal.name}"? This cannot be undone.`)) {
        return;
    }

    const index = AppState.deals.findIndex(d => d.id === dealId);
    if (index > -1) {
        AppState.deals.splice(index, 1);
        closeDeal(dealId);
        removeFromComparison(dealId);
        saveState();
        updateUI();
        showSuccess('Deal deleted');
    }
}

// ============================================================================
// COMPARISON
// ============================================================================

function addToComparison(dealId) {
    if (AppState.comparisonIds.length >= 5) {
        showWarning('Maximum 5 deals for comparison');
        return;
    }
    if (!AppState.comparisonIds.includes(dealId)) {
        AppState.comparisonIds.push(dealId);
        updateComparisonBar();
        const deal = AppState.deals.find(d => d.id === dealId);
        if (deal) {
            showSuccess(`Added "${deal.name}" to comparison`);
        }
    }
}

function removeFromComparison(dealId) {
    const index = AppState.comparisonIds.indexOf(dealId);
    if (index > -1) {
        AppState.comparisonIds.splice(index, 1);
        updateComparisonBar();
    }
}

function clearComparison() {
    AppState.comparisonIds = [];
    updateComparisonBar();
}

function updateComparisonBar() {
    const bar = document.getElementById('comparison-bar');
    const itemsContainer = document.getElementById('comparison-items');
    const countEl = document.getElementById('comparison-count');
    const badgeEl = document.getElementById('comparison-count-badge');

    if (AppState.comparisonIds.length > 0) {
        bar.classList.add('comparison-bar--visible');
        const count = AppState.comparisonIds.length;
        if (countEl) countEl.textContent = count;
        if (badgeEl) badgeEl.textContent = count;

        itemsContainer.innerHTML = AppState.comparisonIds.map(id => {
            const deal = AppState.deals.find(d => d.id === id);
            return `
                <div class="comparison-item">
                    <span>${deal ? deal.name : 'Unknown'}</span>
                    <button class="comparison-item__remove" onclick="removeFromComparison('${id}')">
                        <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
            `;
        }).join('');
    } else {
        bar.classList.remove('comparison-bar--visible');
        if (badgeEl) badgeEl.textContent = '0';
    }
}

// ============================================================================
// UI UPDATE FUNCTIONS
// ============================================================================

function updateLoadingState() {
    const loader = document.getElementById('loading-overlay');
    if (loader) {
        if (AppState.loading) {
            loader.classList.remove('hidden');
        } else {
            loader.classList.add('hidden');
        }
    }
}

function updateUI() {
    updateLoadingState();
    updateCounts();
    updateDealTabs();
    updateComparisonBar();

    // Hide all views first
    const views = ['view-dashboard', 'view-dealsnap', 'view-deals', 'view-deal-editor', 'view-comparison'];
    views.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
    });

    // Show current view
    switch (AppState.currentView) {
        case 'dashboard':
            showDashboard();
            break;
        case 'dealsnap':
            showDealSnapView();
            break;
        case 'deals':
            showDealsView();
            break;
        case 'deal-editor':
            showDealEditor();
            break;
        case 'comparison':
            showComparisonView();
            break;
    }

    updateNavigation();
}

function updateCounts() {
    const active = AppState.deals.filter(d => d.status === 'active').length;
    const completed = AppState.deals.filter(d => d.status === 'completed').length;
    const archived = AppState.deals.filter(d => d.status === 'archived').length;
    const total = AppState.deals.length;

    const filterAll = document.getElementById('filter-all-count');
    if (filterAll) filterAll.textContent = total;
    const filterActive = document.getElementById('filter-active-count');
    if (filterActive) filterActive.textContent = active;
    const filterCompleted = document.getElementById('filter-completed-count');
    if (filterCompleted) filterCompleted.textContent = completed;
    const filterArchived = document.getElementById('filter-archived-count');
    if (filterArchived) filterArchived.textContent = archived;
}

function updateNavigation() {
    document.querySelectorAll('.nav-item[data-view]').forEach(item => {
        const isActive = item.dataset.view === AppState.currentView ||
            (AppState.currentView === 'deal-editor' && item.dataset.view === 'deals') ||
            (AppState.currentView === 'comparison' && item.dataset.view === 'deals');
        item.classList.toggle('nav-item--active', isActive);
    });
}

function updateDealTabs() {
    const container = document.getElementById('deal-tabs-container');
    const tabsEl = document.getElementById('deal-tabs');

    if (AppState.openDealIds.length > 0 && AppState.currentView === 'deal-editor') {
        container.classList.remove('hidden');
        tabsEl.innerHTML = AppState.openDealIds.map(id => {
            const deal = AppState.deals.find(d => d.id === id);
            if (!deal) return '';
            const isActive = id === AppState.activeDealId;
            return `
                <button class="deal-tab ${isActive ? 'deal-tab--active' : ''}" onclick="openDeal('${id}')">
                    <span class="deal-tab__name">${deal.name}</span>
                    <button class="deal-tab__close" onclick="event.stopPropagation(); closeDeal('${id}')" title="Close">
                        <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </button>
            `;
        }).join('');
    } else {
        container.classList.add('hidden');
    }
}

// ============================================================================
// VIEW RENDERERS
// ============================================================================

function showDashboard() {
    document.getElementById('view-dashboard').classList.remove('hidden');
    renderDashboardMetrics();
    renderActivityFeed();
}

function showDealsView() {
    document.getElementById('view-deals').classList.remove('hidden');
    renderDealsGrid();
}

function renderDashboardMetrics() {
    const total = AppState.deals.length;
    const active = AppState.deals.filter(d => d.status === 'active').length;
    const completed = AppState.deals.filter(d => d.status === 'completed').length;
    const dealsWithResults = AppState.deals.filter(d => d.results);

    const avgIRR = dealsWithResults.length > 0
        ? dealsWithResults.reduce((sum, d) => sum + (d.results.IRR || 0), 0) / dealsWithResults.length
        : 0;

    const pipelineValue = AppState.deals.reduce((sum, d) => sum + (d.purchasePrice || 0), 0);

    const passingDeals = dealsWithResults.filter(d => d.results.verdict?.status === 'pass').length;

    const metricsContainer = document.getElementById('dashboard-metrics');
    if (!metricsContainer) return;

    metricsContainer.innerHTML = `
        <div class="metric-card metric-card--highlight">
            <div class="metric-card__icon">
                <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
            </div>
            <div class="metric-card__value">${active}</div>
            <div class="metric-card__label">Active Deals</div>
            <div class="metric-card__subtext">${total} total</div>
        </div>
        <div class="metric-card">
            <div class="metric-card__icon">
                <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                </svg>
            </div>
            <div class="metric-card__value">${formatPercent(avgIRR)}</div>
            <div class="metric-card__label">Avg IRR</div>
            <div class="metric-card__subtext">${dealsWithResults.length} analyzed</div>
        </div>
        <div class="metric-card">
            <div class="metric-card__icon">
                <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
            <div class="metric-card__value">${formatCompactCurrency(pipelineValue)}</div>
            <div class="metric-card__label">Pipeline Value</div>
            <div class="metric-card__subtext">${active} in review</div>
        </div>
        <div class="metric-card ${passingDeals > 0 ? 'metric-card--success' : ''}">
            <div class="metric-card__icon">
                <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
            <div class="metric-card__value">${passingDeals}</div>
            <div class="metric-card__label">Passing Deals</div>
            <div class="metric-card__subtext">${dealsWithResults.length > 0 ? Math.round(passingDeals / dealsWithResults.length * 100) : 0}% pass rate</div>
        </div>
    `;
}

function renderActivityFeed() {
    const listContainer = document.getElementById('recent-deals-list');
    if (!listContainer) return;

    const recent = [...AppState.deals].sort((a, b) => {
        const dateA = new Date(a.updatedAt || a.createdAt || 0);
        const dateB = new Date(b.updatedAt || b.createdAt || 0);
        return dateB - dateA;
    }).slice(0, 6);

    if (recent.length === 0) {
        listContainer.innerHTML = `
            <div class="empty-state empty-state--compact">
                <div class="empty-state__icon">
                    <svg width="32" height="32" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                    </svg>
                </div>
                <p class="empty-state__description">No deals yet. Create your first deal to get started!</p>
                <button class="btn btn--primary btn--sm" onclick="showNewDealModal()">
                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                    </svg>
                    New Deal
                </button>
            </div>
        `;
        return;
    }

    listContainer.innerHTML = recent.map(d => {
        const hasResults = d.results !== null;
        const verdict = d.results?.verdict?.status;

        return `
            <div class="activity-item" onclick="openDeal('${d.id}')">
                <div class="activity-item__indicator activity-item__indicator--${d.status}"></div>
                <div class="activity-item__content">
                    <div class="activity-item__header">
                        <span class="activity-item__name">${d.name}</span>
                        ${hasResults && verdict ? `<span class="verdict-badge verdict-badge--${verdict}">${verdict}</span>` : ''}
                    </div>
                    <div class="activity-item__details">
                        <span class="activity-item__price">${formatCompactCurrency(d.purchasePrice)}</span>
                        <span class="activity-item__separator">•</span>
                        <span class="activity-item__units">${d.units} unit${d.units > 1 ? 's' : ''}</span>
                        ${hasResults ? `<span class="activity-item__separator">•</span><span class="activity-item__irr">${formatPercent(d.results.IRR)} IRR</span>` : ''}
                    </div>
                </div>
                <div class="activity-item__time">${formatRelativeTime(d.updatedAt || d.createdAt)}</div>
            </div>
        `;
    }).join('');
}

function renderDealsGrid() {
    const grid = document.getElementById('deals-grid');
    const emptyState = document.getElementById('empty-state');

    let filteredDeals = AppState.deals;
    if (AppState.categoryFilter !== 'all') {
        filteredDeals = AppState.deals.filter(d => d.status === AppState.categoryFilter);
    }

    // Sort by updated date
    filteredDeals = [...filteredDeals].sort((a, b) => {
        const dateA = new Date(a.updatedAt || a.createdAt || 0);
        const dateB = new Date(b.updatedAt || b.createdAt || 0);
        return dateB - dateA;
    });

    if (filteredDeals.length === 0) {
        grid.classList.add('hidden');
        emptyState.classList.remove('hidden');
    } else {
        grid.classList.remove('hidden');
        emptyState.classList.add('hidden');

        grid.innerHTML = filteredDeals.map(deal => {
            const r = deal.results;
            const isInComparison = AppState.comparisonIds.includes(deal.id);
            const verdictStatus = r?.verdict?.status;

            return `
                <div class="deal-card ${isInComparison ? 'deal-card--selected' : ''}" onclick="openDeal('${deal.id}')">
                    <div class="deal-card__header">
                        <div class="deal-card__header-top">
                            <span class="deal-card__status deal-card__status--${deal.status}">
                                ${deal.status.charAt(0).toUpperCase() + deal.status.slice(1)}
                            </span>
                            ${verdictStatus ? `<span class="verdict-badge verdict-badge--${verdictStatus}">${verdictStatus}</span>` : ''}
                        </div>
                        <h3 class="deal-card__title">${deal.name}</h3>
                        <p class="deal-card__address">${deal.address || 'No address specified'}</p>
                    </div>
                    <div class="deal-card__body">
                        <div class="deal-card__price">${formatCurrency(deal.purchasePrice)}</div>
                        <div class="deal-card__metrics">
                            <div class="deal-card__metric">
                                <span class="deal-card__metric-value ${r && r.IRR >= (deal.targets?.minIRR || 12) ? 'text-success' : ''}">${r ? formatPercent(r.IRR) : '--%'}</span>
                                <span class="deal-card__metric-label">IRR</span>
                            </div>
                            <div class="deal-card__metric">
                                <span class="deal-card__metric-value">${r ? formatPercent(r.cashOnCash_year1) : '--%'}</span>
                                <span class="deal-card__metric-label">CoC</span>
                            </div>
                            <div class="deal-card__metric">
                                <span class="deal-card__metric-value ${r && r.DSCR_year1 >= (deal.targets?.minDSCR || 1.25) ? 'text-success' : r && r.DSCR_year1 < 1.2 ? 'text-danger' : ''}">${r ? formatNumber(r.DSCR_year1) + 'x' : '--'}</span>
                                <span class="deal-card__metric-label">DSCR</span>
                            </div>
                            <div class="deal-card__metric">
                                <span class="deal-card__metric-value">${deal.units}</span>
                                <span class="deal-card__metric-label">Units</span>
                            </div>
                        </div>
                    </div>
                    <div class="deal-card__footer">
                        <span class="deal-card__date">${formatRelativeTime(deal.updatedAt || deal.createdAt)}</span>
                        <div class="deal-card__actions" onclick="event.stopPropagation()">
                            <button class="btn btn--icon btn--ghost ${isInComparison ? 'btn--active' : ''}"
                                    onclick="event.stopPropagation(); ${isInComparison ? `removeFromComparison('${deal.id}')` : `addToComparison('${deal.id}')`}"
                                    title="${isInComparison ? 'Remove from comparison' : 'Add to comparison'}">
                                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                                </svg>
                            </button>
                            <button class="btn btn--icon btn--ghost btn--danger" onclick="event.stopPropagation(); deleteDeal('${deal.id}')" title="Delete deal">
                                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }
}

function showDealEditor() {
    document.getElementById('view-deal-editor').classList.remove('hidden');

    const deal = getActiveDeal();
    if (!deal) {
        AppState.currentView = 'dashboard';
        updateUI();
        return;
    }

    bindDealForm(deal);
    renderExpenses(deal);
    switchPropertyTab(AppState.currentTab);

    if (deal.results) {
        renderResults(deal);
        renderProForma(deal);
    } else {
        // Show placeholder for results
        const resultsContent = document.getElementById('results-content');
        if (resultsContent) {
            resultsContent.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state__icon">
                        <svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                        </svg>
                    </div>
                    <h3 class="empty-state__title">No Results Yet</h3>
                    <p class="empty-state__description">Click "Calculate Returns" in the Financial Modeling tab to analyze this deal.</p>
                </div>
            `;
        }
        const proformaContent = document.getElementById('proforma-content');
        if (proformaContent) {
            proformaContent.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state__icon">
                        <svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                    </div>
                    <h3 class="empty-state__title">Pro Forma Not Available</h3>
                    <p class="empty-state__description">Run the calculation first to view year-by-year projections.</p>
                </div>
            `;
        }
    }
}

function bindDealForm(deal) {
    document.querySelectorAll('[data-field]').forEach(input => {
        const field = input.dataset.field;
        const isNested = field.includes('.');

        let value;
        if (isNested) {
            const [parent, child] = field.split('.');
            value = deal[parent] ? deal[parent][child] : '';
        } else {
            value = deal[field];
        }

        if (input.type === 'checkbox') {
            input.checked = value;
        } else {
            input.value = value !== undefined && value !== null ? value : '';
        }

        // Remove old listeners by cloning
        const newInput = input.cloneNode(true);
        input.parentNode.replaceChild(newInput, input);

        // Add new listener with debounce for better performance
        let debounceTimer;
        newInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                let val = e.target.type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value;

                if (isNested) {
                    const [parent, child] = field.split('.');
                    if (!deal[parent]) deal[parent] = {};
                    deal[parent][child] = val;
                } else {
                    deal[field] = val;
                }
                deal.updatedAt = new Date().toISOString();
                saveState();
            }, 100);
        });
    });
}

function renderExpenses(deal) {
    const container = document.getElementById('expenses-list');
    if (!container) return;

    if (deal.expenseLineItems.length === 0) {
        container.innerHTML = `<div class="text-muted text-sm p-md">No expenses added yet. Click "Add Expense" below.</div>`;
        return;
    }

    container.innerHTML = deal.expenseLineItems.map((item, index) => `
        <div class="expense-item">
            <input type="text"
                   class="form-input"
                   value="${item.label}"
                   onchange="updateExpense(${index}, 'label', this.value)"
                   placeholder="Expense name">
            <div class="input-with-prefix">
                <span class="input-with-prefix__prefix">$</span>
                <input type="number"
                       class="form-input"
                       value="${item.annualAmount}"
                       onchange="updateExpense(${index}, 'annualAmount', parseFloat(this.value) || 0)"
                       placeholder="Annual amount">
            </div>
            <button class="expense-item__remove" onclick="removeExpense(${index})" title="Remove expense">
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
            </button>
        </div>
    `).join('');
}

function updateExpense(index, field, value) {
    const deal = getActiveDeal();
    if (deal && deal.expenseLineItems[index]) {
        deal.expenseLineItems[index][field] = value;
        deal.updatedAt = new Date().toISOString();
        saveState();
    }
}

function addExpense() {
    const deal = getActiveDeal();
    if (deal) {
        deal.expenseLineItems.push({
            id: Date.now().toString(),
            label: 'New Expense',
            annualAmount: 0,
            category: 'other'
        });
        deal.updatedAt = new Date().toISOString();
        saveState();
        renderExpenses(deal);
    }
}

function removeExpense(index) {
    const deal = getActiveDeal();
    if (deal) {
        deal.expenseLineItems.splice(index, 1);
        deal.updatedAt = new Date().toISOString();
        saveState();
        renderExpenses(deal);
    }
}

function switchPropertyTab(tabName) {
    AppState.currentTab = tabName;

    document.querySelectorAll('.property-tab').forEach(tab => {
        tab.classList.toggle('property-tab--active', tab.dataset.tab === tabName);
    });

    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.add('hidden');
        panel.classList.remove('tab-panel--active');
    });

    const activePanel = document.getElementById(`tab-${tabName}`);
    if (activePanel) {
        activePanel.classList.remove('hidden');
        activePanel.classList.add('tab-panel--active');
    }
}

function renderResults(deal) {
    const container = document.getElementById('results-content');
    if (!container || !deal.results) return;

    const r = deal.results;
    const verdict = r.verdict;
    const checks = verdict.checks || {};

    container.innerHTML = `
        <div class="results-summary">
            <div class="results-verdict results-verdict--${verdict.status}">
                <div class="results-verdict__icon">${getVerdictIcon(verdict.status)}</div>
                <div class="results-verdict__content">
                    <div class="results-verdict__status">${verdict.status.toUpperCase()}</div>
                    <div class="results-verdict__summary">${verdict.summary}</div>
                </div>
            </div>
        </div>

        <div class="results-metrics">
            <div class="results-metric results-metric--primary">
                <div class="results-metric__value">${formatPercent(r.IRR)}</div>
                <div class="results-metric__label">Internal Rate of Return</div>
                <div class="results-metric__target ${checks.irr?.pass ? 'results-metric__target--pass' : 'results-metric__target--fail'}">
                    Target: ${deal.targets?.minIRR || 12}%
                </div>
            </div>
            <div class="results-metric">
                <div class="results-metric__value">${formatPercent(r.cashOnCash_year1)}</div>
                <div class="results-metric__label">Year 1 Cash-on-Cash</div>
                <div class="results-metric__target ${checks.cashOnCash?.pass ? 'results-metric__target--pass' : 'results-metric__target--fail'}">
                    Target: ${deal.targets?.minCashOnCash || 6}%
                </div>
            </div>
            <div class="results-metric">
                <div class="results-metric__value">${formatNumber(r.DSCR_year1)}x</div>
                <div class="results-metric__label">Year 1 DSCR</div>
                <div class="results-metric__target ${checks.dscr?.pass ? 'results-metric__target--pass' : 'results-metric__target--fail'}">
                    Target: ${deal.targets?.minDSCR || 1.25}x
                </div>
            </div>
            <div class="results-metric">
                <div class="results-metric__value">${formatPercent(r.capRate_year1)}</div>
                <div class="results-metric__label">Cap Rate</div>
            </div>
            <div class="results-metric">
                <div class="results-metric__value">${formatNumber(r.equityMultiple)}x</div>
                <div class="results-metric__label">Equity Multiple</div>
            </div>
            <div class="results-metric">
                <div class="results-metric__value">${formatCurrency(r.equityInvested)}</div>
                <div class="results-metric__label">Equity Required</div>
                <div class="results-metric__target ${checks.equity?.pass ? 'results-metric__target--pass' : 'results-metric__target--fail'}">
                    Max: ${formatCurrency(deal.targets?.maxEquity || 500000)}
                </div>
            </div>
        </div>

        ${r.warnings && r.warnings.length > 0 ? `
            <div class="results-warnings">
                ${r.warnings.map(w => `
                    <div class="alert alert--warning">
                        <svg class="alert__icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                        </svg>
                        <span>${w}</span>
                    </div>
                `).join('')}
            </div>
        ` : ''}

        <div class="results-details">
            <h3 class="results-details__title">Deal Summary</h3>
            <div class="results-table">
                <div class="results-table__row">
                    <span class="results-table__label">Purchase Price</span>
                    <span class="results-table__value">${formatCurrency(deal.purchasePrice)}</span>
                </div>
                <div class="results-table__row">
                    <span class="results-table__label">Total Acquisition Cost</span>
                    <span class="results-table__value">${formatCurrency(r.totalAcquisitionCost)}</span>
                </div>
                <div class="results-table__row">
                    <span class="results-table__label">Loan Amount</span>
                    <span class="results-table__value">${formatCurrency(r.loanAmount)}</span>
                </div>
                <div class="results-table__row results-table__row--highlight">
                    <span class="results-table__label">Equity Invested</span>
                    <span class="results-table__value">${formatCurrency(r.equityInvested)}</span>
                </div>
                <div class="results-table__row">
                    <span class="results-table__label">Year 1 NOI</span>
                    <span class="results-table__value">${formatCurrency(r.NOI_year1)}</span>
                </div>
                <div class="results-table__row">
                    <span class="results-table__label">Year 1 Cash Flow</span>
                    <span class="results-table__value ${r.cashFlow_year1 < 0 ? 'text-danger' : ''}">${formatCurrency(r.cashFlow_year1)}</span>
                </div>
                <div class="results-table__row">
                    <span class="results-table__label">Exit Sale Price (Year ${deal.holdYears})</span>
                    <span class="results-table__value">${formatCurrency(r.salePrice)}</span>
                </div>
                <div class="results-table__row results-table__row--highlight">
                    <span class="results-table__label">Net Sale Proceeds</span>
                    <span class="results-table__value">${formatCurrency(r.netSaleProceeds)}</span>
                </div>
            </div>
        </div>
    `;
}

function renderProForma(deal) {
    const container = document.getElementById('proforma-content');
    if (!container || !deal.results) return;

    const r = deal.results;

    container.innerHTML = `
        <div class="card">
            <div class="card__header">
                <h2 class="card__title">Year-by-Year Pro Forma</h2>
                <p class="card__subtitle">Projected cash flows over ${deal.holdYears} year hold period</p>
            </div>
            <div class="card__body">
                <div class="proforma-container">
                    <table class="proforma-table">
                        <thead>
                            <tr>
                                <th>Year</th>
                                <th>GPR</th>
                                <th>Vacancy</th>
                                <th>EGI</th>
                                <th>OpEx</th>
                                <th>NOI</th>
                                <th>Debt Service</th>
                                <th>Cash Flow</th>
                                <th>CoC</th>
                                <th>DSCR</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${r.proForma.map(pf => `
                                <tr class="${pf.CashFlow < 0 ? 'proforma-table__row--negative' : ''}">
                                    <td class="proforma-table__year">
                                        ${pf.year}
                                        ${pf.isIOYear ? '<span class="proforma-badge">IO</span>' : ''}
                                    </td>
                                    <td>${formatCurrency(pf.GPR)}</td>
                                    <td class="text-danger">(${formatCurrency(pf.VacancyLoss)})</td>
                                    <td>${formatCurrency(pf.EGI)}</td>
                                    <td class="text-muted">(${formatCurrency(pf.TotalOpEx)})</td>
                                    <td class="font-semibold">${formatCurrency(pf.NOI)}</td>
                                    <td class="text-muted">(${formatCurrency(pf.DebtService)})</td>
                                    <td class="font-semibold ${pf.CashFlow < 0 ? 'text-danger' : 'text-success'}">${formatCurrency(pf.CashFlow)}</td>
                                    <td>${formatPercent(pf.cashOnCashPct)}</td>
                                    <td class="${pf.DSCR < 1.2 ? 'text-danger' : pf.DSCR >= 1.4 ? 'text-success' : ''}">${formatNumber(pf.DSCR)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

function showComparisonView() {
    document.getElementById('view-comparison').classList.remove('hidden');
    renderComparison();
}

function renderComparison() {
    const container = document.getElementById('comparison-content');

    if (AppState.comparisonIds.length < 2) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state__icon">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                    </svg>
                </div>
                <h3 class="empty-state__title">Select Deals to Compare</h3>
                <p class="empty-state__description">Add 2-5 deals to compare from the Deals view. Click the compare icon on any deal card.</p>
                <button class="btn btn--primary" onclick="AppState.currentView = 'deals'; updateUI();">
                    Go to Deals
                </button>
            </div>
        `;
        return;
    }

    const deals = AppState.comparisonIds.map(id => AppState.deals.find(d => d.id === id)).filter(d => d);

    const metrics = [
        { label: 'Purchase Price', key: 'purchasePrice', format: formatCurrency },
        { label: 'Units', key: 'units', format: v => v },
        { label: 'Price per Unit', key: 'pricePerUnit', format: formatCurrency, calc: d => d.purchasePrice / d.units },
        { label: 'IRR', key: 'IRR', format: formatPercent, fromResults: true, highlight: 'max' },
        { label: 'Cash-on-Cash', key: 'cashOnCash_year1', format: formatPercent, fromResults: true, highlight: 'max' },
        { label: 'DSCR', key: 'DSCR_year1', format: v => formatNumber(v) + 'x', fromResults: true, highlight: 'max' },
        { label: 'Cap Rate', key: 'capRate_year1', format: formatPercent, fromResults: true },
        { label: 'Equity Required', key: 'equityInvested', format: formatCurrency, fromResults: true, highlight: 'min' },
        { label: 'Year 1 NOI', key: 'NOI_year1', format: formatCurrency, fromResults: true, highlight: 'max' },
        { label: 'Year 1 Cash Flow', key: 'cashFlow_year1', format: formatCurrency, fromResults: true, highlight: 'max' },
        { label: 'Equity Multiple', key: 'equityMultiple', format: v => formatNumber(v) + 'x', fromResults: true, highlight: 'max' },
        { label: 'Exit Sale Price', key: 'salePrice', format: formatCurrency, fromResults: true }
    ];

    container.innerHTML = `
        <div class="proforma-container">
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        ${deals.map(d => `
                            <th>
                                <div class="comparison-header">
                                    <span class="comparison-header__name">${d.name}</span>
                                    ${d.results?.verdict?.status ? `<span class="verdict-badge verdict-badge--${d.results.verdict.status} verdict-badge--sm">${d.results.verdict.status}</span>` : ''}
                                </div>
                            </th>
                        `).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${metrics.map(m => {
                        const values = deals.map(d => {
                            if (m.calc) return m.calc(d);
                            if (m.fromResults) return d.results ? d.results[m.key] : null;
                            return d[m.key];
                        });

                        let bestIndex = -1;
                        if (m.highlight && values.some(v => v !== null && !isNaN(v))) {
                            const numValues = values.filter(v => v !== null && !isNaN(v));
                            if (numValues.length > 0) {
                                const best = m.highlight === 'max' ? Math.max(...numValues) : Math.min(...numValues);
                                bestIndex = values.indexOf(best);
                            }
                        }

                        return `
                            <tr>
                                <td>${m.label}</td>
                                ${values.map((v, i) => `
                                    <td class="${i === bestIndex ? 'comparison-table__highlight' : ''}">
                                        ${v !== null && !isNaN(v) ? m.format(v) : '--'}
                                    </td>
                                `).join('')}
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function getVerdictIcon(status) {
    switch (status) {
        case 'pass':
            return '<svg width="24" height="24" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>';
        case 'fail':
            return '<svg width="24" height="24" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>';
        case 'borderline':
            return '<svg width="24" height="24" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>';
        default:
            return '';
    }
}

// ============================================================================
// DEALSNAP QUICK MODE
// ============================================================================

function showDealSnapView() {
    document.getElementById('view-dealsnap').classList.remove('hidden');

    // Set smart defaults for DealSnap form if empty
    const setDefault = (id, value) => {
        const el = document.getElementById(id);
        if (el && !el.value) el.value = value;
    };
    setDefault('ds-units', '');
    setDefault('ds-avg-rent', '');
    setDefault('ds-purchase-price', '');
    setDefault('ds-property-type', 'multifamily');
    setDefault('ds-condition', 'average');
    setDefault('ds-expense-responsibility', 'mixed');
    setDefault('ds-insurance-risk', 'moderate');
    setDefault('ds-down-payment', '25');
    setDefault('ds-interest-rate', '6.5');
    setDefault('ds-amort-years', '30');
}

function getDealSnapInputs() {
    const units = parseInt(document.getElementById('ds-units')?.value) || 0;
    const avgRent = parseFloat(document.getElementById('ds-avg-rent')?.value) || 0;
    const purchasePrice = parseFloat(document.getElementById('ds-purchase-price')?.value) || 0;

    const propertyType = document.getElementById('ds-property-type')?.value || 'multifamily';
    const condition = document.getElementById('ds-condition')?.value || 'average';
    const expenseResp = document.getElementById('ds-expense-responsibility')?.value || 'mixed';
    const insuranceRisk = document.getElementById('ds-insurance-risk')?.value || 'moderate';

    const downPayment = parseFloat(document.getElementById('ds-down-payment')?.value) || 25;
    const interestRate = parseFloat(document.getElementById('ds-interest-rate')?.value) || 6.5;
    const amortYears = parseInt(document.getElementById('ds-amort-years')?.value) || 30;

    const rentLiftDollar = parseFloat(document.getElementById('ds-rent-lift-dollar')?.value) || 0;
    const rentLiftPct = parseFloat(document.getElementById('ds-rent-lift-pct')?.value) || 0;

    // Map frontend values to backend enum values
    const typeMap = { 'sfr': 'single_family', 'multifamily': 'multifamily', 'apartment': 'apartment' };

    return {
        units: units,
        avg_monthly_rent: avgRent,
        purchase_price: purchasePrice,
        property_type: typeMap[propertyType] || propertyType,
        property_condition: condition,
        expense_responsibility: expenseResp,
        insurance_risk: insuranceRisk,
        down_payment_pct: downPayment,
        interest_rate_pct: interestRate,
        amort_years: amortYears,
        rent_lift_dollar_per_unit: rentLiftDollar > 0 ? rentLiftDollar : null,
        rent_lift_pct: rentLiftPct > 0 ? rentLiftPct : null
    };
}

async function runDealSnap() {
    const inputs = getDealSnapInputs();

    // Validation
    if (!inputs.units || inputs.units < 1) {
        showWarning('Please enter the number of units');
        document.getElementById('ds-units')?.focus();
        return;
    }
    if (!inputs.avg_monthly_rent || inputs.avg_monthly_rent <= 0) {
        showWarning('Please enter the average monthly rent');
        document.getElementById('ds-avg-rent')?.focus();
        return;
    }
    if (!inputs.purchase_price || inputs.purchase_price <= 0) {
        showWarning('Please enter the purchase price');
        document.getElementById('ds-purchase-price')?.focus();
        return;
    }

    AppState.loading = true;
    updateLoadingState();

    try {
        const response = await fetch('/api/dealsnap', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ inputs: inputs })
        });

        const data = await response.json();

        if (data.success) {
            renderDealSnapResults(data.results);
            showSuccess('DealSnap analysis complete!');
        } else {
            showError(data.error || 'DealSnap calculation failed');
        }
    } catch (error) {
        console.error('DealSnap API error:', error);
        showError('Failed to connect to API. Please check if the server is running.');
    } finally {
        AppState.loading = false;
        updateLoadingState();
    }
}

function renderDealSnapResults(results) {
    const container = document.getElementById('dealsnap-results');
    if (!container) return;

    container.classList.remove('hidden');

    // Render triage banner
    renderDealSnapTriage(results.deal_triage);

    // Render key metrics
    renderDealSnapMetrics(results);

    // Render income summary
    renderDealSnapIncome(results.income);

    // Render value reality check
    renderDealSnapValueCheck(results.value_reality_check);

    // Render finance reality check
    renderDealSnapFinance(results.finance_reality_check, results.expenses);

    // Render reverse engineering
    renderDealSnapReverse(results.reverse_engineering);

    // Render rent sensitivity
    if (results.rent_lift_sensitivity) {
        renderDealSnapRentSensitivity(results.rent_lift_sensitivity);
    }

    // Render investor notes
    renderDealSnapNotes(results);

    // Scroll to results
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderDealSnapTriage(triage) {
    const content = document.getElementById('ds-triage-content');
    if (!content || !triage) return;

    const score = triage.verdict.toLowerCase();
    const emoji = score === 'pursue' ? '&#x2705;' : score === 'watch' ? '&#x26A0;&#xFE0F;' : '&#x274C;';

    content.innerHTML = `
        <div class="ds-triage-banner ds-triage-banner--${score}">
            <div class="ds-triage-banner__icon">${emoji}</div>
            <div class="ds-triage-banner__content">
                <div class="ds-triage-banner__verdict">${triage.verdict}</div>
                <div class="ds-triage-banner__score">Score: ${triage.total_score} / 12</div>
                <div class="ds-triage-banner__breakdown">
                    <span class="ds-triage-badge">Cap Rate: ${triage.cap_rate_score}/3</span>
                    <span class="ds-triage-badge">DSCR: ${triage.dscr_score}/3</span>
                    <span class="ds-triage-badge">Expense: ${triage.expense_ratio_score}/2</span>
                    <span class="ds-triage-badge">GRM: ${triage.grm_score}/2</span>
                    <span class="ds-triage-badge">DSCR Signal: ${triage.dscr_signal_score}/2</span>
                </div>
            </div>
        </div>
    `;
}

function renderDealSnapMetrics(results) {
    const capRate = results.income?.cap_rate;
    const dscr = results.finance_reality_check?.dscr;
    const expenseRatio = results.expenses?.expense_ratio_pct;
    const grm = results.income?.grm;

    const setMetric = (id, value, signal) => {
        const el = document.getElementById(id);
        if (!el) return;
        const valueEl = el.querySelector('.metric-card__value');
        if (valueEl) {
            valueEl.textContent = value;
            valueEl.className = 'metric-card__value';
            if (signal === 'green') valueEl.classList.add('text-success');
            else if (signal === 'red') valueEl.classList.add('text-danger');
            else if (signal === 'orange') valueEl.classList.add('text-warning');
        }
    };

    setMetric('ds-metric-caprate', capRate != null ? formatPercent(capRate) : '--',
        capRate >= 7 ? 'green' : capRate >= 5 ? 'orange' : 'red');
    setMetric('ds-metric-dscr', dscr != null ? formatNumber(dscr) + 'x' : '--',
        dscr >= 1.25 ? 'green' : dscr >= 1.0 ? 'orange' : 'red');
    setMetric('ds-metric-expense-ratio', expenseRatio != null ? formatPercent(expenseRatio) : '--',
        expenseRatio <= 40 ? 'green' : expenseRatio <= 50 ? 'orange' : 'red');
    setMetric('ds-metric-grm', grm != null ? formatNumber(grm, 1) : '--',
        grm <= 10 ? 'green' : grm <= 14 ? 'orange' : 'red');
}

function renderDealSnapIncome(income) {
    const content = document.getElementById('ds-income-content');
    if (!content || !income) return;

    content.innerHTML = `
        <div class="ds-summary-grid">
            <div>
                <div class="ds-summary-item">
                    <span class="ds-summary-label">GPR (Annual)</span>
                    <span class="ds-summary-value">${formatCurrency(income.gpr_annual)}</span>
                </div>
                <div class="ds-summary-item">
                    <span class="ds-summary-label">Vacancy Loss (${formatPercent(income.vacancy_pct || 5)})</span>
                    <span class="ds-summary-value text-danger">-${formatCurrency(income.vacancy_loss)}</span>
                </div>
                <div class="ds-summary-item ds-summary-item--total">
                    <span class="ds-summary-label">EGI</span>
                    <span class="ds-summary-value">${formatCurrency(income.egi)}</span>
                </div>
            </div>
            <div>
                <div class="ds-summary-item">
                    <span class="ds-summary-label">Cap Rate</span>
                    <span class="ds-summary-value">${formatPercent(income.cap_rate)}</span>
                </div>
                <div class="ds-summary-item">
                    <span class="ds-summary-label">GRM</span>
                    <span class="ds-summary-value">${formatNumber(income.grm, 1)}</span>
                </div>
                <div class="ds-summary-item">
                    <span class="ds-summary-label">Price / Unit</span>
                    <span class="ds-summary-value">${formatCurrency(income.price_per_unit)}</span>
                </div>
            </div>
        </div>
    `;
}

function renderDealSnapValueCheck(valueCheck) {
    const content = document.getElementById('ds-value-check-content');
    if (!content || !valueCheck) return;

    const rows = valueCheck.valuations.map(v => {
        const signalClass = v.signal === 'green' ? 'ds-signal--green' : v.signal === 'orange' ? 'ds-signal--orange' : 'ds-signal--red';
        return `
            <tr>
                <td>${formatPercent(v.cap_rate)}</td>
                <td>${formatCurrency(v.implied_value)}</td>
                <td>${formatCurrency(v.delta)}</td>
                <td><span class="ds-signal ${signalClass}"><span class="ds-signal__dot"></span>${v.signal.charAt(0).toUpperCase() + v.signal.slice(1)}</span></td>
            </tr>
        `;
    }).join('');

    content.innerHTML = `
        <p class="text-muted text-sm mb-md">NOI: ${formatCurrency(valueCheck.noi)} | Purchase Price: ${formatCurrency(valueCheck.purchase_price)}</p>
        <table class="ds-value-table">
            <thead>
                <tr>
                    <th>Cap Rate</th>
                    <th>Implied Value</th>
                    <th>Delta</th>
                    <th>Signal</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
}

function renderDealSnapFinance(finance, expenses) {
    const content = document.getElementById('ds-finance-content');
    if (!content || !finance) return;

    const dscrSignal = finance.dscr_signal;
    const dscrClass = dscrSignal === 'green' ? 'ds-dscr-value--green' : dscrSignal === 'orange' ? 'ds-dscr-value--orange' : 'ds-dscr-value--red';
    const bandClass = dscrSignal === 'green' ? 'ds-dscr-band--green' : dscrSignal === 'orange' ? 'ds-dscr-band--orange' : 'ds-dscr-band--red';
    const bandLabel = dscrSignal === 'green' ? 'Healthy (>= 1.25x)' : dscrSignal === 'orange' ? 'Tight (1.0x - 1.25x)' : 'Negative Coverage (< 1.0x)';

    content.innerHTML = `
        <div class="ds-dscr-display mb-lg">
            <div>
                <div class="ds-dscr-value ${dscrClass}">${formatNumber(finance.dscr)}x</div>
                <div class="ds-dscr-label">DSCR</div>
            </div>
            <div>
                <span class="ds-dscr-band ${bandClass}">${bandLabel}</span>
            </div>
        </div>
        <div class="ds-finance-grid">
            <div class="ds-finance-item">
                <div class="ds-finance-item__label">Loan Amount</div>
                <div class="ds-finance-item__value">${formatCurrency(finance.loan_amount)}</div>
            </div>
            <div class="ds-finance-item">
                <div class="ds-finance-item__label">Monthly Payment</div>
                <div class="ds-finance-item__value">${formatCurrency(finance.monthly_payment)}</div>
            </div>
            <div class="ds-finance-item">
                <div class="ds-finance-item__label">Annual Debt Service</div>
                <div class="ds-finance-item__value">${formatCurrency(finance.annual_debt_service)}</div>
            </div>
            <div class="ds-finance-item">
                <div class="ds-finance-item__label">NOI after Debt</div>
                <div class="ds-finance-item__value ${finance.noi_after_debt_service < 0 ? 'text-danger' : ''}">${formatCurrency(finance.noi_after_debt_service)}</div>
            </div>
            ${expenses ? `
                <div class="ds-finance-item">
                    <div class="ds-finance-item__label">Total Expenses</div>
                    <div class="ds-finance-item__value">${formatCurrency(expenses.total_annual_expenses)}</div>
                </div>
                <div class="ds-finance-item">
                    <div class="ds-finance-item__label">Expense Ratio</div>
                    <div class="ds-finance-item__value">${formatPercent(expenses.expense_ratio_pct)}</div>
                </div>
            ` : ''}
        </div>
    `;
}

function renderDealSnapReverse(reverse) {
    const content = document.getElementById('ds-reverse-content');
    if (!content || !reverse) return;

    content.innerHTML = `
        <div class="ds-reverse-grid">
            <div class="ds-reverse-card">
                <div class="ds-reverse-card__label">Break-Even Rent</div>
                <div class="ds-reverse-card__value">${formatCurrency(reverse.breakeven_rent_per_unit)}</div>
                <div class="ds-reverse-card__hint">per unit/month to cover all costs</div>
            </div>
            <div class="ds-reverse-card">
                <div class="ds-reverse-card__label">Max Price for 7% Cap</div>
                <div class="ds-reverse-card__value">${formatCurrency(reverse.max_price_at_target_cap)}</div>
                <div class="ds-reverse-card__hint">at 7% cap rate target</div>
            </div>
            <div class="ds-reverse-card">
                <div class="ds-reverse-card__label">Required NOI for 1.25x DSCR</div>
                <div class="ds-reverse-card__value">${formatCurrency(reverse.noi_needed_for_dscr_125)}</div>
                <div class="ds-reverse-card__hint">to achieve healthy DSCR</div>
            </div>
        </div>
    `;
}

function renderDealSnapRentSensitivity(sensitivity) {
    const card = document.getElementById('ds-rent-sensitivity');
    const content = document.getElementById('ds-rent-sensitivity-content');
    if (!card || !content || !sensitivity) return;

    card.classList.remove('hidden');

    content.innerHTML = `
        <p class="text-muted text-sm mb-md">
            Lift: $${sensitivity.lift_dollar_per_unit}/unit (${formatPercent(sensitivity.lift_pct)})
            | New Rent: ${formatCurrency(sensitivity.new_rent_per_unit)}/unit
        </p>
        <div class="ds-finance-grid mb-lg">
            <div class="ds-finance-item">
                <div class="ds-finance-item__label">New GPR</div>
                <div class="ds-finance-item__value">${formatCurrency(sensitivity.new_gpr)}</div>
            </div>
            <div class="ds-finance-item">
                <div class="ds-finance-item__label">New NOI</div>
                <div class="ds-finance-item__value">${formatCurrency(sensitivity.new_noi)}</div>
            </div>
            <div class="ds-finance-item">
                <div class="ds-finance-item__label">New Cap Rate</div>
                <div class="ds-finance-item__value">${formatPercent(sensitivity.new_cap_rate)}</div>
            </div>
            <div class="ds-finance-item">
                <div class="ds-finance-item__label">New DSCR</div>
                <div class="ds-finance-item__value">${formatNumber(sensitivity.new_dscr)}x</div>
            </div>
            <div class="ds-finance-item">
                <div class="ds-finance-item__label">NOI Delta</div>
                <div class="ds-finance-item__value text-success">+${formatCurrency(sensitivity.noi_delta)}</div>
            </div>
        </div>
    `;
}

function renderDealSnapNotes(results) {
    const list = document.getElementById('ds-investor-notes-list');
    if (!list) return;

    const notes = [];
    const income = results.income;
    const expenses = results.expenses;
    const finance = results.finance_reality_check;
    const triage = results.deal_triage;
    const reverse = results.reverse_engineering;

    // Cap rate assessment
    if (income?.cap_rate >= 8) {
        notes.push({ type: 'positive', text: `Strong cap rate of ${formatPercent(income.cap_rate)} indicates good income relative to price.` });
    } else if (income?.cap_rate >= 6) {
        notes.push({ type: 'info', text: `Cap rate of ${formatPercent(income.cap_rate)} is moderate - acceptable for stable markets.` });
    } else if (income?.cap_rate > 0) {
        notes.push({ type: 'warning', text: `Low cap rate of ${formatPercent(income.cap_rate)} - price may be high relative to income.` });
    }

    // DSCR assessment
    if (finance?.dscr >= 1.25) {
        notes.push({ type: 'positive', text: `DSCR of ${formatNumber(finance.dscr)}x exceeds the 1.25x threshold for healthy debt coverage.` });
    } else if (finance?.dscr >= 1.0) {
        notes.push({ type: 'warning', text: `DSCR of ${formatNumber(finance.dscr)}x is tight - property barely covers debt service. Limited margin of safety.` });
    } else if (finance?.dscr > 0) {
        notes.push({ type: 'negative', text: `DSCR of ${formatNumber(finance.dscr)}x is below 1.0 - NOI does not cover debt service. Negative cash flow expected.` });
    }

    // Expense ratio
    if (expenses?.expense_ratio_pct <= 35) {
        notes.push({ type: 'positive', text: `Expense ratio of ${formatPercent(expenses.expense_ratio_pct)} is low - efficient operations.` });
    } else if (expenses?.expense_ratio_pct <= 45) {
        notes.push({ type: 'info', text: `Expense ratio of ${formatPercent(expenses.expense_ratio_pct)} is within normal range.` });
    } else if (expenses?.expense_ratio_pct > 45) {
        notes.push({ type: 'warning', text: `High expense ratio of ${formatPercent(expenses.expense_ratio_pct)} - review expense assumptions.` });
    }

    // GRM
    if (income?.grm <= 10) {
        notes.push({ type: 'positive', text: `GRM of ${formatNumber(income.grm, 1)} is favorable - good income per dollar of price.` });
    } else if (income?.grm > 15) {
        notes.push({ type: 'warning', text: `GRM of ${formatNumber(income.grm, 1)} is high - property may be overpriced relative to gross rents.` });
    }

    // Break-even rent vs actual rent
    if (reverse?.breakeven_rent_per_unit && income?.gpr_annual) {
        const actualRent = income.gpr_annual / (results.income?.units || 1) / 12;
        if (reverse.breakeven_rent_per_unit > actualRent) {
            notes.push({ type: 'negative', text: `Break-even rent (${formatCurrency(reverse.breakeven_rent_per_unit)}/unit) exceeds current rent. Property loses money as-is.` });
        } else {
            const margin = ((actualRent - reverse.breakeven_rent_per_unit) / actualRent * 100).toFixed(0);
            notes.push({ type: 'info', text: `${margin}% margin above break-even rent of ${formatCurrency(reverse.breakeven_rent_per_unit)}/unit.` });
        }
    }

    // Overall triage
    if (triage?.verdict === 'Pursue') {
        notes.push({ type: 'positive', text: `Overall: Deal scores ${triage.total_score}/12 - worth pursuing for detailed underwriting.` });
    } else if (triage?.verdict === 'Watch') {
        notes.push({ type: 'warning', text: `Overall: Deal scores ${triage.total_score}/12 - worth monitoring but has areas of concern.` });
    } else if (triage?.verdict === 'Pass') {
        notes.push({ type: 'negative', text: `Overall: Deal scores ${triage.total_score}/12 - does not meet minimum thresholds. Consider passing.` });
    }

    if (notes.length === 0) {
        notes.push({ type: 'info', text: 'Run the analysis to generate investor insights.' });
    }

    const iconMap = {
        positive: '&#x2705;',
        warning: '&#x26A0;&#xFE0F;',
        negative: '&#x274C;',
        info: '&#x2139;&#xFE0F;'
    };

    list.innerHTML = notes.map(note => `
        <li class="investor-note investor-note--${note.type}">
            <span class="investor-note__icon">${iconMap[note.type]}</span>
            <span>${note.text}</span>
        </li>
    `).join('');
}

// ============================================================================
// MODAL HANDLING
// ============================================================================

function showNewDealModal() {
    const modal = document.getElementById('new-deal-modal');
    modal.classList.add('modal-overlay--visible');
    document.getElementById('new-deal-name').value = '';
    document.getElementById('new-deal-name').focus();
    AppState.selectedModel = 'standard';
    updateModelSelection();
}

function hideNewDealModal() {
    const modal = document.getElementById('new-deal-modal');
    modal.classList.remove('modal-overlay--visible');
}

function updateModelSelection() {
    document.querySelectorAll('.model-option').forEach(opt => {
        opt.classList.toggle('model-option--selected', opt.dataset.model === AppState.selectedModel);
    });
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    loadState();
    updateUI();

    // New deal buttons
    document.getElementById('new-deal-btn')?.addEventListener('click', showNewDealModal);
    document.getElementById('empty-new-deal-btn')?.addEventListener('click', showNewDealModal);
    document.getElementById('add-deal-tab')?.addEventListener('click', showNewDealModal);

    // Modal controls
    document.getElementById('cancel-new-deal')?.addEventListener('click', hideNewDealModal);
    document.getElementById('create-deal-btn')?.addEventListener('click', () => {
        const name = document.getElementById('new-deal-name').value.trim();
        if (!name) {
            document.getElementById('new-deal-name').focus();
            showWarning('Please enter a property name');
            return;
        }
        createDeal(name, AppState.selectedModel);
        hideNewDealModal();
    });

    // Model option selection
    document.querySelectorAll('.model-option').forEach(opt => {
        opt.addEventListener('click', () => {
            AppState.selectedModel = opt.dataset.model;
            updateModelSelection();
        });
    });

    // Close modal on overlay click
    document.getElementById('new-deal-modal')?.addEventListener('click', (e) => {
        if (e.target.id === 'new-deal-modal') {
            hideNewDealModal();
        }
    });

    // Navigation
    document.querySelectorAll('.nav-item[data-view]').forEach(item => {
        item.addEventListener('click', () => {
            AppState.currentView = item.dataset.view;
            updateUI();
        });
    });

    // Category filters
    document.querySelectorAll('.category-filter').forEach(filter => {
        filter.addEventListener('click', () => {
            AppState.categoryFilter = filter.dataset.filter;
            document.querySelectorAll('.category-filter').forEach(f => {
                f.classList.toggle('category-filter--active', f.dataset.filter === AppState.categoryFilter);
            });
            renderDealsGrid();
        });
    });

    // Property tabs
    document.querySelectorAll('.property-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            switchPropertyTab(tab.dataset.tab);
        });
    });

    // DealSnap Run button
    document.getElementById('run-dealsnap-btn')?.addEventListener('click', runDealSnap);

    // Calculate button
    document.getElementById('calculate-btn')?.addEventListener('click', async () => {
        const deal = getActiveDeal();
        if (deal) {
            const results = await calculateDeal(deal);
            if (results) {
                switchPropertyTab('results');
                renderResults(deal);
                renderProForma(deal);
            }
        }
    });

    // Reset button
    document.getElementById('reset-deal-btn')?.addEventListener('click', () => {
        const deal = getActiveDeal();
        if (deal) {
            if (!confirm('Reset this deal to default values? This will clear all your inputs.')) {
                return;
            }
            const name = deal.name;
            const model = deal.model;
            const id = deal.id;
            const status = deal.status;
            const createdAt = deal.createdAt;

            const defaults = getDefaultDeal(name, model);
            Object.assign(deal, defaults, { id, name, model, status, createdAt });
            deal.results = null;
            saveState();
            bindDealForm(deal);
            renderExpenses(deal);
            showSuccess('Deal reset to defaults');
        }
    });

    // Add expense button
    document.getElementById('add-expense-btn')?.addEventListener('click', addExpense);

    // Comparison controls
    document.getElementById('clear-comparison')?.addEventListener('click', clearComparison);
    document.getElementById('view-comparison-btn')?.addEventListener('click', () => {
        AppState.currentView = 'comparison';
        updateUI();
    });
    document.getElementById('nav-comparison-btn')?.addEventListener('click', () => {
        AppState.currentView = 'comparison';
        updateUI();
    });

    // Back from comparison view
    document.getElementById('back-from-comparison')?.addEventListener('click', () => {
        AppState.currentView = 'deals';
        updateUI();
    });

    // Navigation helper
    window.app = {
        navigateTo: (view) => {
            AppState.currentView = view;
            updateUI();
        }
    };

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideNewDealModal();
        }
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            showNewDealModal();
        }
    });

    // Enter to create deal in modal
    document.getElementById('new-deal-name')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('create-deal-btn').click();
        }
    });
});
