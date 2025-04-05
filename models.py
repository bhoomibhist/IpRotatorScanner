from datetime import datetime
from app import db

class URL(db.Model):
    """Model for storing URLs to check."""
    __tablename__ = 'urls'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    results = db.relationship('CheckResult', backref='url_ref', lazy=True)
    
    def __repr__(self):
        return f'<URL {self.url}>'

class CheckResult(db.Model):
    """Model for storing the results of indexing checks."""
    __tablename__ = 'check_results'
    
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('urls.id'), nullable=False)
    is_indexed = db.Column(db.Boolean, nullable=False)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)
    proxy_used = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<CheckResult {self.id} for URL {self.url_id}>'

class Report(db.Model):
    """Model for storing generated reports."""
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_urls = db.Column(db.Integer, default=0)
    indexed_urls = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Report {self.name}>'
    
    @property
    def indexed_percentage(self):
        if self.total_urls == 0:
            return 0
        return round((self.indexed_urls / self.total_urls) * 100, 2)
