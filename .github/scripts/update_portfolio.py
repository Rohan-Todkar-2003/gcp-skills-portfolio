#!/usr/bin/env python3
"""
Google Cloud Skills Boost Portfolio Updater
Automatically fetches latest badges and updates README.md
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os

class GCPPortfolioUpdater:
    def __init__(self, profile_url):
        self.profile_url = profile_url
        self.badges_data = []
        
    def fetch_profile_data(self):
        """Fetch the latest profile data from Google Cloud Skills Boost"""
        try:
            response = requests.get(self.profile_url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return None
            
    def parse_badges(self, html_content):
        """Parse badges from the HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        badges = []
        
        # Find all badge elements (adjust selectors based on actual HTML structure)
        badge_elements = soup.find_all('div', class_='badge-item')  # Update selector as needed
        
        for badge_elem in badge_elements:
            try:
                # Extract badge information
                title = badge_elem.find('h3', class_='badge-title')
                description = badge_elem.find('p', class_='badge-description')
                date = badge_elem.find('span', class_='badge-date')
                category = self.categorize_badge(title.text if title else "")
                
                badge_info = {
                    'title': title.text.strip() if title else 'Unknown Badge',
                    'description': description.text.strip() if description else '',
                    'earned_date': self.parse_date(date.text if date else ''),
                    'category': category,
                    'badge_url': self.generate_badge_url(title.text if title else '')
                }
                badges.append(badge_info)
                
            except Exception as e:
                print(f"Error parsing badge: {e}")
                continue
                
        return badges
    
    def categorize_badge(self, title):
        """Categorize badge based on title"""
        title_lower = title.lower()
        
        if any(term in title_lower for term in ['ai', 'ml', 'machine learning', 'gemini', 'imagen', 'vertex', 'prompt']):
            return 'ai_ml'
        elif any(term in title_lower for term in ['terraform', 'kubernetes', 'compute', 'infrastructure', 'devops']):
            return 'infrastructure'
        elif any(term in title_lower for term in ['bigquery', 'data', 'analytics', 'looker']):
            return 'data_analytics'
        elif any(term in title_lower for term in ['workspace', 'sheets', 'docs', 'calendar', 'meet']):
            return 'workspace'
        elif any(term in title_lower for term in ['app', 'application', 'flutter', 'development']):
            return 'app_dev'
        elif 'trivia' in title_lower:
            return 'trivia'
        else:
            return 'other'
    
    def parse_date(self, date_str):
        """Parse date string to standard format"""
        try:
            # Handle different date formats
            if 'EDT' in date_str:
                date_str = date_str.replace(' EDT', '')
                return datetime.strptime(date_str, '%b %d, %Y').strftime('%Y-%m-%d')
            return date_str
        except:
            return 'Unknown'
    
    def generate_badge_url(self, title):
        """Generate shield.io badge URL"""
        # Clean title for URL
        clean_title = re.sub(r'[^\w\s-]', '', title).strip()
        clean_title = re.sub(r'[-\s]+', '%20', clean_title)
        
        colors = {
            'ai_ml': 'ff6b6b',
            'infrastructure': '4ecdc4', 
            'data_analytics': '45b7d1',
            'workspace': '4285f4',
            'app_dev': '6c5ce7',
            'trivia': 'ff9ff3',
            'other': '95a5a6'
        }
        
        category = self.categorize_badge(title)
        color = colors.get(category, '95a5a6')
        
        return f"https://img.shields.io/badge/{clean_title}-{color}?style=flat-square&logo=google-cloud"
    
    def update_readme(self, badges):
        """Update the README.md file with new badges"""
        try:
            with open('README.md', 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Update total badges count
            total_badges = len(badges)
            content = re.sub(
                r'\*\*🏆 Total Badges Earned: \d+\*\*',
                f'**🏆 Total Badges Earned: {total_badges}**',
                content
            )
            
            # Update latest achievement
            if badges:
                latest_badge = max(badges, key=lambda x: x['earned_date'])
                content = re.sub(
                    r'\*\*📅 Latest Achievement: .*?\*\*',
                    f"**📅 Latest Achievement: {latest_badge['title']} ({latest_badge['earned_date']})**",
                    content
                )
            
            # Update last updated date
            today = datetime.now().strftime('%B %d, %Y')
            content = re.sub(
                r'\*\*Last Updated:\*\* .*',
                f'**Last Updated:** {today}',
                content
            )
            
            # Write updated content
            with open('README.md', 'w', encoding='utf-8') as file:
                file.write(content)
                
            print(f"README updated with {len(badges)} badges")
            return True
            
        except Exception as e:
            print(f"Error updating README: {e}")
            return False

    def generate_new_badge_table(self, badges, category):
        """Generate table rows for specific category"""
        category_badges = [badge for badge in badges if badge['category'] == category]
        
        table_rows = []
        for badge in category_badges:
            row = f"| ![{badge['title']}]({badge['badge_url']}) | {badge['title']} | {badge['earned_date']} | {badge['description'][:100]}{'...' if len(badge['description']) > 100 else ''} |"
            table_rows.append(row)
        
        return '\n'.join(table_rows)

def main():
    """Main execution function"""
    profile_url = "https://www.cloudskillsboost.google/public_profiles/30dca49f-92b8-41d1-8a0e-ccdaacb4eb68"
    
    updater = GCPPortfolioUpdater(profile_url)
    
    print("Fetching profile data...")
    html_content = updater.fetch_profile_data()
    
    if not html_content:
        print("Failed to fetch profile data")
        return
    
    print("Parsing badges...")
    badges = updater.parse_badges(html_content)
    
    print(f"Found {len(badges)} badges")
    
    print("Updating README...")
    success = updater.update_readme(badges)
    
    if success:
        print("✅ Portfolio updated successfully!")
        
        # Save badges data for future reference
        with open('.github/data/badges.json', 'w') as f:
            json.dump(badges, f, indent=2)
    else:
        print("❌ Failed to update portfolio")

if __name__ == "__main__":
    main()
