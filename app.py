import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Setup Database
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure PostgreSQL database
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Fix for SQLAlchemy compatibility with postgres://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///indexing_checker.db"
    logger.warning("DATABASE_URL not found, falling back to SQLite")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Import models and routes
from models import URL, CheckResult, Report
from proxy_manager import ProxyManager
from indexing_checker import IndexingChecker
from report_generator import ReportGenerator

# Initialize components with demo mode settings
proxy_manager = ProxyManager(use_direct_connection=True)
indexing_checker = IndexingChecker(proxy_manager, demo_mode=True)
report_generator = ReportGenerator()

# Shared state for tracking background process progress
# since we can't directly access Flask session in background threads
background_process_state = {
    'total_urls': 0,
    'processed_urls': 0,
    'is_processing': False
}

# Utility function to sanitize URLs
def sanitize_url(url_str):
    """
    Sanitize a URL string to prevent encoding issues.
    
    Args:
        url_str: The URL string to sanitize
        
    Returns:
        Sanitized URL string or None if the URL has encoding issues
    """
    try:
        # Skip empty URLs
        if not url_str or not url_str.strip():
            return None
            
        # Basic sanitization
        sanitized_url = url_str.strip()
        
        # Test that URL can be properly encoded/decoded
        sanitized_url.encode('utf-8').decode('utf-8')
        
        return sanitized_url
    except (UnicodeError, UnicodeDecodeError, UnicodeEncodeError) as e:
        # Log URLs with encoding issues
        logger.warning(f"URL encoding issue: {repr(url_str)[:100]}... Error: {str(e)}")
        return None

# Utility function to store URLs in database with sanitization
def store_urls_in_database(urls, batch_size=1000):
    """
    Store URLs in the database after sanitization.
    Skip any URLs with encoding issues.
    
    Args:
        urls: List of URLs to store
        batch_size: Number of URLs to process in each batch
        
    Returns:
        List of successfully stored URL objects
    """
    stored_urls = []
    new_urls = []
    
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i+batch_size]
        
        # Process this batch with proper URL sanitization
        for url_str in batch:
            # Apply sanitization to handle encoding issues
            sanitized_url = sanitize_url(url_str)
            if not sanitized_url:
                continue  # Skip invalid URLs
                
            # Check if URL already exists
            url = URL.query.filter_by(url=sanitized_url).first()
            if not url:
                url = URL(url=sanitized_url)
                db.session.add(url)
                new_urls.append(url)
            
            stored_urls.append(url)
        
        # Commit this batch to avoid large transactions
        if new_urls:
            db.session.commit()
            logger.debug(f"Added batch of {len(new_urls)} new URLs to the database")
            new_urls = []
    
    return stored_urls

# Function to process URLs in a background thread
def process_url_dataset(urls, batch_size):
    """
    Process a large URL dataset in batches using the indexing checker.
    This function is intended to be run in a background thread for large datasets.
    
    Args:
        urls: List of URLs to process
        batch_size: Number of URLs to process in each batch
    """
    global background_process_state
    
    try:
        # Set initial state
        background_process_state['total_urls'] = len(urls)
        background_process_state['processed_urls'] = 0
        background_process_state['is_processing'] = True
        
        logger.info(f"Background processing started for {len(urls)} URLs")
        
        # Store URLs in database with sanitization
        stored_urls = store_urls_in_database(urls, batch_size)
        
        # Update progress to 50% after storage phase
        processed = len(urls) // 2
        background_process_state['processed_urls'] = processed
        logger.debug(f"Storage phase completed: {len(stored_urls)} valid URLs stored in database")
        
        # Process URLs in batches to handle large numbers efficiently
        all_results = {}
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i+batch_size]
            batch_results = indexing_checker.check_urls(batch)
            all_results.update(batch_results)
            
            # Save this batch of results to database
            for url_str, is_indexed in batch_results.items():
                url = URL.query.filter_by(url=url_str).first()
                if url:
                    result = CheckResult(
                        url_id=url.id,
                        is_indexed=is_indexed,
                        checked_at=datetime.utcnow()
                    )
                    db.session.add(result)
            
            # Commit after each batch
            db.session.commit()
            
            # Update progress in global state
            # We're in the second phase, so we calculate progress from 50% to 100%
            base_progress = len(urls) // 2  # 50% already done in storage phase
            batch_progress = min(i + batch_size, len(urls)) // 2  # Up to another 50%
            processed = base_progress + batch_progress
            background_process_state['processed_urls'] = processed
            
            percent = (processed / len(urls)) * 100
            logger.debug(f"Processing phase progress: {processed}/{len(urls)} URLs processed ({percent:.1f}%)")
        
        # Create a report
        report = Report(
            name=f"Report {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            created_at=datetime.utcnow(),
            total_urls=len(urls),
            indexed_urls=sum(1 for is_indexed in all_results.values() if is_indexed)
        )
        db.session.add(report)
        db.session.commit()
        
        # Ensure progress shows 100% when complete
        background_process_state['processed_urls'] = len(urls)
        logger.info(f"Successfully processed {len(urls)} URLs in background")
    
    except Exception as e:
        logger.error(f"Error in background URL processing: {str(e)}")
    finally:
        # Make sure to update the state even in case of error
        background_process_state['is_processing'] = False

