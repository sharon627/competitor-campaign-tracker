# Competitor Campaign Tracker - Marriott China

A web application for tracking and analyzing Marriott China's marketing campaigns. This system automatically scrapes campaign data, stores it in a database, and displays it through a modern, responsive dashboard.

## Features

### Story 2.1: Campaign Data Extraction
- **Automated daily scraping** of Marriott China website
- Extracts campaign names, descriptions, and metadata
- **Chinese character encoding** handled properly
- Automatic **category detection** (family, dining, seasonal, rewards, etc.)
- Timestamp recording for campaign discovery

### Story 2.2: Data Storage & Processing
- SQLite database (can be upgraded to PostgreSQL)
- Campaign data stored with proper categorization
- **Duplicate detection** - same campaigns are updated, not re-added
- **Inactive campaign flagging** when campaigns disappear from source
- Data validation before storage
- Scrape activity logging

### Story 2.3: Website Display Integration
- Modern, responsive dashboard design
- **Marriott section** showing all current campaigns
- Campaign cards with: name, description, category, discovery date
- **Filter by category** and status (active/inactive)
- **Search functionality** across campaign names and descriptions
- **Visual indicators** for recently updated campaigns
- Works on both mobile and desktop

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database with Demo Data

```bash
python run.py --init
```

This creates the database and loads sample Marriott campaign data for testing.

### 3. Start the Server

```bash
# Basic server (without scheduler)
python run.py

# With automated daily scraping
python run.py --scheduler
```

### 4. Open the Dashboard

Navigate to: **http://localhost:5000**

## Project Structure

```
├── app.py              # Flask application & API routes
├── models.py           # Database models (SQLAlchemy)
├── scraper.py          # Web scraper for Marriott China
├── scheduler.py        # Automated scheduling (APScheduler)
├── config.py           # Application configuration
├── run.py              # Main entry point
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Main dashboard template
└── static/
    ├── css/
    │   └── styles.css  # Dashboard styles
    └── js/
        └── app.js      # Frontend JavaScript
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/campaigns` | GET | Get all campaigns with filters |
| `/api/campaigns/<id>` | GET | Get specific campaign |
| `/api/categories` | GET | Get all unique categories |
| `/api/stats` | GET | Get dashboard statistics |
| `/api/scrape` | POST | Trigger manual scrape |
| `/api/scrape/logs` | GET | Get scrape history |
| `/api/health` | GET | Health check |

### Query Parameters for `/api/campaigns`

- `category` - Filter by category (e.g., `family`, `dining`)
- `is_active` - Filter by status (`true` or `false`)
- `search` - Search in name and description
- `limit` - Number of results (default: 50)
- `offset` - Pagination offset (default: 0)

## Configuration

Copy `env.example.txt` to `.env` and customize:

```env
# Database
DATABASE_URL=sqlite:///competitor_campaigns.db

# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/competitor_db

# Scraping
SCRAPE_INTERVAL_HOURS=24

# Flask
FLASK_DEBUG=True
FLASK_PORT=5000
```

## Campaign Categories

The scraper automatically categorizes campaigns based on Chinese keywords:

| Category | Chinese Keywords |
|----------|------------------|
| Family | 亲子, 家庭, 儿童 |
| Dining | 餐饮, 美食, 餐厅 |
| Seasonal | 季节, 春节, 中秋 |
| Rewards | 积分, 会员, 旅享家 |
| Travel | 旅行, 度假, 旅游 |
| Business | 商务, 会议, 差旅 |
| Spa | 水疗, SPA, 养生 |
| Wedding | 婚礼, 婚宴, 蜜月 |
| Promotion | 优惠, 折扣, 特价 |

## Database Schema

### competitor_campaigns

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| campaign_name | String(500) | Campaign title |
| campaign_info | Text | Campaign description |
| source_url | String(1000) | Original URL |
| category | String(100) | Auto-detected category |
| scraped_date | DateTime | First discovery date |
| last_seen_date | DateTime | Last seen in scrape |
| is_active | Boolean | Still visible on source |
| competitor_name | String(100) | "Marriott" |

### scrape_logs

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| scrape_date | DateTime | When scrape occurred |
| competitor_name | String(100) | Target competitor |
| status | String(50) | success/failed/partial |
| campaigns_found | Integer | Total campaigns found |
| new_campaigns | Integer | New campaigns added |
| error_message | Text | Error details if failed |

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Manual Scrape via API

```bash
# Trigger live scrape
curl -X POST http://localhost:5000/api/scrape

# Use demo data
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"use_demo": true}'
```

### Customizing the Scraper

Edit `scraper.py` to add new source URLs or adjust selectors:

```python
MARRIOTT_CHINA_URLS = [
    'https://www.marriott.com.cn/default.mi',
    'https://www.marriott.com.cn/specials/offers.mi',
    # Add more URLs here
]
```

## Production Deployment

For production deployment:

1. Set `FLASK_DEBUG=False` in `.env`
2. Use PostgreSQL instead of SQLite
3. Use Gunicorn or uWSGI as WSGI server
4. Set up proper logging
5. Configure reverse proxy (nginx)

Example with Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

### No campaigns showing
1. Click "Run Scraper" button in the dashboard
2. Or run: `python run.py --init` to load demo data

### Scraper returns empty results
- The live Marriott website may have anti-scraping measures
- Demo data is automatically used as fallback
- Check scrape logs for error details

### Database errors
- Delete `competitor_campaigns.db` and restart
- Run `python run.py --init` to recreate

## License

Internal use only - Hilton Competitor Analysis Tool
