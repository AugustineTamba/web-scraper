// Constants
const ITEMS_PER_PAGE = 10;
let currentPage = 1;
let currentData = [];

// Utility functions
function showLoading(show = true) {
    document.getElementById('loadingSpinner').classList.toggle('hidden', !show);
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    setTimeout(() => errorDiv.classList.add('hidden'), 5000);
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'} mr-2"></i>
            <div class="flex-1 break-words">${message}</div>
        </div>
        <button onclick="this.parentElement.remove()" class="ml-4 flex-shrink-0">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    const container = document.getElementById('toastContainer');
    container.appendChild(toast);
    
    // Automatically remove the toast after 5 seconds
    setTimeout(() => toast.remove(), 5000);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize search and sort functionality
    document.getElementById('searchInput').addEventListener('input', filterAndSortData);
    document.getElementById('sortSelect').addEventListener('change', filterAndSortData);
    document.getElementById('clearSearch').addEventListener('click', () => {
        document.getElementById('searchInput').value = '';
        document.getElementById('sortSelect').value = 'default';
        filterAndSortData();
    });
    
    // Update copyright year
    document.getElementById('currentYear').textContent = new Date().getFullYear();
    
    // Initialize pagination if there's initial data
    updatePagination();
    
    // Add responsive table handling
    handleResponsiveTable();
    window.addEventListener('resize', handleResponsiveTable);
});

function handleResponsiveTable() {
    const table = document.getElementById('dataTable');
    const cells = table.getElementsByTagName('td');
    
    for (let cell of cells) {
        const content = cell.textContent;
        if (content.length > 50 && window.innerWidth < 640) {
            cell.setAttribute('title', content);
        } else {
            cell.removeAttribute('title');
        }
    }
}

// Form submission
document.getElementById('scrapeForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const url = document.getElementById('url').value.trim();
    
    // Basic URL validation
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        showToast('Please enter a valid URL starting with http:// or https://', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/scrape', {
            method: 'POST',
            body: new FormData(this),
            headers: { 'Accept': 'application/json' }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to scrape data');
        }
        
        currentData = data;
        currentPage = 1;
        updateTable();
        updatePagination();
        showToast('Data scraped successfully!', 'success');
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        showLoading(false);
    }
});

// Data management functions
async function deleteItem(index) {
    try {
        const response = await fetch(`/delete/${index}`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            currentData = currentData.filter((_, i) => i !== index);
            updateTable();
            updatePagination();
            showToast('Item deleted successfully', 'success');
        } else {
            throw new Error('Failed to delete item');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function refreshData() {
    try {
        const response = await fetch('/refresh', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            currentData = [];
            document.getElementById('searchInput').value = '';
            document.getElementById('sortSelect').value = 'default';
            document.getElementById('url').value = '';
            updateTable();
            updatePagination();
            showToast('Data cleared successfully', 'success');
        }
    } catch (error) {
        showToast('Failed to clear data', 'error');
    }
}

function exportData(format) {
    if (currentData.length === 0) {
        showToast('No data to export', 'error');
        return;
    }
    window.location.href = `/export/${format}`;
}

// Table management functions
function filterAndSortData() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const sortBy = document.getElementById('sortSelect').value;
    
    // Get fresh data from server
    fetch('/get-data')  // You'll need to add this endpoint in your Flask app
        .then(response => response.json())
        .then(data => {
            currentData = data;
            
            let filteredData = currentData.filter(item =>
                item.title.toLowerCase().includes(searchTerm) ||
                item.url.toLowerCase().includes(searchTerm)
            );
            
            if (sortBy === 'title') {
                filteredData.sort((a, b) => a.title.localeCompare(b.title));
            } else if (sortBy === 'date') {
                filteredData.sort((a, b) => new Date(b.date) - new Date(a.date));
            }
            
            currentData = filteredData;
            currentPage = 1;
            updateTable();
            updatePagination();
        });
}

function updateTable() {
    const tableBody = document.querySelector('#dataTable tbody');
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const pageData = currentData.slice(start, end);
    
    tableBody.innerHTML = pageData.map((item, index) => `
        <tr class="hover:bg-gray-50">
            <td class="px-3 py-2 sm:px-4 sm:py-3 text-xs sm:text-sm text-gray-900 truncate-mobile">
                ${item.title}
            </td>
            <td class="px-3 py-2 sm:px-4 sm:py-3 text-xs sm:text-sm">
                <a href="${item.url}" 
                   target="_blank" 
                   class="text-blue-600 hover:text-blue-800 truncate-mobile block"
                   title="${item.url}">
                    ${item.url}
                </a>
            </td>
            <td class="px-3 py-2 sm:px-4 sm:py-3 text-xs sm:text-sm text-gray-900">
                ${item.date}
            </td>
            <td class="px-3 py-2 sm:px-4 sm:py-3 text-center">
                <button onclick="deleteItem(${start + index})" 
                        class="text-red-600 hover:text-red-800 p-1">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    handleResponsiveTable();
}

function updatePagination() {
    const totalPages = Math.ceil(currentData.length / ITEMS_PER_PAGE);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let buttons = [];
    
    // Previous button
    buttons.push(`
        <button 
            onclick="changePage(${currentPage - 1})" 
            class="pagination-button ${currentPage === 1 ? 'opacity-50 cursor-not-allowed' : ''}"
            ${currentPage === 1 ? 'disabled' : ''}
        >
            <i class="fas fa-chevron-left"></i>
        </button>
    `);
    
    // Page buttons
    for (let i = 1; i <= totalPages; i++) {
        if (
            i === 1 || 
            i === totalPages || 
            (i >= currentPage - 1 && i <= currentPage + 1)
        ) {
            buttons.push(`
                <button 
                    onclick="changePage(${i})" 
                    class="pagination-button ${i === currentPage ? 'pagination-active' : ''}"
                >
                    ${i}
                </button>
            `);
        } else if (
            i === currentPage - 2 || 
            i === currentPage + 2
        ) {
            buttons.push('<span class="px-1 sm:px-2">...</span>');
        }
    }
    
    // Next button
    buttons.push(`
        <button 
            onclick="changePage(${currentPage + 1})" 
            class="pagination-button ${currentPage === totalPages ? 'opacity-50 cursor-not-allowed' : ''}"
            ${currentPage === totalPages ? 'disabled' : ''}
        >
            <i class="fas fa-chevron-right"></i>
        </button>
    `);
    
    pagination.innerHTML = buttons.join('');
}

function changePage(page) {
    const totalPages = Math.ceil(currentData.length / ITEMS_PER_PAGE);
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    updateTable();
    updatePagination();
}