# LogiLead AI

LogiLead AI is an automated tender scraping and notification system that helps businesses identify and track relevant tender opportunities in the Clearing & Forwarding (C&F) sector.

## Project Overview

The system automatically:
1. Scrapes tender information from configured websites (currently GeM portal)
2. Stores the data in a PostgreSQL database
3. Sends email notifications about new opportunities
4. Runs on a scheduled basis to keep information up-to-date

## Setup Instructions

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Git

### Installation

1. Clone the repository:
   ```
   git clone [repository-url]
   cd logiled-ai
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```
   cp config.example.env .env
   ```
   Then edit the `.env` file with your specific configuration values.

### Configuration

Create a `.env` file based on the provided `config.example.env` template with the following variables:

- `LOGILEAD_TENDER_SITES`: Comma-separated list of tender websites to scrape
- `LOGILEAD_GEM_URL`: URL for the GeM portal (default: https://gem.gov.in/active-bids)
- `LOGILEAD_DB_URL`: PostgreSQL database connection string (e.g., postgresql://username:password@localhost:5432/logilead)
- `LOGILEAD_SMTP_HOST`: SMTP server for sending email alerts
- `LOGILEAD_SMTP_PORT`: SMTP server port (default: 587)
- `LOGILEAD_SMTP_USER`: SMTP username
- `LOGILEAD_SMTP_PASS`: SMTP password
- `LOGILEAD_ALERT_RECIPIENTS`: Comma-separated list of email addresses to receive alerts

## Project Structure

```
logilead/
├── scraper.py     # Tender scraping functionality
├── db.py          # Database models and persistence
├── scheduler.py   # Job scheduling
├── alerter.py     # Email notification system
└── run_all.py     # Integration script for testing
```

## Usage

### Running a Complete Cycle (Smoke Test)

To run a complete cycle manually (scrape → store → email):

```
python -m logilead.run_all --cycle
```

This will:
1. Scrape new tenders from the GeM portal
2. Store them in the database
3. Send email alerts for new tenders
4. Log the process to both console and `logilead.log`

### Starting the Scheduler

To start the scheduler for automated runs at 00:30 daily:

```
python -m logilead.run_all --scheduler
```

This will start a background scheduler that runs the complete cycle once per day.

### Setting Up as a System Service

#### Using Systemd (Linux)

1. Create a systemd service file:

```
sudo nano /etc/systemd/system/logilead.service
```

2. Add the following content (adjust paths as needed):

```
[Unit]
Description=LogiLead AI Tender Scraper
After=network.target postgresql.service

[Service]
User=your_username
WorkingDirectory=/path/to/logiled-ai
ExecStart=/path/to/logiled-ai/venv/bin/python -m logilead.run_all --scheduler
Restart=on-failure
RestartSec=5s
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```
sudo systemctl enable logilead.service
sudo systemctl start logilead.service
```

4. Check the status:

```
sudo systemctl status logilead.service
```

#### Using Cron (Linux/macOS)

1. Open the crontab editor:

```
crontab -e
```

2. Add the following line to run the job at 00:30 daily:

```
30 0 * * * cd /path/to/logiled-ai && /path/to/logiled-ai/venv/bin/python -m logilead.run_all --cycle >> /path/to/logiled-ai/cron.log 2>&1
```

## Development

Follow the coding style and conventions specified in the project documentation:

- PEP8 style guide (79-char line limit)
- Google-style docstrings
- Type hints on all functions
- Snake case for functions and variables, PascalCase for classes

## Troubleshooting

- Check the `logilead.log` file for detailed logs
- Ensure your database is accessible and credentials are correct
- Verify SMTP settings if email alerts are not being sent
