// Steam Game Scraper Web UI JavaScript

class SteamScraperUI {
    constructor() {
        this.socket = null;
        this.selectedDatabase = null;
        this.searchResults = [];
        this.init();
    }

    init() {
        this.initSocketIO();
        this.initEventListeners();
        this.loadDatabases();
        this.setDefaultDates();
    }

    initSocketIO() {
        console.log('Initializing Socket.IO...');
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
        });

        this.socket.on('scraping_update', (data) => {
            console.log('Scraping update received:', data);
            this.updateScrapingProgress(data);
        });

        this.socket.on('error', (data) => {
            console.log('Socket error:', data);
            this.showToast('Error', data.message, 'error');
        });
    }

    initEventListeners() {
        // Set default date range (last 2 years)
        const today = new Date();
        const twoYearsAgo = new Date(today.getFullYear() - 2, today.getMonth(), today.getDate());
        
        document.getElementById('start-date').value = twoYearsAgo.toISOString().split('T')[0];
        document.getElementById('end-date').value = today.toISOString().split('T')[0];
    }

    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('connection-status');
        const statusText = document.getElementById('status-text');
        
        if (connected) {
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'Connected';
        } else {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = 'Disconnected';
        }
    }

    setDefaultDates() {
        const today = new Date();
        const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
        
        document.getElementById('start-date').value = oneYearAgo.toISOString().split('T')[0];
        document.getElementById('end-date').value = today.toISOString().split('T')[0];
    }

    async loadDatabases() {
        try {
            const response = await fetch('/api/databases');
            const databases = await response.json();
            
            const container = document.getElementById('database-list');
            
            if (databases.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-database" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 1rem;"></i>
                        <p>No databases found. Run the scraper first to create databases.</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = databases.map(db => `
                <div class="database-card" onclick="selectDatabase('${db.filename}')">
                    <div class="database-name">
                        <i class="fas fa-database"></i>
                        ${db.name}
                    </div>
                    <div class="database-stats">
                        <span>${db.game_count} games</span>
                        <span>${db.size_mb} MB</span>
                    </div>
                </div>
            `).join('');
            
        } catch (error) {
            console.error('Error loading databases:', error);
            this.showToast('Error', 'Failed to load databases', 'error');
        }
    }

    selectDatabase(filename) {
        this.selectedDatabase = filename;
        
        // Update database path input if it exists
        const dbPathInput = document.getElementById('database-path');
        if (dbPathInput) {
            dbPathInput.value = filename;
        }
        
        // Update UI
        document.querySelectorAll('.database-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Find and select the clicked card
        const cards = document.querySelectorAll('.database-card');
        cards.forEach(card => {
            if (card.textContent.includes(filename)) {
                card.classList.add('selected');
            }
        });
        
        this.showToast('Database Selected', `Selected database: ${filename}`, 'success');
    }

    async searchGames() {
        if (!this.selectedDatabase) {
            this.showToast('Error', 'Please select a database first', 'warning');
            return;
        }

        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;

        if (!startDate || !endDate) {
            this.showToast('Error', 'Please select start and end dates', 'warning');
            return;
        }

        try {
            // Format dates for display
            const startFormatted = new Date(startDate).toLocaleDateString('en-US', { 
                month: 'long', day: 'numeric', year: 'numeric' 
            });
            const endFormatted = new Date(endDate).toLocaleDateString('en-US', { 
                month: 'long', day: 'numeric', year: 'numeric' 
            });
            
            this.showToast('Searching', `Searching for games released between ${startFormatted} and ${endFormatted}...`, 'info');
            
            const response = await fetch('/api/search_games', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    database: this.selectedDatabase,
                    start_date: startDate,
                    end_date: endDate
                })
            });

            if (!response.ok) {
                throw new Error('Search failed');
            }

            this.searchResults = await response.json();
            this.displaySearchResults();
            
        } catch (error) {
            console.error('Search error:', error);
            this.showToast('Error', 'Search failed', 'error');
        }
    }

    displaySearchResults() {
        const resultsSection = document.getElementById('search-results-section');
        const summary = document.getElementById('results-summary');
        const tbody = document.getElementById('results-tbody');

        if (this.searchResults.length === 0) {
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            const startFormatted = new Date(startDate).toLocaleDateString('en-US', { 
                month: 'long', day: 'numeric', year: 'numeric' 
            });
            const endFormatted = new Date(endDate).toLocaleDateString('en-US', { 
                month: 'long', day: 'numeric', year: 'numeric' 
            });
            
            summary.innerHTML = `
                <p>No games found with release dates between <strong>${startFormatted}</strong> and <strong>${endFormatted}</strong>.</p>
                <p><small>Note: Only games with specific dates (e.g., "16 Oct, 2025") or month/year (e.g., "October 2025") are included. 
                Vague dates like "2025", "Q1 2025", or "TBA" are excluded from search results.</small></p>
            `;
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No results</td></tr>';
            resultsSection.style.display = 'block';
            return;
        }

        // Group results by release date format for summary
        const specificDates = this.searchResults.filter(game => game.release_date.match(/\d{1,2}\s+\w{3},\s+\d{4}/));
        const monthYearDates = this.searchResults.filter(game => game.release_date.match(/^\w+\s+\d{4}$/));
        
        // Update summary
        summary.innerHTML = `
            <p><strong>${this.searchResults.length}</strong> games found matching your date criteria:</p>
            <ul style="margin: 0.5rem 0; padding-left: 1.5rem; color: var(--text-secondary);">
                <li>${specificDates.length} games with specific dates (e.g., "16 Oct, 2025")</li>
                <li>${monthYearDates.length} games with month/year dates (e.g., "October 2025")</li>
            </ul>
        `;

        // Update table
        tbody.innerHTML = this.searchResults.map(game => `
            <tr>
                <td>${game.app_id}</td>
                <td title="${game.name}">${this.truncateText(game.name, 40)}</td>
                <td title="${game.developer}">${this.truncateText(game.developer, 25)}</td>
                <td title="${game.publisher}">${this.truncateText(game.publisher, 25)}</td>
                <td><strong>${game.release_date}</strong></td>
                <td>$${game.price || '0.00'}</td>
            </tr>
        `).join('');

        resultsSection.style.display = 'block';
        this.showToast('Search Complete', `Found ${this.searchResults.length} games with valid release dates`, 'success');
    }

    async exportResults() {
        if (this.searchResults.length === 0) {
            this.showToast('Error', 'No results to export', 'warning');
            return;
        }

        const format = document.getElementById('export-format').value;
        
        // Get date range for filename
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        // Format dates for filename
        const startDateFormatted = new Date(startDate).toLocaleDateString('en-GB', { 
            day: '2-digit', month: 'short', year: 'numeric' 
        }).replace(/ /g, '-');
        const endDateFormatted = new Date(endDate).toLocaleDateString('en-GB', { 
            day: '2-digit', month: 'short', year: 'numeric' 
        }).replace(/ /g, '-');
        
        const dbName = this.selectedDatabase ? this.selectedDatabase.replace('.db', '') : 'search_results';
        const filename = `${dbName}_${startDateFormatted}_to_${endDateFormatted}`;

        try {
            this.showToast('Exporting', 'Preparing your download...', 'info');
            
            // Get app_ids from search results
            const appIds = this.searchResults.map(game => game.app_id);
            
            const response = await fetch('/api/export_search_results', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    database: this.selectedDatabase,
                    app_ids: appIds,
                    format: format,
                    filename: filename,
                    start_date: startDate,
                    end_date: endDate
                })
            });

            if (!response.ok) {
                throw new Error('Export failed');
            }

            // Check if response is a file download
            const contentDisposition = response.headers.get('Content-Disposition');
            if (contentDisposition) {
                // It's a file download - create blob and trigger download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                
                // Extract filename from Content-Disposition header
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                const downloadFilename = filenameMatch ? filenameMatch[1] : `${filename}.${format}`;
                
                a.download = downloadFilename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showToast('Download Started', `Your file ${downloadFilename} is downloading`, 'success');
            } else {
                // Handle error response
                const result = await response.json();
                throw new Error(result.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error('Export error:', error);
            this.showToast('Error', 'Export failed: ' + error.message, 'error');
        }
    }

    startScraping() {
        console.log('startScraping function called');
        const url = document.getElementById('steam-url').value.trim();
        const database = document.getElementById('database-name').value.trim();

        console.log('URL:', url);
        console.log('Database:', database);

        if (!url) {
            this.showToast('Error', 'Please enter a Steam URL', 'warning');
            return;
        }

        if (!database) {
            this.showToast('Error', 'Please enter a database name', 'warning');
            return;
        }

        console.log('Socket available:', !!this.socket);
        
        // Update UI
        document.getElementById('start-scraping').disabled = true;
        document.getElementById('pause-scraping').disabled = false;
        document.getElementById('stop-scraping').disabled = false;
        document.getElementById('progress-section').style.display = 'block';

        // Send scraping request via Socket.IO
        console.log('Emitting start_scraping event');
        this.socket.emit('start_scraping', {
            url: url,
            database: database
        });

        this.showToast('Scraping Started', 'Game scraping has been initiated', 'info');
    }

    stopScraping() {
        this.socket.emit('stop_scraping');
        
        // Update UI
        document.getElementById('start-scraping').disabled = false;
        document.getElementById('stop-scraping').disabled = true;
        
        this.showToast('Stopping', 'Scraping is being stopped...', 'warning');
    }

    updateScrapingProgress(data) {
        document.getElementById('scraping-status').textContent = data.status_message;
        document.getElementById('current-game').textContent = data.current_game || '-';
        document.getElementById('progress-text').textContent = `${data.progress}%`;
        document.getElementById('progress-fill').style.width = `${data.progress}%`;

        // Update statistics
        if (data.total_games !== undefined) {
            document.getElementById('total-games-count').textContent = data.total_games;
        }
        if (data.existing_games !== undefined) {
            document.getElementById('existing-games-count').textContent = data.existing_games;
        }
        if (data.scraped_count !== undefined) {
            document.getElementById('new-games-count').textContent = data.scraped_count;
        }

        // Update button states
        if (!data.is_active) {
            document.getElementById('start-scraping').disabled = false;
            document.getElementById('pause-scraping').disabled = true;
            document.getElementById('stop-scraping').disabled = true;
            
            if (data.progress === 100) {
                this.showToast('Scraping Complete', 'All games have been scraped successfully!', 'success');
                this.loadDatabases(); // Refresh database list
            }
        }
    }

    refreshDatabases() {
        this.loadDatabases();
        this.showToast('Refreshed', 'Database list has been refreshed', 'info');
    }

    exportScrapedData() {
        console.log('Exporting scraped data');
        
        const dbName = document.getElementById('database-name').value.trim();
        if (!dbName) {
            this.showToast('Error', 'Please enter a database name', 'warning');
            return;
        }
        
        // Get selected export format from dropdown
        const formatSelect = document.getElementById('scraper-export-format');
        const format = formatSelect ? formatSelect.value : 'csv';
        
        // Create filename based on database name
        const filename = dbName.endsWith('.db') ? dbName.replace('.db', '') : dbName;
        
        const exportData = {
            database: dbName.endsWith('.db') ? dbName : `${dbName}.db`,
            format: format,
            filename: filename
        };
        
        this.exportDatabaseData(exportData);
    }
    
    async exportDatabaseData(exportData) {
        try {
            this.showToast('Exporting', 'Preparing your download...', 'info');
            
            const response = await fetch('/api/export_database', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(exportData)
            });

            if (!response.ok) {
                throw new Error('Export failed');
            }

            // Check if response is a file download
            const contentDisposition = response.headers.get('Content-Disposition');
            if (contentDisposition) {
                // It's a file download - create blob and trigger download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                
                // Extract filename from Content-Disposition header
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                const filename = filenameMatch ? filenameMatch[1] : `${exportData.filename}.${exportData.format}`;
                
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showToast('Download Started', `Your file ${filename} is downloading`, 'success');
            } else {
                // Handle error response
                const result = await response.json();
                throw new Error(result.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error('Export error:', error);
            this.showToast('Error', 'Export failed: ' + error.message, 'error');
        }
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    showToast(title, message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toastId = 'toast-' + Date.now();
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="${icons[type]} toast-icon"></i>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="closeToast('${toastId}')">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            this.closeToast(toastId);
        }, 5000);
    }

    closeToast(toastId) {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                toast.remove();
            }, 300);
        }
    }
}