# Create database tables
with app.app_context():
    db.create_all()
    logger.debug("Database tables created")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/processing')
def processing():
    """Show processing status for large URL sets"""
    global background_process_state
    
    # Check if there's an ongoing process
    is_processing = background_process_state['is_processing']
    total_urls = background_process_state['total_urls']
    processed_urls = background_process_state['processed_urls']
    
    # Log the current state for debugging
    logger.debug(f"Processing status: is_processing={is_processing}, total={total_urls}, processed={processed_urls}")
    
    # If not processing or complete, redirect to results
    if not is_processing and processed_urls >= total_urls and total_urls > 0:
        return redirect(url_for('results'))
    
    return render_template('processing.html', 
                          total_urls=total_urls,
                          processed_urls=processed_urls)

@app.route('/api/progress')
def get_progress():
    """AJAX endpoint for getting real-time progress updates"""
    global background_process_state
    
    total = background_process_state['total_urls']
    processed = background_process_state['processed_urls']
    is_processing = background_process_state['is_processing']
    
    # Calculate percentage
    percentage = (processed / total * 100) if total > 0 else 0
    
    # If processing complete, redirect to results page
    done = False
    if not is_processing and processed >= total and total > 0:
        done = True
    
    return jsonify({
        'total': total,
        'processed': processed,
        'percentage': round(percentage, 1),
        'is_processing': is_processing,
        'done': done
    })

