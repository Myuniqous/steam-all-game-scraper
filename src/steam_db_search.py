import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import sqlite3
import pandas as pd
import json
import csv
from datetime import datetime, timedelta
import logging
import re
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steam_search.log'),
        logging.StreamHandler()
    ]
)

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
        logging.error(f"Date parsing error for '{date_str}': {e}")
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
        logging.error(f"Date comparison error for '{release_date}': {e}")
        return False

class SteamDBSearch:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam Games Database Search")
        
        # Database connection
        self.db_path = None
        self.db_conn = None
        
        self.create_widgets()
        
    def connect_db(self, db_path):
        """Connect to the SQLite database"""
        try:
            # Close existing connection if any
            if self.db_conn:
                self.db_conn.close()
                
            self.db_conn = sqlite3.connect(db_path)
            self.db_path = db_path
            logging.info(f"Connected to database: {db_path}")
            return True
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            messagebox.showerror("Error", f"Database connection error: {e}")
            return False
        
    def create_widgets(self):
        # Database Selection Frame
        db_frame = ttk.LabelFrame(self.root, text="Select Database", padding="10")
        db_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        self.db_path_var = tk.StringVar()
        ttk.Entry(db_frame, textvariable=self.db_path_var, width=50).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(db_frame, text="Browse...", command=self.browse_database).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(db_frame, text="Connect", command=self.connect_to_db).grid(row=0, column=2, padx=5, pady=5)
        
        # Available Databases Frame
        available_db_frame = ttk.LabelFrame(self.root, text="Available Databases", padding="10")
        available_db_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Add refresh button
        refresh_btn = ttk.Button(available_db_frame, text="Refresh List", command=self.refresh_available_databases)
        refresh_btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Scan for available databases
        self.db_buttons_frame = ttk.Frame(available_db_frame)
        self.db_buttons_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.refresh_available_databases()
        
        # Date Selection Frame
        date_frame = ttk.LabelFrame(self.root, text="Select Date Range", padding="10")
        date_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, padx=5, pady=5)
        self.start_date = DateEntry(date_frame)
        self.start_date.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(date_frame, text="End Date:").grid(row=0, column=2, padx=5, pady=5)
        self.end_date = DateEntry(date_frame)
        self.end_date.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(date_frame, text="Search", command=self.search_games).grid(row=0, column=4, padx=10, pady=5)
        
        # Results Treeview
        self.create_treeview()
        
        # Export Frame
        export_frame = ttk.LabelFrame(self.root, text="Export Results", padding="10")
        export_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        
        self.export_format = tk.StringVar(value="csv")
        ttk.Radiobutton(export_frame, text="CSV", variable=self.export_format, value="csv").grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(export_frame, text="JSON", variable=self.export_format, value="json").grid(row=0, column=1, padx=5, pady=5)
        ttk.Radiobutton(export_frame, text="Excel", variable=self.export_format, value="excel").grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(export_frame, text="Export Selected Format", command=self.export_results).grid(row=0, column=3, padx=10, pady=5)
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
    
    def refresh_available_databases(self):
        """Scan the current directory for SQLite database files"""
        # Clear existing buttons
        for widget in self.db_buttons_frame.winfo_children():
            widget.destroy()
            
        # Find all .db files in the current directory
        db_files = [f for f in os.listdir('.') if f.endswith('.db')]
        
        if not db_files:
            ttk.Label(self.db_buttons_frame, text="No database files found. Run the scraper first to create databases.").grid(row=0, column=0, padx=5, pady=5)
            return
            
        # Create a button for each database file
        for i, db_file in enumerate(db_files):
            btn = ttk.Button(
                self.db_buttons_frame, 
                text=db_file,
                command=lambda f=db_file: self.select_database(f)
            )
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="w")
    
    def select_database(self, db_file):
        """Select a database from the available list"""
        self.db_path_var.set(db_file)
        self.connect_to_db()
        
    def browse_database(self):
        """Open file dialog to select a database file"""
        file_path = filedialog.askopenfilename(
            title="Select Database File",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        if file_path:
            self.db_path_var.set(file_path)
    
    def connect_to_db(self):
        """Connect to the selected database"""
        db_path = self.db_path_var.get()
        if not db_path:
            self.status_var.set("Error: Please select a database file")
            return
            
        if self.connect_db(db_path):
            self.status_var.set(f"Connected to database: {db_path}")
        
    def create_treeview(self):
        """Create and configure the treeview for results"""
        columns = ('app_id', 'name', 'developer', 'publisher', 'release_date', 'price')
        self.tree = ttk.Treeview(self.root, columns=columns, show='headings', height=15)
        
        # Define headings
        self.tree.heading('app_id', text='App ID')
        self.tree.heading('name', text='Game Name')
        self.tree.heading('developer', text='Developer')
        self.tree.heading('publisher', text='Publisher')
        self.tree.heading('release_date', text='Release Date')
        self.tree.heading('price', text='Price')
        
        # Configure columns
        self.tree.column('app_id', width=70)
        self.tree.column('name', width=200)
        self.tree.column('developer', width=150)
        self.tree.column('publisher', width=150)
        self.tree.column('release_date', width=100)
        self.tree.column('price', width=70)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid the treeview and scrollbar
        self.tree.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        scrollbar.grid(row=3, column=1, pady=5, sticky="ns")
        
        # Configure row weights
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    def search_games(self):
        """Search games in the database within the selected date range"""
        if not self.db_conn:
            self.status_var.set("Error: No database connected")
            return
            
        try:
            start_date = self.start_date.get_date().strftime('%Y-%m-%d')
            end_date = self.end_date.get_date().strftime('%Y-%m-%d')
            
            cursor = self.db_conn.cursor()
            cursor.execute('SELECT app_id, name, developer, publisher, release_date, price FROM games')
            all_games = cursor.fetchall()
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Filter games based on date range using improved logic
            filtered_games = []
            excluded_count = 0
            
            for game in all_games:
                app_id, name, dev, pub, release_date, price = game
                
                # Use the improved date filtering function
                if release_date and is_steam_date_in_range(release_date, start_date, end_date):
                    filtered_games.append(game)
                    logging.info(f"Including game: {name} with date: {release_date}")
                else:
                    excluded_count += 1
                    if release_date and release_date not in ['Unknown', 'TBA', 'TBD']:
                        logging.debug(f"Excluding game: {name} with date: {release_date}")
            
            # Insert filtered results
            for row in filtered_games:
                self.tree.insert('', 'end', values=row)
            
            # Enhanced status message
            total_games = len(all_games)
            status_msg = f"Found {len(filtered_games)} games (out of {total_games} total)"
            if excluded_count > 0:
                status_msg += f". Excluded {excluded_count} games with vague or out-of-range dates."
            
            self.status_var.set(status_msg)
            
            # Show informative message if no results
            if len(filtered_games) == 0:
                messagebox.showinfo(
                    "No Results", 
                    f"No games found with release dates between {start_date} and {end_date}.\n\n"
                    f"Note: Only games with specific dates (e.g., '16 Oct, 2025') or month/year "
                    f"(e.g., 'October 2025') are included. Vague dates like '2025', 'Q1 2025', "
                    f"or 'TBA' are excluded from search results."
                )
            
        except Exception as e:
            self.status_var.set(f"Search error: {str(e)}")
            logging.error(f"Search error: {e}")
    
    def export_results(self):
        """Export the search results with ALL fields from database"""
        if not self.db_conn:
            self.status_var.set("Error: No database connected")
            return
            
        try:
            if not self.tree.get_children():
                self.status_var.set("No results to export")
                return
                
            format_type = self.export_format.get()
            
            # Get date range for filename with month names
            start_date_str = self.start_date.get_date().strftime('%d-%b-%Y')
            end_date_str = self.end_date.get_date().strftime('%d-%b-%Y')
            date_range = f"{start_date_str}_to_{end_date_str}"
            
            # Get database name without extension
            db_name = os.path.basename(self.db_path).replace('.db', '')
            
            # Set the correct file extension with date range
            if format_type == 'excel':
                output_path = f"{db_name}_{date_range}.xlsx"
            else:
                output_path = f"{db_name}_{date_range}.{format_type}"
            
            # Get app_ids from the treeview results
            app_ids = [self.tree.item(item)['values'][0] for item in self.tree.get_children()]
            
            # Get complete data for these games from database
            cursor = self.db_conn.cursor()
            
            # Get all fields from games table
            query = '''
                SELECT g.*, GROUP_CONCAT(DISTINCT t.tag) as tags
                FROM games g
                LEFT JOIN tags t ON g.app_id = t.app_id
                WHERE g.app_id IN ({})
                GROUP BY g.app_id
            '''.format(','.join('?' * len(app_ids)))
            
            cursor.execute(query, app_ids)
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Fetch the data
            results = cursor.fetchall()
            
            if format_type == 'csv':
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)  # Write headers
                    writer.writerows(results)
            elif format_type == 'json':
                json_data = []
                for row in results:
                    json_data.append(dict(zip(columns, row)))
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
            elif format_type == 'excel':
                df = pd.DataFrame(results, columns=columns)
                df.to_excel(output_path, index=False, engine='openpyxl')
            
            self.status_var.set(f"Results exported to {output_path}")
            messagebox.showinfo("Success", f"Results exported to {output_path} with all fields!")
            
        except Exception as e:
            self.status_var.set(f"Export error: {str(e)}")
            logging.error(f"Export error: {e}")
            messagebox.showerror("Error", f"Export error: {str(e)}")
    
    def __del__(self):
        """Cleanup database connection"""
        if self.db_conn:
            self.db_conn.close()

def main():
    root = tk.Tk()
    app = SteamDBSearch(root)
    root.mainloop()

if __name__ == "__main__":
    main()