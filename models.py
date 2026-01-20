"""
Database Models for Competitor Campaign Tracking
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class CompetitorCampaign(db.Model):
    """
    Model for storing competitor campaign data
    
    Fields as specified in Story 2.2:
    - campaign_name: Name of the campaign
    - campaign_info: Description and key details
    - source_url: Where the campaign was found
    - category: Campaign category (family, dining, seasonal, etc.)
    - scraped_date: When the campaign was discovered
    - is_active: Whether the campaign is still active
    """
    __tablename__ = 'competitor_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_name = db.Column(db.String(500), nullable=False)
    campaign_info = db.Column(db.Text, nullable=True)
    source_url = db.Column(db.String(1000), nullable=False)
    category = db.Column(db.String(100), nullable=True, default='general')
    scraped_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_seen_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    competitor_name = db.Column(db.String(100), nullable=False, default='Marriott')
    
    # Additional metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicates
    __table_args__ = (
        db.UniqueConstraint('campaign_name', 'competitor_name', name='unique_campaign_per_competitor'),
    )
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'campaign_name': self.campaign_name,
            'campaign_info': self.campaign_info,
            'source_url': self.source_url,
            'category': self.category,
            'scraped_date': self.scraped_date.isoformat() if self.scraped_date else None,
            'last_seen_date': self.last_seen_date.isoformat() if self.last_seen_date else None,
            'is_active': self.is_active,
            'competitor_name': self.competitor_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'days_since_update': (datetime.utcnow() - self.last_seen_date).days if self.last_seen_date else None
        }
    
    def __repr__(self):
        return f'<Campaign {self.campaign_name[:50]}... ({self.competitor_name})>'


class ScrapeLog(db.Model):
    """
    Model for logging scraping activities
    """
    __tablename__ = 'scrape_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    scrape_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    competitor_name = db.Column(db.String(100), nullable=False)
    source_url = db.Column(db.String(1000), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # success, failed, partial
    campaigns_found = db.Column(db.Integer, nullable=False, default=0)
    new_campaigns = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'scrape_date': self.scrape_date.isoformat() if self.scrape_date else None,
            'competitor_name': self.competitor_name,
            'source_url': self.source_url,
            'status': self.status,
            'campaigns_found': self.campaigns_found,
            'new_campaigns': self.new_campaigns,
            'error_message': self.error_message
        }
