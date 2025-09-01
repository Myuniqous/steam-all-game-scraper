# Steam Game Scraper - Web UI User Guide

## 🚀 How to Start the Web UI

### Step 1: Launch the Application
1. **Double-click** `run_web_ui.bat` 
2. Wait for the dependencies to install (first time only)
3. The application will start and show you the URL
4. Open your web browser and go to: **http://localhost:5000**

### Step 2: Access the Web Interface
- The web UI will open with a modern dark theme
- You'll see two main tabs: **"Scrape Games"** and **"Search Database"**

---

## 📊 Using the Scraper Section

### To Scrape Steam Games:

1. **Click the "Scrape Games" tab** (should be active by default)

2. **Enter Steam URL:**
   - Paste any Steam store search URL in the "Steam Store URL" field
   - OR select from preset categories in the dropdown:
     - Indie Games (Coming Soon)
     - Action RPG
     - Strategy Games
     - Single Player
     - All Coming Soon

3. **Set Database Name:**
   - Enter a name for your database (e.g., "indie_games")
   - Don't include ".db" - it's added automatically

4. **Start Scraping:**
   - Click the blue **"Start Scraping"** button
   - Watch real-time progress with:
     - Live status updates
     - Current game being scraped
     - Progress percentage
     - Animated progress bar

5. **Stop if Needed:**
   - Click the red **"Stop Scraping"** button to halt the process

---

## 🔍 Using the Search Section

### To Search Your Databases:

1. **Click the "Search Database" tab**

2. **Select a Database:**
   - View all available databases with their game counts and file sizes
   - Click on any database card to select it
   - Click **"Refresh"** to update the list

3. **Set Date Range:**
   - Choose start date and end date for filtering games
   - Default is set to last year

4. **Search Games:**
   - Click the blue **"Search Games"** button
   - Results will appear in a table below

5. **Export Results:**
   - Choose format: CSV, JSON, or Excel
   - Click the green **"Export"** button
   - File will be saved in your project folder

---

## 🎨 Web UI Features

### Visual Feedback:
- **Toast Notifications:** Pop-up messages for actions (top-right corner)
- **Connection Status:** Green dot = connected, Red dot = disconnected
- **Real-time Updates:** Progress updates without page refresh
- **Hover Effects:** Interactive buttons and cards

### Responsive Design:
- **Desktop:** Full featured layout
- **Mobile/Tablet:** Optimized for smaller screens
- **Dark Theme:** Easy on the eyes for long sessions

---

## 🛠️ Troubleshooting

### If the Web UI won't start:
1. Make sure Python is installed and in PATH
2. Check if port 5000 is available
3. Run `run_web_ui.bat` from command prompt to see errors

### If scraping fails:
1. Check if Chrome browser is installed
2. Verify the Steam URL is valid
3. Check your internet connection

### If search shows no results:
1. Make sure you have databases (run scraper first)
2. Check the date range isn't too restrictive
3. Verify the database contains games in that date range

---

## 💡 Tips for Best Experience

1. **Bookmarks:** Bookmark http://localhost:5000 for quick access
2. **Multiple Tabs:** You can open multiple browser tabs
3. **Background Running:** Keep the command prompt window open while using the web UI
4. **Export Before Closing:** Export important search results before stopping the server

---

## 🔄 Switching Between Old and New

### You can still use the old batch files:
- `run_steam_scraper.bat` - Original Tkinter GUI scraper
- `run_steam_search.bat` - Original Tkinter GUI search
- `run_web_ui.bat` - **NEW** Modern Web UI

### All methods work with the same databases!
- Databases created with old method work with new Web UI
- Databases created with Web UI work with old batch files
- Complete compatibility between all versions

---

## 🎯 Summary

**To use the Web UI:**
1. Run `run_web_ui.bat`
2. Open http://localhost:5000 in browser
3. Use "Scrape Games" tab to collect data
4. Use "Search Database" tab to find and export games
5. Enjoy the modern interface! 🎮

**Much better than batch files because:**
✅ Real-time progress tracking  
✅ Better visual organization  
✅ Mobile-friendly design  
✅ Professional appearance  
✅ No windows popping up  
✅ Works in any browser  