from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import os
import sqlite3
import json
import threading
import time
from datetime import datetime, timedelta
import logging
import re
from steam_scraper import SteamScraper
def parse_steam_date_to_comparable(date_str):
    """Parse Steam date to a comparable date, return None if too vague"""
    if not date_str or date_str.strip() in ['Unknown', 'TBA', 'TBD', 'Coming Soon']:
        return None
        
    date_str = date_str.strip()
    
    # Skip vague dates immediately
    if re.match(r'^\d{4}$', date_str):  # Just year like "2025"
        return None
    if re.match(r'Q[1-4]\s+\d{4}', date_str):  # Quarter like "Q1 2025"
        return None
    
    try:
        # Handle "16 Oct, 2025" format - SPECIFIC DATE
        if re.match(r'\d{1,2}\s+\w{3},\s+\d{4}', date_str):
            return datetime.strptime(date_str, "%d %b, %Y")
            
        # Handle "Oct 16, 2025" format - SPECIFIC DATE
        if re.match(r'\w{3}\s+\d{1,2},\s+\d{4}', date_str):
            return datetime.strptime(date_str, "%b %d, %Y")
            
        # Handle "October 16, 2025" format - SPECIFIC DATE
        if re.match(r'\w+\s+\d{1,2},\s+\d{4}', date_str):
            return datetime.strptime(date_str, "%B %d, %Y")

        # Handle "October 2025" format - MONTH AND YEAR (use first day)
        if re.match(r'^\w+\s+\d{4}$', date_str):
            try:
                return datetime.strptime(date_str, "%B %Y")
            except ValueError:
                return datetime.strptime(date_str, "%b %Y")

        return None
        
    except Exception as e:
        logger.error(f"Date parsing error for '{date_str}': {e}")
        return None