// Global functions for HTML onclick events
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update content sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(tabName + '-section').classList.add('active');
}

function setPresetUrl(url) {
    console.log('Setting preset URL:', url);
    const urlInput = document.getElementById('steam-url');
    
    if (url && urlInput) {
        urlInput.value = url;
        app.showToast('URL Set', 'Preset URL has been applied', 'success');
    }
}

function selectDatabase(filename) {
    app.selectDatabase(filename);
}

function refreshDatabases() {
    app.refreshDatabases();
}

function searchGames() {
    app.searchGames();
}

function exportResults() {
    app.exportResults();
}

function startScraping() {
    console.log('Global startScraping function called');
    console.log('App instance available:', !!app);
    if (app) {
        app.startScraping();
    } else {
        console.error('App instance not available!');
        alert('Application not ready. Please refresh the page.');
    }
}

function stopScraping() {
    app.stopScraping();
}

function pauseScraping() {
    console.log('Pause scraping function called');
    app.showToast('Pause Feature', 'Pause functionality coming soon!', 'info');
}

function exportScrapedData() {
    console.log('Export scraped data function called');
    app.exportScrapedData();
}

function handleDatabaseFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        document.getElementById('database-path').value = file.name;
        app.showToast('File Selected', `Selected: ${file.name}`, 'success');
    }
}

function connectToDatabase() {
    const dbPath = document.getElementById('database-path').value;
    if (dbPath) {
        app.selectDatabase(dbPath);
    } else {
        app.showToast('Error', 'Please select a database file first', 'warning');
    }
}

function closeToast(toastId) {
    app.closeToast(toastId);
}

// Add custom CSS for slide out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: var(--text-muted);
    }
`;
document.head.appendChild(style);

// Initialize the application
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new SteamScraperUI();
});