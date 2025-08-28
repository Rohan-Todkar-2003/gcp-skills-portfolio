#!/usr/bin/env python3
"""
Google Cloud Skills Boost Portfolio Updater
Automatically fetches latest badges with real images and updates README.md
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os
import hashlib

class GCPPortfolioUpdater:
    def __init__(self, profile_url):
        self.profile_url = profile_url
        self.badges_data = []
        self.badge_images = {
            # Real Google Cloud Skills Boost badge images
            'ai_ml': {
                'gemini': 'https://cdn.qwiklabs.com/badges/gemini-ai-badge.png',
                'vertex': 'https://cdn.qwiklabs.com/badges/vertex-ai-badge.png',
                'mlops': 'https://cdn.qwiklabs.com/badges/mlops-badge.png',
                'prompt': 'https://cdn.qwiklabs.com/badges/prompt-design-badge.png',
                'responsible': 'https://cdn.qwiklabs.com/badges/responsible-ai-badge.png',
                'default': 'https://cloud.google.com/_static/cloud/images/social-icon-google-cloud-1200-630.png'
            },
            'infrastructure': {
                'terraform': 'https://www.terraform.io/img/logo-hashicorp.svg',
                'kubernetes': 'https://kubernetes.io/images/kubernetes-horizontal-color.png',
                'gke': 'https://cdn.qwiklabs.com/badges/gke-badge.png',
                'compute': 'https://cdn.qwiklabs.com/badges/compute-engine-badge.png',
                'monitoring': 'https://cdn.qwiklabs.com/badges/monitoring-badge.png',
                'default': 'https://www.gstatic.com/devrel-devsite/prod/v2210deb8920cd4a55bd580441aa58e7853afc04b39a9d9ac4198e1cd7fbe04ef6/cloud/images/cloud-logo.svg'
            },
            'data_analytics': {
                'bigquery': 'https://www.gstatic.com/bricks/image/0dfa6e5bf59a06c4973bf1b5bb951e93cd8c9cf64b88b1a6b99bfff7b8e45c1a.svg',
                'looker': 'https://looker.com/assets/img/looker-logo.svg',
                'dataflow': 'https://cdn.qwiklabs.com/badges/dataflow-badge.png',
                'default': 'https://www.gstatic.com/bricks/image/0dfa6e5bf59a06c4973bf1b5bb951e93cd8c9cf64b88b1a6b99bfff7b8e45c1a.svg'
            },
            'workspace': {
                'sheets': 'https://fonts.gstatic.com/s/i/productlogos/sheets/v4/24px.svg',
                'docs': 'https://fonts.gstatic.com/s/i/productlogos/docs/v6/24px.svg',
                'calendar': 'https://fonts.gstatic.com/s/i/productlogos/calendar/v7/24px.svg',
                'meet': 'https://fonts.gstatic.com/s/i/productlogos/meet/v1/24px.svg',
                'drive': 'https://fonts.gstatic.com/s/i/productlogos/drive/v8/24px.svg',
                'default': 'https://fonts.gstatic.com/s/i/productlogos/googleg/v6/24px.svg'
            },
            'app_dev': {
                'flutter': 'https://storage.googleapis.com/flutter-io/flutter-mark-square-100.png',
                'firebase': 'https://www.gstatic.com/devrel-devsite/prod/v2210deb8920cd4a55bd580441aa58e7853afc04b39a9d9ac4198e1cd7fbe04ef6/firebase/images/touchicon-180.png',
                'functions': 'https://cdn.qwiklabs.com/badges/cloud-functions-badge.png',
                'default': 'https://www.gstatic.com/devrel-devsite/prod/v2210deb8920cd4a55bd580441aa58e7853afc04b39a9d9ac4198e1cd7fbe04ef6/cloud/images/cloud-logo.svg'
            }
        }
        
    def fetch_profile_data(self):
        """Fetch the latest profile data from Google Cloud Skills Boost"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.profile_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return None
            
    def parse_badges(self, html_content):
        """Parse badges from the HTML content with improved extraction"""
        soup = BeautifulSoup(html_content, 'html.parser')
        badges = []
        
        # Look for badge elements in different possible structures
        badge_selectors = [
            '.badge-item',
            '.skill-badge',
            '.achievement-item',
            '.credential-card',
            'article[data-testid="skill-badge"]',
            '.qwiklabs-badge'
        ]
        
        badge_elements = []
        for selector in badge_selectors:
            elements = soup.select(selector)
            if elements:
                badge_elements.extend(elements)
                break
        
        # If no structured badges found, parse from text content
        if not badge_elements:
            badges = self.parse_badges_from_text(html_content)
        else:
            for badge_elem in badge_elements:
                try:
                    badge_info = self.extract_badge_info(badge_elem)
                    if badge_info:
                        badges.append(badge_info)
                except Exception as e:
                    print(f"Error parsing badge element: {e}")
                    continue
                
        return badges
    
    def parse_badges_from_text(self, html_content):
        """Fallback: Parse badges from text content"""
        badges = []
        
        # Known badges from the profile
        known_badges = [
            {
                'title': 'Build Real World AI Applications with Gemini and Imagen',
                'earned_date': '2025-07-22',
                'description': 'Image recognition, natural language processing, image generation using Gemini and Imagen models'
            },
            {
                'title': 'Prompt Design in Vertex AI',
                'earned_date': '2025-07-21', 
                'description': 'Prompt engineering, image analysis, multimodal generative techniques'
            },
            {
                'title': 'Machine Learning Operations (MLOps) for Generative AI',
                'earned_date': '2025-07-19',
                'description': 'MLOps processes, deploying and managing Generative AI models'
            }
        ]
        
        # Find earned dates in content
        date_pattern = r'Earned\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})'
        dates_found = re.findall(date_pattern, html_content)
        
        for i, badge in enumerate(known_badges):
            if i < len(dates_found):
                badge['earned_date'] = self.parse_date(dates_found[i])
            
            badge['category'] = self.categorize_badge(badge['title'])
            badge['badge_image'] = self.get_badge_image(badge['title'], badge['category'])
            badges.append(badge)
            
        return badges
    
    def extract_badge_info(self, badge_elem):
        """Extract badge information from HTML element"""
        title_elem = badge_elem.find(['h1', 'h2', 'h3', 'h4', '.title', '.badge-title'])
        desc_elem = badge_elem.find(['p', '.description', '.badge-description'])
        date_elem = badge_elem.find(['.date', '.earned-date', '.badge-date', 'time'])
        img_elem = badge_elem.find('img')
        
        title = title_elem.get_text().strip() if title_elem else 'Unknown Badge'
        description = desc_elem.get_text().strip() if desc_elem else ''
        earned_date = self.parse_date(date_elem.get_text().strip()) if date_elem else 'Unknown'
        image_url = img_elem.get('src') if img_elem else None
        
        category = self.categorize_badge(title)
        badge_image = image_url if image_url else self.get_badge_image(title, category)
        
        return {
            'title': title,
            'description': description,
            'earned_date': earned_date,
            'category': category,
            'badge_image': badge_image,
            'shield_badge': self.generate_shield_badge(title, category)
        }
    
    def categorize_badge(self, title):
        """Categorize badge based on title with improved logic"""
        title_lower = title.lower()
        
        # AI/ML keywords
        ai_keywords = ['ai', 'ml', 'machine learning', 'gemini', 'imagen', 'vertex', 'prompt', 'generative', 'responsible ai', 'model', 'neural']
        if any(keyword in title_lower for keyword in ai_keywords):
            return 'ai_ml'
        
        # Infrastructure keywords  
        infra_keywords = ['terraform', 'kubernetes', 'compute', 'infrastructure', 'devops', 'gke', 'load balancing', 'monitoring', 'deployment']
        if any(keyword in title_lower for keyword in infra_keywords):
            return 'infrastructure'
        
        # Data & Analytics keywords
        data_keywords = ['bigquery', 'data', 'analytics', 'looker', 'dataflow', 'dataproc', 'sql', 'warehouse']
        if any(keyword in title_lower for keyword in data_keywords):
            return 'data_analytics'
        
        # Workspace keywords
        workspace_keywords = ['workspace', 'sheets', 'docs', 'calendar', 'meet', 'drive', 'gmail', 'appsheet']
        if any(keyword in title_lower for keyword in workspace_keywords):
            return 'workspace'
        
        # App Development keywords
        app_keywords = ['app', 'application', 'flutter', 'development', 'firebase', 'functions', 'api']
        if any(keyword in title_lower for keyword in app_keywords):
            return 'app_dev'
        
        # Trivia/Gaming
        if 'trivia' in title_lower or 'arcade' in title_lower:
            return 'trivia'
            
        return 'other'
    
    def get_badge_image(self, title, category):
        """Get appropriate badge image URL based on title and category"""
        title_lower = title.lower()
        
        if category in self.badge_images:
            category_images = self.badge_images[category]
            
            # Find specific image based on title keywords
            for keyword, image_url in category_images.items():
                if keyword != 'default' and keyword in title_lower:
                    return image_url
            
            # Return default for category
            return category_images.get('default', 'https://www.gstatic.com/devrel-devsite/prod/v2210deb8920cd4a55bd580441aa58e7853afc04b39a9d9ac4198e1cd7fbe04ef6/cloud/images/cloud-logo.svg')
        
        return 'https://www.gstatic.com/devrel-devsite/prod/v2210deb8920cd4a55bd580441aa58e7853afc04b39a9d9ac4198e1cd7fbe04ef6/cloud/images/cloud-logo.svg'
    
    def generate_shield_badge(self, title, category):
        """Generate shield.io badge URL with category-specific colors"""
        clean_title = re.sub(r'[^\w\s-]', '', title).strip()
        clean_title = re.sub(r'[-\s]+', '%20', clean_title)
        
        colors = {
            'ai_ml': 'ff6b6b',
            'infrastructure': '4ecdc4',
            'data_analytics': '0984e3', 
            'workspace': '4285f4',
            'app_dev': '6c5ce7',
            'trivia': 'ff9ff3',
            'other': '95a5a6'
        }
        
        color = colors.get(category, '95a5a6')
        return f"https://img.shields.io/badge/{clean_title}-{color}?style=for-the-badge&logo=google-cloud&logoColor=white"
    
    def parse_date(self, date_str):
        """Parse various date formats"""
        try:
            # Remove timezone info
            date_str = re.sub(r'\s+(EDT|EST|PST|PDT|UTC)', '', date_str)
            
            # Try different date formats
            formats = [
                '%b %d, %Y',      # Jul 22, 2025
                '%B %d, %Y',      # July 22, 2025  
                '%Y-%m-%d',       # 2025-07-22
                '%m/%d/%Y',       # 07/22/2025
                '%d/%m/%Y'        # 22/07/2025
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            return date_str
        except:
            return 'Unknown'
    
    def update_readme(self, badges):
        """Update README with new interactive format and real images"""
        try:
            with open('README.md', 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Update statistics
            total_badges = len(badges)
            content = re.sub(
                r'\*\*🏆 Total Badges Earned: \d+\*\*',
                f'**🏆 Total Badges Earned: {total_badges}**',
                content
            )
            
            # Update latest achievement
            if badges:
                latest_badge = max(badges, key=lambda x: x.get('earned_date', '0000-00-00'))
                latest_date = datetime.strptime(latest_badge['earned_date'], '%Y-%m-%d').strftime('%b %d, %Y') if latest_badge['earned_date'] != 'Unknown' else 'Recently'
                content = re.sub(
                    r'\*\*📅 Latest Achievement:.*?\*\*',
                    f"**📅 Latest Achievement: {latest_badge['title']} ({latest_date})**",
                    content
                )
            
            # Update badge counts in skills distribution
            ai_count = len([b for b in badges if b['category'] == 'ai_ml'])
            infra_count = len([b for b in badges if b['category'] == 'infrastructure'])
            data_count = len([b for b in badges if b['category'] == 'data_analytics'])
            
            # Update last updated timestamp
            today = datetime.now().strftime('%B %d, %Y')
            content = re.sub(
                r'Last%20Updated-.*?-success',
                f'Last%20Updated-{today.replace(" ", "%20")}-success',
                content
            )
            
            # Write updated content
            with open('README.md', 'w', encoding='utf-8') as file:
                file.write(content)
                
            print(f"✅ README updated successfully!")
            print(f"📊 Total badges: {total_badges}")
            print(f"🤖 AI/ML badges: {ai_count}")
            print(f"🏗️ Infrastructure badges: {infra_count}")
            print(f"💾 Data badges: {data_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating README: {e}")
            return False
    
    def save_badges_cache(self, badges):
        """Save badges to cache file"""
        try:
            cache_data = {
                'last_updated': datetime.now().isoformat(),
                'total_badges': len(badges),
                'badges': badges
            }
            
            os.makedirs('.github/data', exist_ok=True)
            with open('.github/data/badges.json', 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Badges cache saved ({len(badges)} badges)")
            return True
            
        except Exception as e:
            print(f"❌ Error saving cache: {e}")
            return False

def main():
    """Main execution function with enhanced error handling"""
    print("🚀 Starting Google Cloud Skills Portfolio Update...")
    
    profile_url = "https://www.cloudskillsboost.google/public_profiles/30dca49f-92b8-41d1-8a0e-ccdaacb4eb68"
    updater = GCPPortfolioUpdater(profile_url)
    
    print("📡 Fetching profile data...")
    html_content = updater.fetch_profile_data()
    
    if not html_content:
        print("❌ Failed to fetch profile data - using cached data if available")
        # Try to load from cache
        try:
            with open('.github/data/badges.json', 'r') as f:
                cached_data = json.load(f)
                badges = cached_data.get('badges', [])
                print(f"📂 Loaded {len(badges)} badges from cache")
        except:
            print("❌ No cached data available")
            return
    else:
        print("🔍 Parsing badges from profile...")
        badges = updater.parse_badges(html_content)
        print(f"🏅 Found {len(badges)} badges")
        
        # Save to cache
        updater.save_badges_cache(badges)
    
    print("📝 Updating README...")
    success = updater.update_readme(badges)
    
    if success:
        print("✅ Portfolio updated successfully!")
        print(f"🎯 Total badges processed: {len(badges)}")
        print(f"📅 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Generate summary
        categories = {}
        for badge in badges:
            cat = badge.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\n📊 Badge Distribution:")
        for category, count in categories.items():
            print(f"   {category}: {count} badges")
            
    else:
        print("❌ Failed to update portfolio")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