def is_steam_date_in_range(release_date, start_date_str, end_date_str):
    """Simple, robust date range checking"""
    release_dt = parse_steam_date_to_comparable(release_date)
    
    if not release_dt:
        return False
        
    try:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        # Check if it's a month-only date (like "October 2025")
        original_date = release_date.strip()
        month_patterns = [r'^\w+\s+\d{4}$']  # "October 2025" or "Oct 2025"
        
        is_month_only = any(re.match(pattern, original_date) for pattern in month_patterns)
        
        if is_month_only:
            # For month-only dates, check if the ENTIRE month overlaps with the range
            month_start = release_dt.replace(day=1)
            # Get last day of the month
            if release_dt.month == 12:
                month_end = release_dt.replace(year=release_dt.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = release_dt.replace(month=release_dt.month + 1, day=1) - timedelta(days=1)
            
            # Check if ANY part of the month overlaps with the search range
            return not (month_end < start_dt or month_start > end_dt)
        else:
            # For specific dates, simple comparison
            return start_dt <= release_dt <= end_dt
            
    except Exception as e:
        logger.error(f"Date comparison error for '{release_date}': {e}")
        return False
import glob

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for scraping status
scraping_status = {
    'is_active': False,
    'current_game': '',
    'progress': 0,
    'total_games': 0,
    'existing_games': 0,
    'scraped_count': 0,
    'status_message': 'Ready'
}

class WebScraper:
    def __init__(self):
        self.scraper = None
        self.is_running = False
        
    def start_scraping(self, url, db_name, socketio_instance):
        """Start the scraping process with real-time updates"""
        global scraping_status
        
        try:
            logger.info(f"WebScraper.start_scraping called with URL: {url}, DB: {db_name}")
            
            scraping_status['is_active'] = True
            scraping_status['status_message'] = 'Initializing scraper...'
            socketio_instance.emit('scraping_update', scraping_status)
            
            logger.info("Initializing SteamScraper...")
            # Initialize scraper
            self.scraper = SteamScraper(url, db_name)
            logger.info("SteamScraper initialized, starting driver...")
            self.scraper.initialize_driver()
            logger.info("Driver initialized successfully")
            
            # Get existing games count
            existing_games = self.scraper.get_existing_app_ids()
            logger.info(f"Found {len(existing_games)} existing games")
            
            scraping_status['existing_games'] = len(existing_games)
            socketio_instance.emit('scraping_update', scraping_status)
            
            scraping_status['status_message'] = 'Collecting game links...'
            socketio_instance.emit('scraping_update', scraping_status)
            
            # Get game links
            logger.info("Starting to collect game links...")
            game_links = self.scraper.scroll_and_collect_games()
            logger.info(f"Collected {len(game_links)} game links")
            
            scraping_status['total_games'] = len(game_links)
            scraping_status['scraped_count'] = 0
            
            # Update total including existing games
            total_with_existing = len(game_links) + scraping_status['existing_games']
            scraping_status['total_games'] = total_with_existing
            socketio_instance.emit('scraping_update', scraping_status)
            
            if len(game_links) == 0:
                scraping_status['is_active'] = False
                scraping_status['status_message'] = 'No new games found to scrape.'
                socketio_instance.emit('scraping_update', scraping_status)
                logger.warning("No game links found")
                return
            
            # Start scraping individual games
            for i, link in enumerate(game_links):
                if not scraping_status['is_active']:  # Check if user stopped
                    logger.info("Scraping stopped by user")
                    break
                    
                scraping_status['current_game'] = f"Game {i+1} of {len(game_links)}"
                scraping_status['progress'] = int((i / len(game_links)) * 100)
                scraping_status['scraped_count'] = i
                scraping_status['status_message'] = f'Scraping: {scraping_status["current_game"]}'
                
                # Emit update
                socketio_instance.emit('scraping_update', scraping_status)
                logger.info(f"Scraping game {i+1}/{len(game_links)}: {link}")
                
                # Scrape the game
                result = self.scraper.scrape_game_details(link)
                if result:
                    logger.info(f"Successfully scraped: {result.get('name', 'Unknown')}")
                else:
                    logger.warning(f"Failed to scrape: {link}")
                    
                time.sleep(1)  # Small delay to prevent overwhelming
                
            scraping_status['is_active'] = False
            scraping_status['status_message'] = f'Completed! Scraped {len(game_links)} games.'
            scraping_status['progress'] = 100
            socketio_instance.emit('scraping_update', scraping_status)
            logger.info("Scraping completed successfully")
            
        except Exception as e:
            scraping_status['is_active'] = False
            scraping_status['status_message'] = f'Error: {str(e)}'
            socketio_instance.emit('scraping_update', scraping_status)
            logger.error(f"Scraping error: {e}", exc_info=True)
        finally:
            if self.scraper:
                logger.info("Closing scraper resources...")
                self.scraper.close_all()

web_scraper = WebScraper()

@app.route('/')
def index():
    """Main page with both scraper and search functionality"""
    return render_template('index.html')

@app.route('/api/databases')
def get_databases():
    """Get list of available database files"""
    try:
        db_files = glob.glob('*.db')
        databases = []
        
        for db_file in db_files:
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM games")
                count = cursor.fetchone()[0]
                conn.close()
                
                # Get file size
                size = os.path.getsize(db_file) / (1024 * 1024)  # MB
                
                databases.append({
                    'filename': db_file,
                    'name': db_file.replace('.db', '').replace('_', ' ').title(),
                    'game_count': count,
                    'size_mb': round(size, 1)
                })
            except Exception as e:
                logger.error(f"Error reading database {db_file}: {e}")
                
        return jsonify(databases)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search_games', methods=['POST'])
def search_games():
    """Search games in database by date range"""
    try:
        data = request.json
        db_name = data.get('database')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not db_name or not os.path.exists(db_name):
            return jsonify({'error': 'Database not found'}), 400
            
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Get all games and filter by date
        cursor.execute('SELECT app_id, name, developer, publisher, release_date, price FROM games')
        all_games = cursor.fetchall()
        
        logger.info(f"Filtering games between {start_date} and {end_date}")
        
        filtered_games = []
        for game in all_games:
            release_date = game[4]
            if release_date and is_steam_date_in_range(release_date, start_date, end_date):
                logger.info(f"Including game: {game[1]} with date: {release_date}")
                filtered_games.append({
                    'app_id': game[0],
                    'name': game[1],
                    'developer': game[2],
                    'publisher': game[3],
                    'release_date': game[4],
                    'price': game[5]
                })
            else:
                if release_date and release_date != 'Unknown':
                    logger.debug(f"Excluding game: {game[1]} with date: {release_date}")
        
        conn.close()
        return jsonify(filtered_games)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export_database', methods=['POST'])
def export_database():
    """Export entire database to file"""
    try:
        data = request.json
        db_name = data.get('database')
        format_type = data.get('format', 'csv')
        filename = data.get('filename', 'database_export')
        
        if not db_name or not os.path.exists(db_name):
            return jsonify({'error': 'Database not found'}), 400
            
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Get all games with tags
        cursor.execute('''
            SELECT g.*, GROUP_CONCAT(DISTINCT t.tag) as tags
            FROM games g
            LEFT JOIN tags t ON g.app_id = t.app_id
            GROUP BY g.app_id
        ''')
        games = cursor.fetchall()
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        conn.close()
        
        # Prepare data for export
        output_path = f"{filename}.{format_type}"
        
        if format_type == 'csv':
            import csv
            output_path = f"{filename}.csv"
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(games)
                
        elif format_type == 'json':
            output_path = f"{filename}.json"
            json_data = []
            for row in games:
                json_data.append(dict(zip(columns, row)))
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                
        elif format_type == 'excel':
            import pandas as pd
            output_path = f"{filename}.xlsx"
            df = pd.DataFrame(games, columns=columns)
            df.to_excel(output_path, index=False, engine='openpyxl')
            
        return jsonify({'message': f'Successfully exported to {output_path}', 'filename': output_path})
        
    except Exception as e:
        logger.error(f"Database export error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export_search_results', methods=['POST'])
def export_search_results():
    """Export search results with complete database fields"""
    try:
        data = request.json
        db_name = data.get('database')
        app_ids = data.get('app_ids', [])
        format_type = data.get('format', 'csv')
        filename = data.get('filename', 'search_results')
        
        if not db_name or not os.path.exists(db_name):
            return jsonify({'error': 'Database not found'}), 400
            
        if not app_ids:
            return jsonify({'error': 'No games to export'}), 400
            
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Get complete data for these games with tags
        placeholders = ','.join('?' * len(app_ids))
        query = f'''
            SELECT g.*, GROUP_CONCAT(DISTINCT t.tag) as tags
            FROM games g
            LEFT JOIN tags t ON g.app_id = t.app_id
            WHERE g.app_id IN ({placeholders})
            GROUP BY g.app_id
        '''
        
        cursor.execute(query, app_ids)
        games = cursor.fetchall()
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        conn.close()
        
        # Prepare data for export
        if format_type == 'csv':
            import csv
            output_path = f"{filename}.csv"
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(games)
                
        elif format_type == 'json':
            output_path = f"{filename}.json"
            json_data = []
            for row in games:
                json_data.append(dict(zip(columns, row)))
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                
        elif format_type == 'excel':
            import pandas as pd
            output_path = f"{filename}.xlsx"
            df = pd.DataFrame(games, columns=columns)
            df.to_excel(output_path, index=False, engine='openpyxl')
            
        return jsonify({'message': f'Successfully exported {len(games)} games to {output_path}', 'filename': output_path})
        
    except Exception as e:
        logger.error(f"Search results export error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export_games', methods=['POST'])
def export_games():
    """Export search results to file"""
    try:
        data = request.json
        games = data.get('games', [])
        format_type = data.get('format', 'csv')
        filename = data.get('filename', 'search_results')
        
        if not games:
            return jsonify({'error': 'No games to export'}), 400
            
        # Prepare data for export
        output_path = f"{filename}.csv"  # Default to CSV
        
        if format_type == 'csv':
            import csv
            output_path = f"{filename}.csv"
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['App ID', 'Name', 'Developer', 'Publisher', 'Release Date', 'Price'])
                for game in games:
                    writer.writerow([
                        game['app_id'], game['name'], game['developer'], 
                        game['publisher'], game['release_date'], game['price']
                    ])
                    
        elif format_type == 'json':
            output_path = f"{filename}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(games, f, indent=2, ensure_ascii=False)
                
        elif format_type == 'excel':
            import pandas as pd
            output_path = f"{filename}.xlsx"
            df = pd.DataFrame(games)
            df.to_excel(output_path, index=False, engine='openpyxl')
            
        return jsonify({'message': f'Successfully exported to {output_path}', 'filename': output_path})
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({'error': str(e)}), 500

@socketio.on('start_scraping')
def handle_start_scraping(data):
    """Handle scraping start request"""
    global scraping_status
    
    logger.info(f"Received start_scraping request with data: {data}")
    
    if scraping_status['is_active']:
        logger.warning("Scraping already in progress")
        emit('error', {'message': 'Scraping is already in progress'})
        return
        
    url = data.get('url', '').strip()
    db_name = data.get('database', '').strip()
    
    logger.info(f"URL: {url}, Database: {db_name}")
    
    if not url:
        logger.error("No URL provided")
        emit('error', {'message': 'Please provide a valid Steam URL'})
        return
        
    if not db_name:
        logger.error("No database name provided")
        emit('error', {'message': 'Please provide a database name'})
        return
        
    # Ensure database name has .db extension
    if not db_name.endswith('.db'):
        db_name = f"{db_name}.db"
    
    logger.info(f"Starting scraping thread for URL: {url}, DB: {db_name}")
    
    # Start scraping in a separate thread
    thread = threading.Thread(
        target=web_scraper.start_scraping, 
        args=(url, db_name, socketio)
    )
    thread.daemon = True
    thread.start()
    
    logger.info("Scraping thread started successfully")

@socketio.on('stop_scraping')
def handle_stop_scraping():
    """Handle scraping stop request"""
    global scraping_status
    scraping_status['is_active'] = False
    scraping_status['status_message'] = 'Stopping...'
    emit('scraping_update', scraping_status)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected to Socket.IO")
    emit('scraping_update', scraping_status)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from Socket.IO")

if __name__ == '__main__':
    # Ensure templates and static directories exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("🚀 Starting Steam Game Scraper Web UI...")
    print("📱 Access the application at: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)