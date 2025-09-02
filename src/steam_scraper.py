import logging
import json
import csv
import time
import os
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from bs4 import BeautifulSoup
import requests
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steam_scraper.log'),
        logging.StreamHandler()
    ]
)

class SteamScraper:
    def __init__(self, base_url, db_name='steam_games.db'):
        self.base_url = base_url
        self.db_name = db_name
        self.driver = None
        self.db_conn = None
        self.setup_database()
        
    def setup_database(self):
        """Initialize SQLite database and create necessary tables"""
        try:
            self.db_conn = sqlite3.connect(self.db_name)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    app_id INTEGER PRIMARY KEY,
                    name TEXT,
                    developer TEXT,
                    publisher TEXT,
                    release_date TEXT,
                    full_description TEXT,
                    short_description TEXT,
                    price REAL,
                    system_requirements TEXT,
                    supported_languages TEXT,
                    user_rating REAL,
                    review_count INTEGER,
                    steam_url TEXT,
                    header_image TEXT,
                    screenshot1 TEXT,
                    screenshot2 TEXT,
                    screenshot3 TEXT,
                    screenshot4 TEXT,
                    screenshot5 TEXT,
                    last_updated TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id INTEGER,
                    tag TEXT,
                    FOREIGN KEY (app_id) REFERENCES games (app_id)
                )
            ''')
            
            self.db_conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            raise

    def initialize_driver(self):
        """Initialize Selenium WebDriver with appropriate options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        
    def get_existing_app_ids(self):
        """Get list of app IDs already in database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT app_id FROM games")
            return {str(row[0]) for row in cursor.fetchall()}
        except sqlite3.Error as e:
            logging.error(f"Database error getting existing app IDs: {e}")
            return set()

    def scroll_and_collect_games(self):
        """Scroll through the Steam store and collect all game links"""
        try:
            self.driver.get(self.base_url)
            game_links = set()
            existing_apps = self.get_existing_app_ids()
            last_count = 0
            no_new_games_count = 0
            max_attempts = 5  # Maximum number of attempts with no new games
            
            logging.info(f"Found {len(existing_apps)} existing games in database")
            
            while True:
                # Scroll down multiple times to ensure content loads
                for _ in range(3):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)  # Increased wait time
                
                # Wait for elements to be present
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.search_result_row"))
                )
                
                # Get all game links
                elements = self.driver.find_elements(By.CSS_SELECTOR, "a.search_result_row")
                for elem in elements:
                    href = elem.get_attribute('href')
                    if href:
                        app_id = href.split('/')[4]
                        if app_id not in existing_apps:  # Only add if not in database
                            game_links.add(href)
                
                current_count = len(game_links)
                total_games = current_count + len(existing_apps)
                logging.info(f"Found {current_count} new games (Total with existing: {total_games})")
                
                # Check if we're finding new games
                if current_count == last_count:
                    no_new_games_count += 1
                    if no_new_games_count >= max_attempts:
                        logging.info("No new games found after multiple attempts, stopping...")
                        break
                else:
                    no_new_games_count = 0
                
                last_count = current_count
                
                # Additional check for total games count
                try:
                    total_results = self.driver.find_element(By.CLASS_NAME, "search_results_count")
                    if total_results:
                        total_count = int(''.join(filter(str.isdigit, total_results.text)))
                        if total_games >= total_count:
                            logging.info(f"Reached total number of available games ({total_count})")
                            break
                except:
                    pass
            
            logging.info(f"Final collection: {len(game_links)} new games to scrape")
            logging.info(f"Total games (including existing): {len(game_links) + len(existing_apps)}")
            return list(game_links)
        except Exception as e:
            logging.error(f"Error while scrolling: {e}")
            return []

    def scrape_game_details(self, url):
        """Scrape detailed information for a single game"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                app_id = url.split('/')[4]
                
                # Initialize with default values
                game_data = {
                    'app_id': app_id,
                    'steam_url': url,
                    'name': 'Unknown',
                    'developer': 'Unknown',
                    'publisher': 'Unknown',
                    'release_date': 'Unknown',
                    'full_description': '',
                    'short_description': '',
                    'price': 0.0,
                    'system_requirements': '',
                    'tags': [],
                    'supported_languages': '',
                    'user_rating': None,
                    'review_count': 0,
                    'header_image': '',
                    'screenshot1': '',
                    'screenshot2': '',
                    'screenshot3': '',
                    'screenshot4': '',
                    'screenshot5': ''
                }
                
                # Safely extract elements
                name_elem = soup.select_one('.apphub_AppName')
                if name_elem:
                    game_data['name'] = name_elem.text.strip()
                
                dev_elem = soup.select_one('#developers_list')
                if dev_elem:
                    game_data['developer'] = dev_elem.text.strip()
                
                # Extract publisher - try multiple methods to find the correct publisher info
                publisher = 'Unknown'
                
                # Method 1: Look for publisher in the details block
                pub_elem = soup.select_one('.dev_row')
                if pub_elem:
                    # Check if this row contains "Publisher:" text
                    subtitle = pub_elem.select_one('.subtitle')
                    if subtitle and 'publisher' in subtitle.text.lower():
                        # Get the next sibling which contains the publisher name
                        publisher_link = pub_elem.select_one('a')
                        if publisher_link:
                            publisher = publisher_link.text.strip()
                        else:
                            # Fallback: get text after the subtitle
                            text_content = pub_elem.get_text()
                            if ':' in text_content:
                                publisher = text_content.split(':', 1)[1].strip()
                
                # Method 2: Look for publisher in game details section
                if publisher == 'Unknown':
                    # Try to find publisher in the game details section
                    details_block = soup.select('.details_block')
                    for block in details_block:
                        block_text = block.get_text()
                        if 'Publisher:' in block_text:
                            lines = block_text.split('\n')
                            for i, line in enumerate(lines):
                                if 'Publisher:' in line and i + 1 < len(lines):
                                    publisher = lines[i + 1].strip()
                                    break
                            break
                
                # Method 3: Look for specific publisher elements
                if publisher == 'Unknown':
                    # Try alternative selectors
                    pub_link = soup.select_one('a[href*="/publisher/"]')
                    if pub_link:
                        publisher = pub_link.text.strip()
                
                # Method 4: Look in glance_ctn section
                if publisher == 'Unknown':
                    glance_section = soup.select_one('.glance_ctn')
                    if glance_section:
                        dev_rows = glance_section.select('.dev_row')
                        for row in dev_rows:
                            subtitle = row.select_one('.subtitle')
                            if subtitle and 'publisher' in subtitle.text.lower():
                                pub_link = row.select_one('a')
                                if pub_link:
                                    publisher = pub_link.text.strip()
                                    break
                
                # If still not found, fallback to developer (which is common for indie games)
                if publisher == 'Unknown' and game_data['developer'] != 'Unknown':
                    publisher = game_data['developer']
                
                game_data['publisher'] = publisher
                
                date_elem = soup.select_one('.release_date .date')
                if date_elem:
                    game_data['release_date'] = date_elem.text.strip()
                
                desc_elem = soup.select_one('#game_area_description')
                if desc_elem:
                    game_data['full_description'] = desc_elem.text.strip()
                
                short_desc_elem = soup.select_one('.game_description_snippet')
                if short_desc_elem:
                    game_data['short_description'] = short_desc_elem.text.strip()
                
                # Collect different types of images
                
                # 1. Get screenshots using multiple methods
                screenshots = []
                
                # Method 1: Try to get screenshots from the page's HTML directly
                # Look for URLs that match the pattern in the entire page source
                screenshot_pattern = f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{app_id}/ss_"
                for img in soup.find_all('img'):
                    if 'src' in img.attrs:
                        src = img['src']
                        if screenshot_pattern in src and 'blank.gif' not in src:
                            # Convert to full-size URL if needed
                            if '.116x65' in src:
                                src = src.replace('.116x65', '')
                            if '.600x338' in src:
                                src = src.replace('.600x338', '')
                            screenshots.append(src)
                
                # Method 2: Try to get screenshots from the screenshot_holder divs
                if not screenshots:
                    screenshot_divs = soup.select('.screenshot_holder')
                    for div in screenshot_divs:
                        # Look for img tags within the screenshot_holder
                        img_tag = div.select_one('img')
                        if img_tag and 'src' in img_tag.attrs:
                            img_url = img_tag['src']
                            # Convert thumbnail URL to full-size URL if needed
                            if '.116x65' in img_url:
                                img_url = img_url.replace('.116x65', '')
                            if '.600x338' in img_url:
                                img_url = img_url.replace('.600x338', '')
                            if img_url and 'blank.gif' not in img_url:
                                screenshots.append(img_url)
                
                # Method 3: Try to get screenshots from the links
                if not screenshots:
                    screenshot_links = soup.select('.screenshot_holder a')
                    for link in screenshot_links:
                        if 'href' in link.attrs:
                            img_url = link['href']
                            if img_url and 'blank.gif' not in img_url:
                                screenshots.append(img_url)
                
                # Log screenshot information
                if screenshots:
                    logging.info(f"Found {len(screenshots)} screenshots for {game_data['name']} (App ID: {app_id})")
                    # Store up to 5 screenshots in individual fields
                    for i, url in enumerate(screenshots[:5], 1):
                        game_data[f'screenshot{i}'] = url
                else:
                    logging.warning(f"No screenshots found for {game_data['name']} (App ID: {app_id})")
                
                # 2. Get header image
                header_image = ''
                
                # Try to find the header image using the specific class
                header_img_elem = soup.select_one('.game_header_image_full')
                if header_img_elem and 'src' in header_img_elem.attrs:
                    header_image = header_img_elem['src']
                
                # If not found, try the alternative class
                if not header_image:
                    header_img_elem = soup.select_one('.game_header_image')
                    if header_img_elem and 'src' in header_img_elem.attrs:
                        header_image = header_img_elem['src']
                
                # If still not found, try to construct it from the app_id
                if not header_image:
                    header_image = f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg"
                    logging.info(f"Constructed header image URL for {game_data['name']} (App ID: {app_id})")
                
                if header_image and 'blank.gif' not in header_image:
                    game_data['header_image'] = header_image
                    logging.info(f"Found header image for {game_data['name']} (App ID: {app_id})")
                else:
                    logging.warning(f"No header image found for {game_data['name']} (App ID: {app_id})")
                game_data['price'] = self._extract_price(soup)
                game_data['system_requirements'] = self._extract_system_requirements(soup)
                game_data['tags'] = [tag.text.strip() for tag in soup.select('.app_tag')]
                
                lang_elem = soup.select_one('#language_dropdown')
                if lang_elem:
                    game_data['supported_languages'] = lang_elem.text.strip()
                
                game_data['user_rating'] = self._extract_user_rating(soup)
                game_data['review_count'] = self._extract_review_count(soup)
                
                self._save_to_database(game_data)
                return game_data
                
            except requests.exceptions.RequestException as e:
                retry_count += 1
                logging.warning(f"Attempt {retry_count} failed for {url}: {e}")
                time.sleep(5)  # Wait before retrying
                
            except Exception as e:
                logging.error(f"Error scraping {url}: {e}")
                return None
                
        logging.error(f"Failed to scrape {url} after {max_retries} attempts")
        return None

    def _extract_price(self, soup):
        """Extract price information from the page"""
        price_elem = soup.select_one('.game_purchase_price')
        if price_elem and not price_elem.text.strip().lower() == 'free':
            return float(price_elem.text.strip().replace('$', '').replace(',', ''))
        return 0.0

    def _extract_system_requirements(self, soup):
        """Extract system requirements from the page"""
        sys_req = soup.select_one('.sysreq_contents')
        return sys_req.text.strip() if sys_req else ''

    def _extract_user_rating(self, soup):
        """Extract user rating percentage"""
        rating_elem = soup.select_one('.game_review_summary')
        return float(rating_elem.text.strip().replace('%', '')) if rating_elem else None

    def _extract_review_count(self, soup):
        """Extract number of user reviews"""
        review_elem = soup.select_one('.review_count')
        if review_elem:
            count_text = review_elem.text.strip().replace(',', '')
            return int(''.join(filter(str.isdigit, count_text)))
        return 0

    def _save_to_database(self, game_data):
        """Save game data to SQLite database"""
        try:
            cursor = self.db_conn.cursor()
            
            # Check if game exists and if data has changed
            cursor.execute("SELECT last_updated FROM games WHERE app_id = ?", (game_data['app_id'],))
            existing_game = cursor.fetchone()
            
            if existing_game:
                # Game exists, check if any data has changed
                cursor.execute('''
                    SELECT name, developer, publisher, release_date, 
                           full_description, short_description, price,
                           system_requirements, supported_languages,
                           user_rating, review_count, steam_url, header_image,
                           screenshot1, screenshot2, screenshot3, screenshot4, screenshot5
                    FROM games WHERE app_id = ?
                ''', (game_data['app_id'],))
                
                old_data = cursor.fetchone()
                new_data = (
                    game_data['name'], game_data['developer'], game_data['publisher'],
                    game_data['release_date'], game_data['full_description'],
                    game_data['short_description'], game_data['price'],
                    game_data['system_requirements'], game_data['supported_languages'],
                    game_data['user_rating'], game_data['review_count'], game_data['steam_url'],
                    game_data['header_image'],
                    game_data.get('screenshot1', ''), game_data.get('screenshot2', ''),
                    game_data.get('screenshot3', ''), game_data.get('screenshot4', ''),
                    game_data.get('screenshot5', '')
                )
                
                # If data has changed, log the changes
                if old_data != new_data:
                    logging.info(f"Game {game_data['app_id']} ({game_data['name']}) has been updated")
                    
                    # Check specifically for release date changes
                    if old_data[3] != game_data['release_date']:
                        logging.info(f"Release date changed from '{old_data[3]}' to '{game_data['release_date']}'")
            
            # Insert or replace game details
            cursor.execute('''
                INSERT OR REPLACE INTO games (
                    app_id, name, developer, publisher, release_date,
                    full_description, short_description, price,
                    system_requirements, supported_languages,
                    user_rating, review_count, steam_url, header_image,
                    screenshot1, screenshot2, screenshot3, screenshot4, screenshot5,
                    last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game_data['app_id'], game_data['name'], game_data['developer'],
                game_data['publisher'], game_data['release_date'],
                game_data['full_description'], game_data['short_description'],
                game_data['price'], game_data['system_requirements'],
                game_data['supported_languages'], game_data['user_rating'],
                game_data['review_count'], game_data['steam_url'], 
                game_data['header_image'],
                game_data.get('screenshot1', ''), game_data.get('screenshot2', ''),
                game_data.get('screenshot3', ''), game_data.get('screenshot4', ''),
                game_data.get('screenshot5', ''),
                datetime.now()
            ))
            
            # For tags, first delete existing ones to avoid duplicates
            cursor.execute("DELETE FROM tags WHERE app_id = ?", (game_data['app_id'],))
            
            # Insert tags
            cursor.executemany('''
                INSERT INTO tags (app_id, tag) VALUES (?, ?)
            ''', [(game_data['app_id'], tag) for tag in game_data['tags']])
            
            self.db_conn.commit()
            
        except sqlite3.Error as e:
            logging.error(f"Database error while saving game {game_data['app_id']}: {e}")
            self.db_conn.rollback()

    def export_data(self, format_type, output_path):
        """Export collected data in the specified format"""
        try:
            cursor = self.db_conn.cursor()
            
            # Get all game data with related information
            cursor.execute('''
                SELECT g.*, GROUP_CONCAT(DISTINCT t.tag) as tags
                FROM games g
                LEFT JOIN tags t ON g.app_id = t.app_id
                GROUP BY g.app_id
            ''')
            
            columns = [description[0] for description in cursor.description]
            data = cursor.fetchall()
            
            if format_type == 'csv':
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(data)
                    
            elif format_type == 'json':
                json_data = []
                for row in data:
                    json_data.append(dict(zip(columns, row)))
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2)
                    
            elif format_type == 'excel':
                df = pd.DataFrame(data, columns=columns)
                df.to_excel(output_path, index=False, engine='openpyxl')
                
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            raise

    def ensure_db_connection(self):
        """Ensure database connection is active"""
        try:
            # Test the connection
            self.db_conn.execute("SELECT 1")
        except (sqlite3.Error, AttributeError):
            # Reconnect if needed
            try:
                self.db_conn = sqlite3.connect(self.db_name)
            except sqlite3.Error as e:
                logging.error(f"Database reconnection error: {e}")
                raise
            
    def close_driver(self):
        """Close only the Selenium driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def close_all(self):
        """Close all resources including database"""
        self.close_driver()
        if self.db_conn:
            self.db_conn.close()
            self.db_conn = None
            
    def close(self):
        """Legacy method for backward compatibility"""
        self.close_all()

class SteamScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam Games Scraper")
        self.default_url = "https://store.steampowered.com/search/?tags=492&supportedlang=english&filter=comingsoon&ndl=1"
        self.scraper = None
        self.is_scraping = False
        self.is_paused = False
        self.current_game_links = []
        self.current_index = 0
        self.db_name = "steam_games.db"
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # URL Input Frame
        url_frame = ttk.LabelFrame(self.root, text="Steam URL", padding="5")
        url_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        ttk.Label(url_frame, text="Enter Steam URL:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.url_var = tk.StringVar(value=self.default_url)
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=70)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Database Name Frame
        db_frame = ttk.LabelFrame(self.root, text="Database Settings", padding="5")
        db_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        ttk.Label(db_frame, text="Database Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.db_var = tk.StringVar(value=self.db_name)
        self.db_entry = ttk.Entry(db_frame, textvariable=self.db_var, width=30)
        self.db_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(db_frame, text=".db").grid(row=0, column=2, padx=0, pady=5, sticky="w")
        
        # Preset URLs
        presets_frame = ttk.LabelFrame(self.root, text="Preset URLs", padding="5")
        presets_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        
        # Define preset URLs
        self.presets = {
            "Indie Games": "https://store.steampowered.com/search/?tags=492&supportedlang=english&ndl=1",
            "Action RPG": "https://store.steampowered.com/search/?tags=4231&supportedlang=english&ndl=1",
            "Strategy": "https://store.steampowered.com/search/?tags=9&supportedlang=english&ndl=1",
            "Single Player": "https://store.steampowered.com/search/?tags=4182&supportedlang=english&ndl=1",
            "Coming Soon": "https://store.steampowered.com/search/?filter=comingsoon&supportedlang=english&ndl=1"
        }
        
        # Create buttons for each preset
        col = 0
        for name, url in self.presets.items():
            btn = ttk.Button(presets_frame, text=name, command=lambda u=url: self.set_preset_url(u))
            btn.grid(row=0, column=col, padx=5, pady=5)
            col += 1
        
        # Stats Frame
        stats_frame = ttk.LabelFrame(self.root, text="Statistics", padding="5")
        stats_frame.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        
        self.total_games_var = tk.StringVar(value="Total Games: 0")
        self.existing_games_var = tk.StringVar(value="Existing Games: 0")
        self.new_games_var = tk.StringVar(value="New Games: 0")
        
        ttk.Label(stats_frame, textvariable=self.total_games_var).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(stats_frame, textvariable=self.existing_games_var).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(stats_frame, textvariable=self.new_games_var).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        # Export options
        export_frame = ttk.LabelFrame(self.root, text="Export Options", padding="5")
        export_frame.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        
        self.export_format = tk.StringVar(value="csv")
        ttk.Radiobutton(export_frame, text="CSV", variable=self.export_format, value="csv").grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(export_frame, text="JSON", variable=self.export_format, value="json").grid(row=0, column=1, padx=5, pady=5)
        ttk.Radiobutton(export_frame, text="Excel", variable=self.export_format, value="excel").grid(row=0, column=2, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=5, column=0, padx=5, pady=5, sticky="ew")
        
        self.start_button = ttk.Button(button_frame, text="Start Scraping", command=self.start_scraping)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.pause_button = ttk.Button(button_frame, text="Pause", command=self.toggle_pause, state="disabled")
        self.pause_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.export_button = ttk.Button(button_frame, text="Export Data", command=self.export_data)
        self.export_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress.grid(row=6, column=0, padx=5, pady=5, sticky="ew")
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.root, textvariable=self.status_var)
        self.status_label.grid(row=7, column=0, padx=5, pady=5, sticky="ew")
    
    def set_preset_url(self, url):
        """Set the URL entry to a preset value"""
        self.url_var.set(url)
        
    def toggle_pause(self):
        """Toggle between pause and resume"""
        self.is_paused = not self.is_paused
        self.pause_button.configure(text="Resume" if self.is_paused else "Pause")
        status = "Paused" if self.is_paused else "Resuming..."
        self.status_var.set(status)
        
        if not self.is_paused:
            # Resume scraping
            self.root.after(100, self.continue_scraping)

    def start_scraping(self):
        """Start the scraping process"""
        if self.is_scraping:
            return
        
        # Get URL and database name from UI
        url = self.url_var.get().strip()
        if not url:
            self.status_var.set("Error: Please enter a valid Steam URL")
            return
            
        # Get database name
        db_name = self.db_var.get().strip()
        if not db_name:
            self.status_var.set("Error: Please enter a database name")
            return
            
        # Ensure database name has .db extension
        if not db_name.endswith('.db'):
            db_name = f"{db_name}.db"
            
        self.db_name = db_name
        self.is_scraping = True
        self.is_paused = False
        self.status_var.set(f"Initializing scraper for {url}...")
        self.progress_var.set(0)
        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        
        try:
            # Create a new scraper instance with the provided URL and database
            self.scraper = SteamScraper(url, db_name)
            self.scraper.initialize_driver()
            
            # Get existing games count
            existing_games = self.scraper.get_existing_app_ids()
            self.existing_games_var.set(f"Existing Games: {len(existing_games)}")
            
            # Get game links
            self.status_var.set("Collecting game links...")
            self.current_game_links = self.scraper.scroll_and_collect_games()
            self.current_index = 0
            
            # Update UI with counts
            self.new_games_var.set(f"New Games: {len(self.current_game_links)}")
            total_games = len(self.current_game_links) + len(existing_games)
            self.total_games_var.set(f"Total Games: {total_games}")
            
            # Start scraping process
            self.continue_scraping()
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            logging.error(f"Scraping error: {e}")
            self.cleanup()

    def continue_scraping(self):
        """Continue scraping from where we left off"""
        if not self.is_scraping or self.is_paused:
            return
            
        try:
            if self.current_index < len(self.current_game_links):
                link = self.current_game_links[self.current_index]
                self.status_var.set(f"Scraping game {self.current_index + 1} of {len(self.current_game_links)}")
                self.scraper.scrape_game_details(link)
                self.progress_var.set(((self.current_index + 1) / len(self.current_game_links)) * 100)
                self.current_index += 1
                
                # Schedule next game
                self.root.after(100, self.continue_scraping)
            else:
                self.status_var.set("Scraping completed!")
                self.cleanup()
                
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            logging.error(f"Scraping error: {e}")
            self.cleanup()

    def cleanup(self):
        """Clean up resources and reset UI"""
        self.is_scraping = False
        self.is_paused = False
        self.start_button.configure(state="normal")
        self.pause_button.configure(state="disabled")
        self.pause_button.configure(text="Pause")
        if self.scraper:
            self.scraper.close_driver()
            
    def export_data(self):
        """Export the collected data"""
        try:
            if not self.scraper:
                # Try to create a scraper for the current database
                db_name = self.db_var.get().strip()
                if not db_name:
                    self.status_var.set("Error: Please enter a database name")
                    return
                    
                # Ensure database name has .db extension
                if not db_name.endswith('.db'):
                    db_name = f"{db_name}.db"
                
                # Check if database exists
                if not os.path.exists(db_name):
                    self.status_var.set(f"Error: Database {db_name} does not exist. Please run scraper first.")
                    return
                    
                # Create a scraper just for exporting
                self.scraper = SteamScraper("", db_name)
                
            self.scraper.ensure_db_connection()  # Ensure DB connection is active
            format_type = self.export_format.get()
            
            # Get database name without extension for output files
            db_base_name = self.db_name.replace('.db', '')
            
            # Set the correct file extension
            if format_type == 'excel':
                output_path = f"{db_base_name}.xlsx"
            else:
                output_path = f"{db_base_name}.{format_type}"
            
            self.status_var.set(f"Exporting data to {output_path}...")
            self.scraper.export_data(format_type, output_path)
            self.status_var.set(f"Export completed! Data saved to {output_path}")
            
        except Exception as e:
            self.status_var.set(f"Export error: {str(e)}")
            logging.error(f"Export error: {e}")
            
    def __del__(self):
        """Destructor to ensure cleanup"""
        if hasattr(self, 'scraper') and self.scraper:
            self.scraper.close_all()

def main():
    root = tk.Tk()
    app = SteamScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()