"""
Automated Scheduler for Campaign Scraping

Story 2.1: Runs daily via automated scheduler
- Configurable scrape interval
- Logs all scraping activities
- Handles errors gracefully
"""
import logging
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import Config
from models import db, CompetitorCampaign, ScrapeLog
from scraper import MarriottChinaScraper, get_demo_campaigns

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CampaignScheduler:
    """
    Scheduler for automated campaign scraping
    """
    
    def __init__(self, app=None):
        self.app = app
        self.scheduler = BackgroundScheduler()
        self.scraper = MarriottChinaScraper(user_agent=Config.USER_AGENT)
    
    def init_app(self, app):
        """Initialize scheduler with Flask app context"""
        self.app = app
    
    def scrape_job(self):
        """
        Main scraping job - runs on schedule
        """
        logger.info("Starting scheduled scrape job...")
        
        with self.app.app_context():
            try:
                # Run the scraper
                campaigns_data = self.scraper.scrape_all(Config.MARRIOTT_CHINA_URLS)
                
                # If no campaigns found, use demo data (for development)
                use_demo = False
                if not campaigns_data:
                    logger.warning("No campaigns found from live scrape, using demo data")
                    campaigns_data = get_demo_campaigns()
                    use_demo = True
                
                # Save campaigns to database
                new_count = 0
                updated_count = 0
                
                for campaign_data in campaigns_data:
                    result = self._save_campaign(campaign_data)
                    if result == 'new':
                        new_count += 1
                    elif result == 'updated':
                        updated_count += 1
                
                # Mark inactive campaigns
                if campaigns_data:
                    self._mark_inactive_campaigns(campaigns_data)
                
                # Log success
                log = ScrapeLog(
                    competitor_name='Marriott',
                    source_url='https://www.marriott.com.cn',
                    status='success',
                    campaigns_found=len(campaigns_data),
                    new_campaigns=new_count
                )
                db.session.add(log)
                db.session.commit()
                
                logger.info(
                    f"Scrape completed: {len(campaigns_data)} found, "
                    f"{new_count} new, {updated_count} updated"
                    f"{' (demo data)' if use_demo else ''}"
                )
                
            except Exception as e:
                logger.error(f"Scrape job failed: {e}")
                
                # Log failure
                try:
                    log = ScrapeLog(
                        competitor_name='Marriott',
                        source_url='https://www.marriott.com.cn',
                        status='failed',
                        campaigns_found=0,
                        new_campaigns=0,
                        error_message=str(e)
                    )
                    db.session.add(log)
                    db.session.commit()
                except:
                    pass
    
    def _save_campaign(self, campaign_data: dict) -> str:
        """
        Save or update a campaign in the database
        
        Returns: 'new', 'updated', or 'skipped'
        """
        if not campaign_data.get('campaign_name'):
            return 'skipped'
        
        existing = CompetitorCampaign.query.filter_by(
            campaign_name=campaign_data['campaign_name'],
            competitor_name=campaign_data.get('competitor_name', 'Marriott')
        ).first()
        
        if existing:
            existing.campaign_info = campaign_data.get('campaign_info') or existing.campaign_info
            existing.source_url = campaign_data.get('source_url') or existing.source_url
            existing.category = campaign_data.get('category') or existing.category
            existing.last_seen_date = datetime.utcnow()
            existing.is_active = True
            db.session.commit()
            return 'updated'
        else:
            campaign = CompetitorCampaign(
                campaign_name=campaign_data['campaign_name'],
                campaign_info=campaign_data.get('campaign_info'),
                source_url=campaign_data.get('source_url', ''),
                category=campaign_data.get('category', 'general'),
                competitor_name=campaign_data.get('competitor_name', 'Marriott'),
                scraped_date=campaign_data.get('scraped_date', datetime.utcnow()),
                last_seen_date=datetime.utcnow(),
                is_active=True
            )
            db.session.add(campaign)
            db.session.commit()
            return 'new'
    
    def _mark_inactive_campaigns(self, current_campaigns: list):
        """Mark campaigns as inactive if not seen in current scrape"""
        current_names = {c.get('campaign_name') for c in current_campaigns if c.get('campaign_name')}
        
        active_campaigns = CompetitorCampaign.query.filter_by(
            competitor_name='Marriott',
            is_active=True
        ).all()
        
        for campaign in active_campaigns:
            if campaign.campaign_name not in current_names:
                days_since_seen = (datetime.utcnow() - campaign.last_seen_date).days
                if days_since_seen > 3:
                    campaign.is_active = False
        
        db.session.commit()
    
    def start(self, run_immediately=False):
        """
        Start the scheduler
        
        Args:
            run_immediately: Run a scrape job immediately on startup
        """
        # Schedule daily scrape at 6 AM
        self.scheduler.add_job(
            self.scrape_job,
            CronTrigger(hour=6, minute=0),
            id='daily_scrape',
            name='Daily campaign scrape',
            replace_existing=True
        )
        
        # Alternative: interval-based scheduling
        # self.scheduler.add_job(
        #     self.scrape_job,
        #     IntervalTrigger(hours=Config.SCRAPE_INTERVAL_HOURS),
        #     id='interval_scrape',
        #     name='Interval campaign scrape',
        #     replace_existing=True
        # )
        
        self.scheduler.start()
        logger.info("Scheduler started - daily scrape scheduled for 6:00 AM")
        
        if run_immediately:
            logger.info("Running initial scrape...")
            self.scrape_job()
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        return [
            {
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in self.scheduler.get_jobs()
        ]


# Create scheduler instance
campaign_scheduler = CampaignScheduler()


def init_scheduler(app, run_immediately=False):
    """
    Initialize and start the scheduler with the Flask app
    
    Args:
        app: Flask application instance
        run_immediately: Run a scrape immediately on startup
    """
    campaign_scheduler.init_app(app)
    campaign_scheduler.start(run_immediately=run_immediately)
    return campaign_scheduler


if __name__ == '__main__':
    # Test the scheduler standalone
    from app import create_app
    
    app = create_app()
    scheduler = init_scheduler(app, run_immediately=True)
    
    print("Scheduler is running. Press Ctrl+C to exit.")
    
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.stop()
        print("Scheduler stopped.")
