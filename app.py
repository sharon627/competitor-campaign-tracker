"""
Flask Application - Competitor Campaign Tracking Website

Stories 2.2 & 2.3: Data Storage & Website Display Integration
"""
import os
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from sqlalchemy import or_

from config import config
from models import db, CompetitorCampaign, ScrapeLog
from scraper import MarriottChinaScraper, get_demo_campaigns


def create_app(config_name: str = None):
    """Application factory"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register routes
    register_routes(app)
    
    return app


def register_routes(app: Flask):
    """Register all application routes"""
    
    # ==================== Frontend Routes ====================
    
    @app.route('/')
    def index():
        """Serve the main dashboard page"""
        return render_template('index.html')
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files"""
        return send_from_directory(app.static_folder, filename)
    
    # ==================== API Routes ====================
    
    @app.route('/api/campaigns', methods=['GET'])
    def get_campaigns():
        """
        Get all campaigns with optional filtering
        
        Query Parameters:
        - competitor: Filter by competitor name (default: all)
        - category: Filter by category
        - is_active: Filter by active status (true/false)
        - search: Search in campaign name and info
        - limit: Number of results (default: 50)
        - offset: Pagination offset (default: 0)
        """
        try:
            # Build query
            query = CompetitorCampaign.query
            
            # Filter by competitor
            competitor = request.args.get('competitor')
            if competitor:
                query = query.filter(CompetitorCampaign.competitor_name.ilike(f'%{competitor}%'))
            
            # Filter by category
            category = request.args.get('category')
            if category and category != 'all':
                query = query.filter(CompetitorCampaign.category == category)
            
            # Filter by active status
            is_active = request.args.get('is_active')
            if is_active is not None:
                is_active_bool = is_active.lower() == 'true'
                query = query.filter(CompetitorCampaign.is_active == is_active_bool)
            
            # Search in name and info
            search = request.args.get('search')
            if search:
                search_pattern = f'%{search}%'
                query = query.filter(
                    or_(
                        CompetitorCampaign.campaign_name.ilike(search_pattern),
                        CompetitorCampaign.campaign_info.ilike(search_pattern)
                    )
                )
            
            # Order by most recently seen
            query = query.order_by(CompetitorCampaign.last_seen_date.desc())
            
            # Pagination
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            campaigns = query.offset(offset).limit(limit).all()
            
            return jsonify({
                'success': True,
                'data': [c.to_dict() for c in campaigns],
                'total': total,
                'limit': limit,
                'offset': offset
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/campaigns/<int:campaign_id>', methods=['GET'])
    def get_campaign(campaign_id: int):
        """Get a specific campaign by ID"""
        try:
            campaign = CompetitorCampaign.query.get_or_404(campaign_id)
            return jsonify({
                'success': True,
                'data': campaign.to_dict()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 404
    
    @app.route('/api/categories', methods=['GET'])
    def get_categories():
        """Get all unique campaign categories"""
        try:
            categories = db.session.query(
                CompetitorCampaign.category
            ).distinct().all()
            
            category_list = [c[0] for c in categories if c[0]]
            
            return jsonify({
                'success': True,
                'data': sorted(category_list)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/competitors', methods=['GET'])
    def get_competitors():
        """Get all unique competitor names"""
        try:
            competitors = db.session.query(
                CompetitorCampaign.competitor_name
            ).distinct().all()
            
            competitor_list = [c[0] for c in competitors if c[0]]
            
            return jsonify({
                'success': True,
                'data': sorted(competitor_list)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """Get campaign statistics"""
        try:
            total_campaigns = CompetitorCampaign.query.count()
            active_campaigns = CompetitorCampaign.query.filter_by(is_active=True).count()
            
            # Category breakdown
            category_stats = db.session.query(
                CompetitorCampaign.category,
                db.func.count(CompetitorCampaign.id)
            ).group_by(CompetitorCampaign.category).all()
            
            # Competitor breakdown
            competitor_stats = db.session.query(
                CompetitorCampaign.competitor_name,
                db.func.count(CompetitorCampaign.id)
            ).group_by(CompetitorCampaign.competitor_name).all()
            
            # Last scrape info
            last_scrape = ScrapeLog.query.order_by(ScrapeLog.scrape_date.desc()).first()
            
            return jsonify({
                'success': True,
                'data': {
                    'total_campaigns': total_campaigns,
                    'active_campaigns': active_campaigns,
                    'inactive_campaigns': total_campaigns - active_campaigns,
                    'categories': {c[0]: c[1] for c in category_stats},
                    'competitors': {c[0]: c[1] for c in competitor_stats},
                    'last_scrape': last_scrape.to_dict() if last_scrape else None
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/scrape', methods=['POST'])
    def trigger_scrape():
        """
        Manually trigger a scrape operation
        
        Request Body (optional):
        - use_demo: boolean - Use demo data instead of live scraping
        """
        try:
            data = request.get_json() or {}
            use_demo = data.get('use_demo', False)
            
            if use_demo:
                campaigns_data = get_demo_campaigns()
            else:
                scraper = MarriottChinaScraper()
                campaigns_data = scraper.scrape_all()
                
                # If no campaigns found, fall back to demo data
                if not campaigns_data:
                    campaigns_data = get_demo_campaigns()
                    use_demo = True
            
            # Save campaigns to database
            new_count = 0
            updated_count = 0
            
            for campaign_data in campaigns_data:
                result = save_campaign(campaign_data)
                if result == 'new':
                    new_count += 1
                elif result == 'updated':
                    updated_count += 1
            
            # Mark campaigns not seen in this scrape as potentially inactive
            # (Only if we found some campaigns)
            if campaigns_data:
                mark_inactive_campaigns(campaigns_data)
            
            # Log the scrape
            log = ScrapeLog(
                competitor_name='Marriott',
                source_url='https://www.marriott.com.cn',
                status='success',
                campaigns_found=len(campaigns_data),
                new_campaigns=new_count
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Scrape completed successfully',
                'data': {
                    'campaigns_found': len(campaigns_data),
                    'new_campaigns': new_count,
                    'updated_campaigns': updated_count,
                    'used_demo_data': use_demo
                }
            })
            
        except Exception as e:
            # Log failed scrape
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
            
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/scrape/logs', methods=['GET'])
    def get_scrape_logs():
        """Get scrape history logs"""
        try:
            limit = request.args.get('limit', 20, type=int)
            logs = ScrapeLog.query.order_by(
                ScrapeLog.scrape_date.desc()
            ).limit(limit).all()
            
            return jsonify({
                'success': True,
                'data': [log.to_dict() for log in logs]
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        })


def save_campaign(campaign_data: dict) -> str:
    """
    Save or update a campaign in the database
    
    Story 2.2 Requirements:
    - Duplicate campaigns are detected and not re-added
    - Data is validated before storage
    
    Args:
        campaign_data: Campaign dictionary
        
    Returns:
        'new', 'updated', or 'skipped'
    """
    # Validate required fields
    if not campaign_data.get('campaign_name'):
        return 'skipped'
    
    # Check for existing campaign
    existing = CompetitorCampaign.query.filter_by(
        campaign_name=campaign_data['campaign_name'],
        competitor_name=campaign_data.get('competitor_name', 'Marriott')
    ).first()
    
    if existing:
        # Update existing campaign
        existing.campaign_info = campaign_data.get('campaign_info') or existing.campaign_info
        existing.source_url = campaign_data.get('source_url') or existing.source_url
        existing.category = campaign_data.get('category') or existing.category
        existing.last_seen_date = datetime.utcnow()
        existing.is_active = True
        
        db.session.commit()
        return 'updated'
    else:
        # Create new campaign
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


def mark_inactive_campaigns(current_campaigns: list):
    """
    Mark campaigns as inactive if they weren't seen in the current scrape
    
    Story 2.2 Requirement:
    - Old/inactive campaigns are flagged after they disappear from source
    
    Args:
        current_campaigns: List of campaign dicts from current scrape
    """
    current_names = {c.get('campaign_name') for c in current_campaigns if c.get('campaign_name')}
    
    # Get all active Marriott campaigns
    active_campaigns = CompetitorCampaign.query.filter_by(
        competitor_name='Marriott',
        is_active=True
    ).all()
    
    for campaign in active_campaigns:
        if campaign.campaign_name not in current_names:
            # Check if it's been missing for more than 3 scrapes (roughly 3 days)
            days_since_seen = (datetime.utcnow() - campaign.last_seen_date).days
            if days_since_seen > 3:
                campaign.is_active = False
    
    db.session.commit()


# Create the application instance
app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
