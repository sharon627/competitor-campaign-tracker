"""
Main Entry Point - Competitor Campaign Tracker

This script starts the Flask application with the automated scheduler.
"""
import os
import sys

from app import create_app
from scheduler import init_scheduler


def main():
    """
    Start the application with optional scheduler
    
    Usage:
        python run.py              # Start web server only
        python run.py --scheduler  # Start web server with scheduler
        python run.py --init       # Initialize DB and load demo data
    """
    # Parse arguments
    enable_scheduler = '--scheduler' in sys.argv
    init_data = '--init' in sys.argv
    
    # Create application
    app = create_app()
    
    # Initialize database and load demo data if requested
    if init_data:
        with app.app_context():
            from models import db
            from scraper import get_demo_campaigns
            from app import save_campaign
            
            print("Initializing database...")
            db.create_all()
            
            print("Loading demo campaign data...")
            demo_campaigns = get_demo_campaigns()
            
            for campaign_data in demo_campaigns:
                result = save_campaign(campaign_data)
                print(f"  - {campaign_data['campaign_name'][:40]}... ({result})")
            
            print(f"\nLoaded {len(demo_campaigns)} demo campaigns.")
            print("You can now start the server with: python run.py")
            return
    
    # Start scheduler if enabled
    if enable_scheduler:
        print("Starting scheduler...")
        scheduler = init_scheduler(app, run_immediately=False)
        print("Scheduler started - will run daily at 6:00 AM")
    
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          Competitor Campaign Tracker - Marriott China        ║
╠══════════════════════════════════════════════════════════════╣
║  Server:    http://{host}:{port}                              
║  Debug:     {debug}                                           
║  Scheduler: {'Enabled (daily at 6:00 AM)' if enable_scheduler else 'Disabled'}
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run the application
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
