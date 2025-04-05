import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
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

# Configure SQLite database for MVP
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///indexing_checker.db")
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

# Initialize components
proxy_manager = ProxyManager()
indexing_checker = IndexingChecker(proxy_manager)
report_generator = ReportGenerator()

# Create database tables
with app.app_context():
    db.create_all()
    logger.debug("Database tables created")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_urls():
    urls_text = request.form.get('urls', '')
    urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
    
    if not urls:
        flash('Please enter at least one URL to check.', 'danger')
        return redirect(url_for('index'))
    
    # Store URLs in database if they don't exist
    new_urls = []
    for url_str in urls:
        url = URL.query.filter_by(url=url_str).first()
        if not url:
            url = URL(url=url_str)
            db.session.add(url)
            new_urls.append(url)
    
    if new_urls:
        db.session.commit()
        logger.debug(f"Added {len(new_urls)} new URLs to the database")
    
    # Start checking the URLs
    try:
        results = indexing_checker.check_urls(urls)
        
        # Save results to database
        for url_str, is_indexed in results.items():
            url = URL.query.filter_by(url=url_str).first()
            if url:
                result = CheckResult(
                    url_id=url.id,
                    is_indexed=is_indexed,
                    checked_at=datetime.utcnow()
                )
                db.session.add(result)
        
        db.session.commit()
        logger.debug("Saved check results to database")
        
        # Create a report
        report = Report(
            name=f"Report {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            created_at=datetime.utcnow(),
            total_urls=len(urls),
            indexed_urls=sum(1 for is_indexed in results.values() if is_indexed)
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
    # Get the latest check results
    latest_results = []
    for url in URL.query.all():
        latest_result = CheckResult.query.filter_by(url_id=url.id).order_by(CheckResult.checked_at.desc()).first()
        if latest_result:
            latest_results.append({
                'url': url.url,
                'is_indexed': latest_result.is_indexed,
                'checked_at': latest_result.checked_at
            })
    
    return render_template('results.html', results=latest_results)

@app.route('/reports')
def reports():
    all_reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template('reports.html', reports=all_reports)

@app.route('/reports/<int:report_id>')
def report_detail(report_id):
    report = Report.query.get_or_404(report_id)
    
    # Get results for this report time period
    # For simplicity, we'll get results checked around the report creation time
    # In a real implementation, you'd associate results with specific reports
    results = []
    for url in URL.query.all():
        result = CheckResult.query.filter_by(url_id=url.id).filter(
            CheckResult.checked_at <= report.created_at
        ).order_by(CheckResult.checked_at.desc()).first()
        
        if result:
            results.append({
                'url': url.url,
                'is_indexed': result.is_indexed,
                'checked_at': result.checked_at
            })
    
    # Generate detailed report data
    report_data = report_generator.generate_report(report, results)
    
    return render_template('report_detail.html', report=report, results=results, report_data=report_data)

@app.route('/export_report/<int:report_id>')
def export_report(report_id):
    report = Report.query.get_or_404(report_id)
    
    # Similar to report_detail, get results for this report
    results = []
    for url in URL.query.all():
        result = CheckResult.query.filter_by(url_id=url.id).filter(
            CheckResult.checked_at <= report.created_at
        ).order_by(CheckResult.checked_at.desc()).first()
        
        if result:
            results.append({
                'url': url.url,
                'is_indexed': result.is_indexed,
                'checked_at': result.checked_at
            })
    
    # Generate CSV report
    csv_data = report_generator.export_csv(report, results)
    
    return csv_data, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=report_{report_id}.csv'
    }