@app.route('/check', methods=['POST'])
def check_urls():
    global background_process_state
    
    # Configure app for large file uploads
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit for file uploads
    
    # Get URLs from either form textarea or uploaded file
    urls = []
    
    # Check if a file was uploaded - use a safer approach
    try:
        if request.files and 'url_file' in request.files:
            file = request.files['url_file']
            
            # Check if it's a valid file with a name
            if file and file.filename and (file.filename.endswith('.txt') or file.filename.endswith('.csv')):
                try:
                    # Read file content as text with a smaller buffer size
                    file_content = ""
                    for chunk in iter(lambda: file.stream.read(8192).decode('utf-8', errors='ignore'), ""):
                        file_content += chunk
                        
                    file_urls = [url.strip() for url in file_content.split('\n') if url.strip()]
                    urls.extend(file_urls)
                    logger.info(f"Loaded {len(file_urls)} URLs from uploaded file {file.filename}")
                except Exception as e:
                    logger.error(f"Error reading uploaded file: {str(e)}")
                    flash(f'Error reading file: {str(e)}', 'danger')
                    return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error accessing file uploads: {str(e)}")
        flash(f'Error processing file upload: {str(e)}', 'danger')
        return redirect(url_for('index'))
    
    # Also check the textarea for URLs
    urls_text = request.form.get('urls', '')
    if urls_text:
        textarea_urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        urls.extend(textarea_urls)
        logger.info(f"Added {len(textarea_urls)} URLs from form textarea")
    
    # Make sure we have at least one URL
    if not urls:
        flash('Please enter at least one URL to check or upload a file with URLs.', 'danger')
        return redirect(url_for('index'))
    
    # Set a very high limit for URL checking (1 million)
    max_urls = 1000000
    
    # Truncate if there are too many URLs
    if len(urls) > max_urls:
        urls = urls[:max_urls]
        flash(f'Processing the first {max_urls} URLs.', 'warning')
    
    # Check if batch processing is enabled
    batch_process = request.form.get('batch_process') == 'true'
    
    # Use larger batch size if batch processing is disabled
    batch_size = 1000 if batch_process else 10000
    
    # For large datasets, use background processing
    is_large_dataset = len(urls) > 10000
    if is_large_dataset:
        # If already processing, don't start another job
        if background_process_state['is_processing']:
            flash('Another batch of URLs is currently being processed. Please wait for it to complete.', 'warning')
            return redirect(url_for('processing'))
        
        # For large datasets, redirect to the processing page immediately
        # The actual processing will happen while the user watches the progress
        logger.info(f"Starting to process {len(urls)} URLs in batches of {batch_size}")
        flash(f'Processing {len(urls)} URLs. This may take some time for large datasets.', 'info')
        
        # Start processing in a background thread
        def process_urls_background():
            with app.app_context():
                try:
                    process_url_dataset(urls, batch_size)
                except Exception as e:
                    logger.error(f"Background processing error: {str(e)}")
                
        # Import threading only when needed
        import threading
        processing_thread = threading.Thread(target=process_urls_background)
        processing_thread.daemon = True
        processing_thread.start()
        
        return redirect(url_for('processing'))
    
    logger.info(f"Starting to process {len(urls)} URLs in batches of {batch_size}")
    flash(f'Processing {len(urls)} URLs. This may take some time for large datasets.', 'info')
    
    try:
        # Use our utility function to store URLs with sanitization
        stored_urls = store_urls_in_database(urls, batch_size)
        logger.debug(f"Added {len(stored_urls)} sanitized URLs to the database")
        
        # Process URLs in batches to handle large numbers efficiently
        all_results = {}
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i+batch_size]
            batch_results = indexing_checker.check_urls(batch)
            all_results.update(batch_results)
            
            # Save this batch of results to database
            for url_str, is_indexed in batch_results.items():
                url = URL.query.filter_by(url=url_str).first()
                if url:
                    result = CheckResult(
                        url_id=url.id,
                        is_indexed=is_indexed,
                        checked_at=datetime.utcnow()
                    )
                    db.session.add(result)
            
            # Commit after each batch
            db.session.commit()
            logger.debug(f"Saved batch of check results ({i+1}-{min(i+batch_size, len(urls))} of {len(urls)})")
        
        # Create a report
        report = Report(
            name=f"Report {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            created_at=datetime.utcnow(),
            total_urls=len(urls),
            indexed_urls=sum(1 for is_indexed in all_results.values() if is_indexed)
        )
        db.session.add(report)
        db.session.commit()
        
        flash(f'Successfully checked {len(urls)} URLs.', 'success')
        return redirect(url_for('results'))
    
    except Exception as e:
        logger.error(f"Error checking URLs: {str(e)}")
        flash(f'Error checking URLs: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/results')
