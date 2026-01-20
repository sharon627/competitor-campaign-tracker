"""
Web Scraper for Marriott China Campaigns

Story 2.1: Campaign Data Extraction
- Scrapes Marriott's Chinese homepage for campaign data
- Extracts campaign names, descriptions, and metadata
- Handles Chinese character encoding properly
- Identifies campaign categories
"""
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarriottChinaScraper:
    """
    Scraper for Marriott China promotional campaigns
    """
    
    # Campaign category keywords mapping (Chinese to English categories)
    CATEGORY_KEYWORDS = {
        'family': ['亲子', '家庭', '儿童', '家族', '亲情', '孩子'],
        'dining': ['餐饮', '美食', '餐厅', '饮食', '用餐', '早餐', '晚餐', '自助餐'],
        'seasonal': ['季节', '春', '夏', '秋', '冬', '节日', '新年', '圣诞', '春节', '中秋'],
        'rewards': ['积分', '会员', '旅享家', '奖励', '里程', '返现', 'Bonvoy'],
        'travel': ['旅行', '度假', '出行', '旅游', '游玩', '探索'],
        'business': ['商务', '会议', '办公', '差旅'],
        'spa': ['水疗', 'SPA', '养生', '按摩', '理疗'],
        'wedding': ['婚礼', '婚宴', '婚庆', '蜜月'],
        'promotion': ['优惠', '折扣', '特价', '促销', '立减', '返利'],
    }
    
    def __init__(self, user_agent: str = None):
        """Initialize the scraper with custom user agent"""
        self.user_agent = user_agent or (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def _detect_category(self, text: str) -> str:
        """
        Detect campaign category based on Chinese keywords
        
        Args:
            text: Campaign name or description text
            
        Returns:
            Category string (e.g., 'family', 'dining', etc.)
        """
        if not text:
            return 'general'
        
        text_lower = text.lower()
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return category
        
        return 'general'
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text, handling Chinese characters properly
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ''
        
        # Remove extra whitespace while preserving Chinese characters
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return parsed BeautifulSoup object
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if fetch failed
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Handle Chinese encoding properly
            response.encoding = response.apparent_encoding or 'utf-8'
            
            return BeautifulSoup(response.text, 'lxml')
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def scrape_homepage(self, url: str = 'https://www.marriott.com.cn/default.mi') -> List[Dict]:
        """
        Scrape Marriott China homepage for promotional campaigns
        
        Args:
            url: Homepage URL
            
        Returns:
            List of campaign dictionaries
        """
        campaigns = []
        soup = self._fetch_page(url)
        
        if not soup:
            return campaigns
        
        # Look for promotional sections - these selectors may need adjustment
        # based on actual page structure
        promo_selectors = [
            '.promotion-card',
            '.offer-card',
            '.campaign-item',
            '.promo-section',
            '[data-component="offer"]',
            '.m-offer-card',
            '.l-container-offers',
            '.offers-list-item',
            'article.offer',
            '.hero-banner',
            '.promo-banner',
        ]
        
        for selector in promo_selectors:
            elements = soup.select(selector)
            for element in elements:
                campaign = self._extract_campaign_from_element(element, url)
                if campaign and campaign.get('campaign_name'):
                    campaigns.append(campaign)
        
        # Also look for generic promotional content
        campaigns.extend(self._extract_from_generic_elements(soup, url))
        
        logger.info(f"Found {len(campaigns)} campaigns from {url}")
        return campaigns
    
    def scrape_offers_page(self, url: str = 'https://www.marriott.com.cn/specials/offers.mi') -> List[Dict]:
        """
        Scrape Marriott China offers page for promotional campaigns
        
        Args:
            url: Offers page URL
            
        Returns:
            List of campaign dictionaries
        """
        campaigns = []
        soup = self._fetch_page(url)
        
        if not soup:
            return campaigns
        
        # Offers page specific selectors
        offer_selectors = [
            '.offer-tile',
            '.special-offer',
            '.offer-item',
            '.offers-card',
            '[class*="offer"]',
            '[class*="promotion"]',
        ]
        
        for selector in offer_selectors:
            elements = soup.select(selector)
            for element in elements:
                campaign = self._extract_campaign_from_element(element, url)
                if campaign and campaign.get('campaign_name'):
                    campaigns.append(campaign)
        
        logger.info(f"Found {len(campaigns)} campaigns from offers page")
        return campaigns
    
    def scrape_bonvoy_page(self, url: str = 'https://www.marriott.com.cn/marriott-bonvoy/member-benefits.mi') -> List[Dict]:
        """
        Scrape Marriott Bonvoy member benefits page
        
        Args:
            url: Bonvoy benefits page URL
            
        Returns:
            List of campaign dictionaries
        """
        campaigns = []
        soup = self._fetch_page(url)
        
        if not soup:
            return campaigns
        
        # Bonvoy page specific selectors
        benefit_selectors = [
            '.benefit-card',
            '.member-benefit',
            '.bonvoy-offer',
            '[class*="benefit"]',
            '[class*="member"]',
        ]
        
        for selector in benefit_selectors:
            elements = soup.select(selector)
            for element in elements:
                campaign = self._extract_campaign_from_element(element, url)
                if campaign and campaign.get('campaign_name'):
                    campaigns.append(campaign)
        
        logger.info(f"Found {len(campaigns)} campaigns from Bonvoy page")
        return campaigns
    
    def _extract_campaign_from_element(self, element, source_url: str) -> Optional[Dict]:
        """
        Extract campaign data from a BeautifulSoup element
        
        Args:
            element: BeautifulSoup element
            source_url: Source URL for reference
            
        Returns:
            Campaign dictionary or None
        """
        try:
            # Try to find campaign name from various elements
            name = None
            name_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.name', '.heading', '[class*="title"]']
            
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    name = self._clean_text(name_elem.get_text())
                    if name and len(name) > 3:  # Minimum reasonable length
                        break
            
            if not name:
                return None
            
            # Try to find description
            info = None
            info_selectors = ['p', '.description', '.info', '.content', '.summary', '[class*="desc"]']
            
            for selector in info_selectors:
                info_elem = element.select_one(selector)
                if info_elem and info_elem != element.select_one(name_selectors[0] if name_selectors else 'h1'):
                    info = self._clean_text(info_elem.get_text())
                    if info and len(info) > 10:
                        break
            
            # Get link if available
            link = element.select_one('a')
            campaign_url = source_url
            if link and link.get('href'):
                campaign_url = urljoin(source_url, link.get('href'))
            
            # Detect category
            combined_text = f"{name} {info or ''}"
            category = self._detect_category(combined_text)
            
            return {
                'campaign_name': name,
                'campaign_info': info,
                'source_url': campaign_url,
                'category': category,
                'scraped_date': datetime.utcnow(),
                'competitor_name': 'Marriott'
            }
            
        except Exception as e:
            logger.error(f"Error extracting campaign: {e}")
            return None
    
    def _extract_from_generic_elements(self, soup: BeautifulSoup, source_url: str) -> List[Dict]:
        """
        Extract campaigns from generic page elements when specific selectors don't match
        
        Args:
            soup: BeautifulSoup object
            source_url: Source URL
            
        Returns:
            List of campaign dictionaries
        """
        campaigns = []
        
        # Look for sections with Chinese promotional text patterns
        promo_patterns = [
            r'.*优惠.*',
            r'.*促销.*',
            r'.*特价.*',
            r'.*活动.*',
            r'.*会员.*专享.*',
        ]
        
        # Find headings that match promotional patterns
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = self._clean_text(heading.get_text())
            
            if any(re.match(pattern, text) for pattern in promo_patterns):
                # Found a promotional heading, try to get its description
                info = None
                next_elem = heading.find_next_sibling()
                if next_elem and next_elem.name == 'p':
                    info = self._clean_text(next_elem.get_text())
                
                campaign = {
                    'campaign_name': text,
                    'campaign_info': info,
                    'source_url': source_url,
                    'category': self._detect_category(text),
                    'scraped_date': datetime.utcnow(),
                    'competitor_name': 'Marriott'
                }
                campaigns.append(campaign)
        
        return campaigns
    
    def scrape_all(self, urls: List[str] = None) -> List[Dict]:
        """
        Scrape all configured URLs and return combined results
        
        Args:
            urls: List of URLs to scrape (optional)
            
        Returns:
            List of all unique campaigns found
        """
        if urls is None:
            urls = [
                'https://www.marriott.com.cn/default.mi',
                'https://www.marriott.com.cn/specials/offers.mi',
                'https://www.marriott.com.cn/marriott-bonvoy/member-benefits.mi',
            ]
        
        all_campaigns = []
        seen_names = set()
        
        for url in urls:
            try:
                if 'offers' in url:
                    campaigns = self.scrape_offers_page(url)
                elif 'bonvoy' in url or 'member' in url:
                    campaigns = self.scrape_bonvoy_page(url)
                else:
                    campaigns = self.scrape_homepage(url)
                
                # Deduplicate by campaign name
                for campaign in campaigns:
                    name = campaign.get('campaign_name', '')
                    if name and name not in seen_names:
                        seen_names.add(name)
                        all_campaigns.append(campaign)
                        
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
        
        logger.info(f"Total unique campaigns found: {len(all_campaigns)}")
        return all_campaigns


# Demo/test data for development when scraping isn't available
def get_demo_campaigns() -> List[Dict]:
    """
    Return demo campaign data for testing and development
    """
    return [
        {
            'campaign_name': '万豪旅享家亲子主题房',
            'campaign_info': '为家庭旅客打造的专属主题房体验，包含儿童欢迎礼品、亲子活动及家庭套餐优惠。入住即享专属儿童用品和游乐设施。',
            'source_url': 'https://www.marriott.com.cn/specials/family-theme-room.mi',
            'category': 'family',
            'scraped_date': datetime.utcnow(),
            'competitor_name': 'Marriott'
        },
        {
            'campaign_name': '万豪旅享家会员积分加倍',
            'campaign_info': '限时活动：预订指定酒店可获得双倍积分奖励。会员专享，积分可兑换免费住宿及多种礼遇。',
            'source_url': 'https://www.marriott.com.cn/marriott-bonvoy/double-points.mi',
            'category': 'rewards',
            'scraped_date': datetime.utcnow(),
            'competitor_name': 'Marriott'
        },
        {
            'campaign_name': '春季美食节特别优惠',
            'campaign_info': '品尝春季限定美食，指定餐厅消费满额享8折优惠。包含多款时令菜品和精选套餐。',
            'source_url': 'https://www.marriott.com.cn/dining/spring-food-festival.mi',
            'category': 'dining',
            'scraped_date': datetime.utcnow(),
            'competitor_name': 'Marriott'
        },
        {
            'campaign_name': '商务差旅尊享计划',
            'campaign_info': '为商务旅客定制的专属礼遇，包含延迟退房、行政酒廊使用权及专属商务服务。',
            'source_url': 'https://www.marriott.com.cn/specials/business-travel.mi',
            'category': 'business',
            'scraped_date': datetime.utcnow(),
            'competitor_name': 'Marriott'
        },
        {
            'campaign_name': '水疗养生套餐',
            'campaign_info': '尊享90分钟身心放松体验，包含特色按摩及水疗护理。预订住宿套餐可享专属折扣。',
            'source_url': 'https://www.marriott.com.cn/specials/spa-wellness.mi',
            'category': 'spa',
            'scraped_date': datetime.utcnow(),
            'competitor_name': 'Marriott'
        },
        {
            'campaign_name': '周末度假特惠',
            'campaign_info': '周五至周日入住指定度假酒店，享房价7折优惠，含双人早餐及度假村活动体验。',
            'source_url': 'https://www.marriott.com.cn/specials/weekend-getaway.mi',
            'category': 'travel',
            'scraped_date': datetime.utcnow(),
            'competitor_name': 'Marriott'
        },
        {
            'campaign_name': '新会员首住礼遇',
            'campaign_info': '新注册万豪旅享家会员首次入住即获500积分奖励，更有机会升级房型。',
            'source_url': 'https://www.marriott.com.cn/marriott-bonvoy/new-member.mi',
            'category': 'rewards',
            'scraped_date': datetime.utcnow(),
            'competitor_name': 'Marriott'
        },
        {
            'campaign_name': '婚礼场地预订优惠',
            'campaign_info': '2024年婚宴预订享专属优惠，包含场地布置、定制菜单及新人住宿礼遇。',
            'source_url': 'https://www.marriott.com.cn/meetings/weddings.mi',
            'category': 'wedding',
            'scraped_date': datetime.utcnow(),
            'competitor_name': 'Marriott'
        },
    ]


if __name__ == '__main__':
    # Test the scraper
    scraper = MarriottChinaScraper()
    
    print("Testing with demo data:")
    demo_campaigns = get_demo_campaigns()
    for campaign in demo_campaigns:
        print(f"- {campaign['campaign_name']} ({campaign['category']})")
    
    print("\nAttempting live scrape...")
    campaigns = scraper.scrape_all()
    
    if campaigns:
        print(f"\nFound {len(campaigns)} campaigns:")
        for campaign in campaigns:
            print(f"- {campaign['campaign_name']} ({campaign['category']})")
    else:
        print("No campaigns found from live scrape. Using demo data for development.")
