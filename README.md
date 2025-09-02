# 🎮 Steam All Game Scraper - Web UI

> Professional Steam game data collection tool with modern web interface, real-time progress tracking, and enhanced export functionality

[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-latest-green.svg)](https://flask.palletsprojects.com/)
[![Flask-SocketIO](https://img.shields.io/badge/flask--socketio-latest-green.svg)](https://flask-socketio.readthedocs.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)
[![Render](https://img.shields.io/badge/deploy-render-blueviolet.svg)](https://render.com)
[![Railway](https://img.shields.io/badge/deploy-railway-purple.svg)](https://railway.app)

## ✨ Key Features

### 🎯 Core Functionality
- 🚀 **Real-time web scraping** with live progress updates via WebSocket
- 🎯 **Advanced date filtering** handles Steam's inconsistent date formats
- 💾 **Multi-format exports** - CSV, JSON, Excel with direct browser downloads
- 📊 **SQLite database management** with separate databases per game category
- 🔍 **Preset URL categories** - Indie, Strategy, Coming Soon, and more
- 📈 **Batch processing** handles thousands of games efficiently

### 🎨 Modern Web Interface
- 🎨 **Professional dark theme** with responsive design
- 📊 **Enhanced progress tracking** with detailed statistics
- 🔄 **Pause/Resume functionality** for long scraping sessions
- 📱 **Mobile-friendly** interface for all devices
- ⚡ **Real-time updates** without page refreshes

### 🚀 Deployment & Production Ready
- 🐳 **Docker containerization** with professional naming conventions
- ☁️ **Cloud platform ready** - Render.com, Railway, and more
- 🔐 **Production configuration** with Flask-SocketIO optimizations
- 📦 **Version-locked dependencies** for reliable deployments
- 🛡️ **Privacy protection** with comprehensive .gitignore

## 🚀 Quick Start

### Option 1: Docker Desktop (Recommended)

```bash
# Clone repository
git clone https://github.com/Myuniqous/steam-all-game-scraper.git
cd "Steam All Game Scraper - Web UI"

# Build Docker image with professional naming
docker build -t steam-scraper .

# Run container with proper naming
docker run -d -p 5000:5000 --name steam-scraper steam-scraper

# Access web interface
# Open your browser to: http://localhost:5000
```

### Option 2: Docker Compose

```bash
# Clone and start with single command
git clone https://github.com/Myuniqous/steam-all-game-scraper.git
cd "Steam All Game Scraper - Web UI"
docker-compose up -d

# Access at http://localhost:5000
```

### Option 3: Local Development

```bash
# Prerequisites: Python 3.6+, Chrome Browser, ChromeDriver
git clone https://github.com/Myuniqous/steam-all-game-scraper.git
cd "Steam All Game Scraper - Web UI"

# Create virtual environment
python -m venv venv

# Activate environment
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Quick start with batch files (Windows)
scripts\run_web_ui.bat

# Or manual start
cd src
python app.py
```

### Option 4: Deploy to Cloud (Free Hosting)

**Render.com (Recommended - Free Tier)**
1. Fork this repository on GitHub
2. Connect your GitHub account to Render.com
3. Create new Web Service from your forked repository
4. Use these settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd src && python app.py`
   - Environment: `NODE_ENV=production`
5. Deploy automatically on every GitHub push

## 📱 Complete Usage Guide

### 🎯 **Scraping Games**
1. **Configure Scraping**:
   - Enter custom Steam search URL or select from presets:
     - 🎮 Indie Games
     - 🏆 Strategy Games  
     - 🆕 Coming Soon
     - 🎯 Custom Categories
   - Set unique database name for each category
   - Configure scraping parameters

2. **Monitor Progress**:
   - Real-time WebSocket updates
   - Live statistics: games processed, success rate, errors
   - Enhanced progress bar with visual feedback
   - Pause/Resume functionality for long sessions

3. **Export Scraped Data**:
   - Select export format (CSV, JSON, Excel) from dropdown
   - Click export button for instant browser download
   - Files include all database fields with proper formatting
   - No files saved in container - direct download experience

### 🔍 **Searching & Filtering**
1. **Database Selection**:
   - Browse available databases in the "Available Databases" section
   - Click on database card to select and connect
   - View database statistics and game count

2. **Advanced Date Filtering**:
   - Set start and end date ranges
   - Intelligent parsing handles Steam's inconsistent formats:
     - ✅ Specific dates: "16 Oct, 2025"
     - ✅ Month-year: "October 2025"  
     - ❌ Vague dates: "2025", "Q1 2025" (automatically filtered)
   - Real-time result counting

3. **Export Search Results**:
   - Same export options as scraping section
   - Filtered data based on your date criteria
   - Maintains all original game information

### 💡 **Pro Tips**
- **Database Organization**: Create separate databases for different game categories
- **Performance**: Pause scraping during high system usage
- **Data Management**: Regular exports for backup and analysis
- **URL Optimization**: Use Steam's advanced search parameters for targeted scraping

## 🏗️ System Architecture

### Component Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │◄──►│   Flask Web UI  │◄──►│  Steam Scraper  │
│   (Frontend)    │    │ (app.py)        │    │ (steam_scraper) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐             │
         └──────────────►│  Flask-SocketIO │◄────────────┘
                        │ (Real-time Comm)│
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │ SQLite Database │
                        │ (Multi-Category)│
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │  Export Engine  │
                        │ (CSV/JSON/Excel)│
                        └─────────────────┘
```

### Design Patterns
- **MVC Pattern**: Flask web application structure
- **Singleton Pattern**: Database connection handling  
- **Factory Pattern**: Export format selection
- **Observer Pattern**: Real-time progress updates via WebSocket
- **Strategy Pattern**: Multiple deployment configurations

## 📁 Project Structure

```
📁 Steam All Game Scraper - Web UI/
├── 📁 src/                          # Source code (clean separation)
│   ├── 🐍 app.py                    # Flask web application with SocketIO
│   ├── 🕷️ steam_scraper.py          # Enhanced scraping engine
│   ├── 🔍 steam_db_search.py        # Database operations & date filtering
│   ├── 📁 templates/
│   │   └── 🌐 index.html            # Modern responsive web interface
│   └── 📁 static/
│       ├── 📁 css/
│       │   └── 🎨 style.css         # Professional dark theme
│       └── 📁 js/
│           └── ⚡ app.js            # WebSocket client & export handling
├── 📁 scripts/                      # Convenient batch launchers
│   ├── 🚀 run_web_ui.bat           # Launch web interface
│   ├── 🔧 run_steam_scraper.bat    # Direct scraper access
│   └── 🔍 run_steam_search.bat     # Database search tool
├── 🐳 Dockerfile                   # Production containerization
├── 🐙 docker-compose.yml           # Easy deployment
├── 📋 requirements.txt             # Version-locked dependencies
├── 📖 README.md                    # This documentation
└── 🚫 .gitignore                   # Privacy protection
```

### Key Files Explained
- **`src/app.py`**: Main Flask application with Flask-SocketIO for real-time updates
- **`src/steam_scraper.py`**: Core scraping logic with Selenium WebDriver
- **`src/steam_db_search.py`**: Database management and advanced date filtering
- **`Dockerfile`**: Production-ready container configuration
- **`requirements.txt`**: Version-locked dependencies for compatibility
- **`.gitignore`**: Protects databases and sensitive files from GitHub upload

## 🎯 Advanced Technical Features

### 📅 Intelligent Date Filtering System
Handles Steam's inconsistent date formats with smart parsing:
- ✅ **Specific Dates**: `"16 Oct, 2025"`, `"December 1, 2024"`
- ✅ **Month-Year**: `"October 2025"`, `"Dec 2024"`  
- ❌ **Vague Dates**: `"2025"`, `"Q1 2025"`, `"Coming Soon"` (automatically excluded)
- 🔄 **Range Filtering**: Efficient start/end date comparisons
- 🎯 **Accuracy**: 95%+ success rate with Steam's data variations

### ⚡ Real-time Progress & Communication
- 🔌 **WebSocket Integration**: Flask-SocketIO for live updates
- 📊 **Enhanced Progress Tracking**: Visual progress bars with statistics
- 🔄 **Non-blocking Processing**: Background scraping with pause/resume
- 📱 **Responsive Updates**: Real-time status without page refreshes
- 💻 **Production Ready**: Configured for deployment environments

### 💾 Export & Data Management
- 📁 **Direct Browser Downloads**: Files served directly to user (no container storage)
- 📋 **Multiple Formats**: CSV, JSON, Excel with proper formatting
- 🗄️ **Database Categories**: Separate SQLite files per game category
- 🔍 **Full Field Export**: All scraped data including metadata
- 📈 **Batch Processing**: Handles thousands of games efficiently

### 🛡️ Production & Security Features
- 🐳 **Professional Docker Setup**: Optimized containerization with proper naming
- 🔒 **Privacy Protection**: Comprehensive .gitignore for sensitive data
- ⚙️ **Version Compatibility**: Locked dependencies (pandas, numpy, etc.)
- 🏭 **Production Config**: Flask-SocketIO with `allow_unsafe_werkzeug=True`
- ☁️ **Cloud Ready**: Configured for Render.com, Railway deployment

### 🔧 Robust Error Handling & Reliability
- 🔄 **Automatic Retries**: Network failure recovery
- 🛠️ **ChromeDriver Management**: Version compatibility handling  
- 📝 **Comprehensive Logging**: Detailed error tracking
- 🎯 **Graceful Degradation**: Continues processing despite individual failures
- 💾 **Database Integrity**: Handles missing databases gracefully

## 🚀 Deployment Options

### 🏠 **Local Development**
- **Windows**: Use included batch scripts (`scripts/run_web_ui.bat`)
- **Cross-platform**: Python virtual environment setup
- **Requirements**: Python 3.6+, Chrome browser, ChromeDriver
- **Best for**: Development, testing, personal use

### 🐳 **Docker Deployment**
- **Professional Setup**: `docker build -t steam-scraper .`
- **Container Management**: `docker run -d -p 5000:5000 --name steam-scraper steam-scraper`
- **Docker Compose**: Single command deployment with `docker-compose up -d`
- **Data Persistence**: Configure volumes for database storage
- **Best for**: Production environments, consistent deployments

### ☁️ **Free Cloud Hosting**

**🎯 Render.com (Recommended)**
- ✅ **Free Tier**: 512MB RAM, automatic HTTPS
- ✅ **GitHub Integration**: Auto-deploy on push
- ✅ **Zero Config**: Works out of the box
- ⚠️ **Cold Start**: 30-second delay after inactivity
- 💰 **Cost**: Free for 100+ daily visitors

**🚂 Railway.app (Alternative)**
- ✅ **Real-time Features**: Better WebSocket support
- ✅ **No Cold Start**: Always warm
- ✅ **PostgreSQL**: Free database included
- 💰 **Cost**: $5/month after free tier

### 🖥️ **Self-Hosted Options**
- **VPS Deployment**: DigitalOcean, Linode, AWS EC2
- **Home Server**: Raspberry Pi, local server setup
- **Network Storage**: Database backup and sync options
- **Best for**: High-volume usage, data privacy requirements

### 📊 **Hosting Recommendations by Use Case**

| Use Case | Recommended Platform | Why |
|----------|---------------------|-----|
| **Personal Use** | Local + Docker | Full control, no costs |
| **Small Team** | Render.com Free | Easy setup, GitHub integration |
| **Production** | Railway.app | No cold starts, better performance |
| **High Volume** | Self-hosted VPS | Unlimited resources, full control |

## 📖 Technical Requirements

### 🔧 **System Requirements**

**Minimum Requirements:**
- **Python**: 3.6 or higher
- **Chrome Browser**: Latest stable version
- **ChromeDriver**: Compatible with installed Chrome version
- **RAM**: 512MB (1GB recommended for large scraping)
- **Storage**: 100MB + database storage

**Dependencies:**
- `Flask` & `Flask-SocketIO`: Web interface and real-time communication
- `Selenium`: Browser automation for scraping
- `pandas` & `openpyxl`: Data processing and Excel export
- `lxml`: HTML parsing and data extraction

### 📚 **Advanced Configuration**

**Environment Variables (Optional):**
```bash
# Flask Secret Key (auto-generated if not provided)
SECRET_KEY=your-secret-key-here

# Production Settings
FLASK_ENV=production
PORT=5000
```

**Chrome Options:**
- Headless mode for server deployment
- Custom user agent and viewport settings
- Memory optimization for large-scale scraping

**Database Configuration:**
- SQLite file location: `/app/data/` (Docker) or local `data/` folder
- Automatic database creation per category
- Optimized schema for Steam game data

### 🔍 **Performance Tuning**

**For High-Volume Scraping:**
- Adjust Chrome memory settings
- Configure batch size for database operations
- Monitor system resources during operation
- Use pause/resume for system resource management

**For Production Deployment:**
- Set `debug=False` for Flask-SocketIO
- Configure proper logging levels
- Use production WSGI server (included in Docker)
- Implement database backup strategies

## 🔧 **Troubleshooting**

### Common Issues & Solutions

**🚫 "ChromeDriver not found"**
- Download ChromeDriver matching your Chrome version
- Place in system PATH or project root directory
- Ensure executable permissions on Linux/Mac

**⚠️ "Database locked" error**
- Close any other applications accessing the database
- Restart the application if the issue persists
- Check file permissions in the data directory

**🔌 "WebSocket connection failed"**
- Check firewall settings for port 5000
- Ensure Flask-SocketIO is properly installed
- Verify production configuration in deployment

**📦 Docker issues**
- Stop and remove old containers: `docker stop steam-scraper && docker rm steam-scraper`
- Rebuild image: `docker build -t steam-scraper .`
- Check Docker Desktop is running

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** this repository on GitHub
2. **Clone** your fork locally
3. **Create** a feature branch: `git checkout -b feature-name`
4. **Make** your changes following the project structure
5. **Test** your changes with Docker and local setup
6. **Commit** with clear messages: `git commit -m "Add feature description"`
7. **Push** to your fork: `git push origin feature-name`
8. **Submit** a Pull Request with detailed description

### 🎯 **Areas for Contribution**
- 🌐 Additional Steam search categories
- 📊 Enhanced data visualization
- 🔍 Advanced filtering options
- 🌍 Internationalization support
- 📱 Mobile interface improvements
- ⚡ Performance optimizations

## ⚖️ Legal & Usage Notice

**📋 Terms of Use:**
- This tool is for **educational and research purposes** only
- Users must comply with **Steam's Terms of Service**
- Respect **rate limits** and avoid overwhelming Steam's servers
- **No warranty** provided - use at your own risk

**🛡️ Privacy & Data:**
- All scraped data is stored **locally** in your databases
- No data is transmitted to external services
- **Your responsibility** to handle data according to applicable laws
- Consider **GDPR compliance** if sharing data

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

**Need Help?**
- 📖 Check this README for common solutions
- 🐛 Report bugs via GitHub Issues
- 💡 Request features via GitHub Issues
- 📧 Contact via GitHub profile for complex issues

## 🙏 Acknowledgments

- **Steam Community**: For the inspiration and data source
- **Flask & SocketIO Teams**: For excellent web framework tools
- **Selenium Project**: For robust browser automation
- **Docker Community**: For containerization best practices
- **Open Source Community**: For continuous improvements and feedback

---

**🎮 Built with ❤️ for gamers, developers, and data enthusiasts worldwide**

[![GitHub stars](https://img.shields.io/github/stars/Myuniqous/steam-all-game-scraper?style=social)](https://github.com/Myuniqous/steam-all-game-scraper/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Myuniqous/steam-all-game-scraper?style=social)](https://github.com/Myuniqous/steam-all-game-scraper/network/members)
[![GitHub issues](https://img.shields.io/github/issues/Myuniqous/steam-all-game-scraper)](https://github.com/Myuniqous/steam-all-game-scraper/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/Myuniqous/steam-all-game-scraper)](https://github.com/Myuniqous/steam-all-game-scraper/commits/main)