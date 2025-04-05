# URL Indexing Checker

A Python-based web application for automated Google indexing status monitoring of URLs with support for bulk processing up to 1 million URLs.

![URL Indexing Checker](static/images/screenshot.svg)

## Features

- Process URLs in bulk (up to 1 million URLs at once)
- Check if URLs are indexed on Google using IP rotation to avoid rate limiting
- Display comprehensive reports with visual analytics
- Export results as CSV files
- Background processing for large datasets with real-time progress tracking
- PostgreSQL database for robust data storage

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Clone the Repository](#clone-the-repository)
  - [Set Up PostgreSQL Database](#set-up-postgresql-database)
  - [Environment Variables](#environment-variables)
  - [Install Dependencies](#install-dependencies)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
  - [Checking URLs](#checking-urls)
  - [Viewing Results](#viewing-results)
  - [Generating Reports](#generating-reports)
  - [Exporting Data](#exporting-data)
- [Demo Mode](#demo-mode)
- [Adding Custom Proxies](#adding-custom-proxies)
- [Configuration Options](#configuration-options)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package installer)
- Git (optional, for cloning the repository)

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/url-indexing-checker.git
cd url-indexing-checker
```

Or download and extract the ZIP file from GitHub.

### Set Up PostgreSQL Database

1. Install PostgreSQL if you haven't already:

   **Ubuntu/Debian**:
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

   **macOS** (using Homebrew):
   ```bash
   brew install postgresql
   brew services start postgresql
   ```

   **Windows**:
   Download and install from [PostgreSQL Official Website](https://www.postgresql.org/download/windows/)

2. Create a database for the application:

   ```bash
   sudo -u postgres psql
   ```

   In the PostgreSQL prompt:
   ```sql
   CREATE DATABASE url_indexing_checker;
   CREATE USER url_checker WITH PASSWORD 'yourpassword';
   GRANT ALL PRIVILEGES ON DATABASE url_indexing_checker TO url_checker;
   \q
   ```

### Environment Variables

Create a `.env` file in the project root directory with the following variables:

```
DATABASE_URL=postgresql://url_checker:yourpassword@localhost/url_indexing_checker
SESSION_SECRET=your_secure_secret_key
```

Replace `yourpassword` with the password you set for the PostgreSQL user, and `your_secure_secret_key` with a random string for session security.

### Install Dependencies

1. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

2. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

   If the requirements.txt file is missing, you can create one with the following content:

   ```
   flask
   flask-sqlalchemy
   gunicorn
   pandas
   psycopg2-binary
   requests
   sqlalchemy
   trafilatura
   werkzeug
   python-dotenv
   ```

   Then run `pip install -r requirements.txt` again.

## Running the Application

1. Run the setup script to initialize the database and environment variables:

   ```bash
   python setup.py
   ```

   Or specify a custom database URL:

   ```bash
   python setup.py --db-url postgresql://user:password@localhost/url_indexing_checker
   ```

2. Start the application:

   **Development mode**:
   ```bash
   python main.py
   ```

   **Production mode** (using Gunicorn):
   ```bash
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

3. Access the application in your web browser at `http://localhost:5000`

## Usage Guide

### Checking URLs

1. Navigate to the homepage by accessing `http://localhost:5000`
2. Enter URLs to check in the text area (one URL per line) or upload a text/CSV file containing URLs
3. Click "Check URLs" to start the process
4. For large datasets (>10,000 URLs), you'll see a progress tracking page

### Viewing Results

- After processing, you'll be redirected to the results page
- Results are paginated for easier navigation
- You can see summary statistics at the top of the page

### Generating Reports

- Reports are automatically generated after checking URLs
- View all reports by clicking on the "Reports" link in the navigation menu
- Click on a report name to view detailed analytics

### Exporting Data

- On the report detail page, click "Export as CSV" to download the report data
- The CSV file includes all URLs with their indexing status

## Demo Mode

By default, the application runs in "demo mode" which simulates checking indexing status without making actual Google queries. This is useful for testing the application without risking IP blocks from Google.

To disable demo mode and use actual Google queries (use with caution):

1. Open `indexing_checker.py`
2. Change `self.demo_mode = True` to `self.demo_mode = False` in the `__init__` method
3. Restart the application

## Adding Custom Proxies

For production use, you'll want to use reliable proxies to avoid rate limiting:

1. Open `proxy_manager.py`
2. Modify the `update_proxies` method to fetch proxies from your preferred service
3. Alternatively, replace the `default_proxies` list with your own proxy servers

Example for adding custom proxies:

```python
self.default_proxies = [
    '123.45.67.89:8080',
    '98.76.54.32:3128',
    # Add more proxies here
]
```

## Configuration Options

You can customize the application by modifying the following settings:

- **Max URLs per request**: Edit `max_urls` in the `check_urls` route in `app.py`
- **Results per page**: Edit `per_page` in the `results` route in `app.py`
- **Background processing threshold**: Edit `is_large_dataset` check in `app.py`
- **Batch size**: Modify the `batch_size` variable in the `check_urls` route

## Troubleshooting

### Database Connection Issues

If you encounter database connection problems:

1. Verify that PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```

2. Check that your database credentials in the `.env` file are correct

3. Make sure the database exists:
   ```bash
   sudo -u postgres psql -c "\l"
   ```

### Application Not Starting

If the application fails to start:

1. Check the logs for error messages
2. Verify that all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Make sure you're using Python 3.8+:
   ```bash
   python --version
   ```

### Slow Performance with Large Datasets

For very large datasets:

1. Increase the batch size in `app.py`
2. Ensure your PostgreSQL database has adequate resources
3. Consider adding indexing to the database tables if not already present

## License

This project is licensed under the MIT License - see the LICENSE file for details.