def results():
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 100  # Show 100 results per page
    
    # Get total count for pagination
    total_urls = URL.query.count()
    
    # Get the URLs for this page with pagination
    paginated_urls = URL.query.order_by(URL.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # Get the latest check results for the URLs on this page only
    latest_results = []
    for url in paginated_urls.items:
        latest_result = CheckResult.query.filter_by(url_id=url.id).order_by(CheckResult.checked_at.desc()).first()
        if latest_result:
            latest_results.append({
                'url': url.url,
                'is_indexed': latest_result.is_indexed,
                'checked_at': latest_result.checked_at
            })
    
    # Calculate summary statistics
    recent_results = CheckResult.query.join(URL).order_by(CheckResult.checked_at.desc()).limit(10000).all()
    indexed_count = sum(1 for result in recent_results if result.is_indexed)
    not_indexed_count = len(recent_results) - indexed_count
    index_rate = (indexed_count / len(recent_results)) * 100 if recent_results else 0
    
    stats = {
        'total_urls': total_urls,
        'indexed_count': indexed_count,
        'not_indexed_count': not_indexed_count,
        'index_rate': index_rate
    }
    
    return render_template('results.html', 
                          results=latest_results, 
                          pagination=paginated_urls,
                          stats=stats,
                          page=page)

@app.route('/reports')
def reports():
    all_reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template('reports.html', reports=all_reports)

@app.route('/reports/<int:report_id>')
def report_detail(report_id):
    report = Report.query.get_or_404(report_id)
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 100  # Show 100 results per page
    
    # Get URLs with pagination
    urls = URL.query.order_by(URL.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # Get results for this report time period
    # For simplicity, we'll get results checked around the report creation time
    # In a real implementation, you'd associate results with specific reports
    paginated_results = []
    for url in urls.items:
        result = CheckResult.query.filter_by(url_id=url.id).filter(
            CheckResult.checked_at <= report.created_at
        ).order_by(CheckResult.checked_at.desc()).first()
        
        if result:
            paginated_results.append({
                'url': url.url,
                'is_indexed': result.is_indexed,
                'checked_at': result.checked_at
            })
    
    # For the report_data, we need to get all results
    # This is used for calculating the overall statistics and charts
    all_results = []
    # Use a more efficient query to get the relevant results for statistics
    result_stats = db.session.query(CheckResult.is_indexed, func.count(CheckResult.id)) \
        .join(URL) \
        .filter(CheckResult.checked_at <= report.created_at) \
        .group_by(CheckResult.is_indexed) \
        .all()
    
    # Build the statistics from the aggregated query results
    indexed_count = 0
    not_indexed_count = 0
    for is_indexed, count in result_stats:
        if is_indexed:
            indexed_count = count
        else:
            not_indexed_count = count
    
    total_count = indexed_count + not_indexed_count
    
    # Create a stats dictionary for the template
    stats = {
        'total_urls': total_count,
        'indexed_count': indexed_count,
        'not_indexed_count': not_indexed_count,
        'index_rate': (indexed_count / total_count * 100) if total_count > 0 else 0
    }
    
    # Generate detailed report data
    report_data = report_generator.generate_report(report, paginated_results)
    
    return render_template('report_detail.html', 
                          report=report, 
                          results=paginated_results, 
                          report_data=report_data,
                          pagination=urls,
                          stats=stats,
                          page=page)

@app.route('/export_report/<int:report_id>')
def export_report(report_id):
    report = Report.query.get_or_404(report_id)
    
    # For CSV export, we need to process all URLs in batches to handle large datasets
    results = []
    batch_size = 1000  # Process 1000 URLs at a time to avoid memory issues
    
    # Get the total number of URLs
    total_urls = URL.query.count()
    processed = 0
    
    # Process URLs in batches
    for offset in range(0, total_urls, batch_size):
        # Get a batch of URLs
        url_batch = URL.query.order_by(URL.created_at).limit(batch_size).offset(offset).all()
        
        # Process each URL in the batch
        for url in url_batch:
            result = CheckResult.query.filter_by(url_id=url.id).filter(
                CheckResult.checked_at <= report.created_at
            ).order_by(CheckResult.checked_at.desc()).first()
            
            if result:
                results.append({
                    'url': url.url,
                    'is_indexed': result.is_indexed,
                    'checked_at': result.checked_at
                })
        
        processed += len(url_batch)
        logger.debug(f"CSV Export: Processed {processed} of {total_urls} URLs")
    
    # Generate CSV report
    csv_data = report_generator.export_csv(report, results)
    
    return csv_data, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=report_{report_id}.csv'
    }
