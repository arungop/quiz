from xml.etree import ElementTree as ET
import requests
import os
from datetime import datetime
import re
from html import unescape

def clean_html(raw_html):
    """Remove HTML tags and decode HTML entities."""
    # Remove HTML tags
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    # Decode HTML entities
    return unescape(cleantext).strip()

def get_week_year():
    """Get current week number and year."""
    current_date = datetime.now()
    week_number = current_date.isocalendar()[1]
    year = current_date.year
    return week_number, year

def create_folder_structure(year):
    """Create folder structure for the year if it doesn't exist."""
    base_folder = "data"
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
        
    year_folder = os.path.join(base_folder, str(year))
    if not os.path.exists(year_folder):
        os.makedirs(year_folder)
    return year_folder

def get_txt_filename(week_number, year, folder_path):
    """Generate TXT filename with week number and year."""
    return os.path.join(folder_path, f"week_{week_number}_{year}.txt")

def get_existing_urls(txt_file):
    """Get list of URLs that are already in the TXT to avoid duplicates."""
    if not os.path.exists(txt_file):
        return set()
    
    existing_urls = set()
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n\n'):  # Split by double newline to separate entries
                if 'Link:' in line:
                    url = line.split('Link:')[1].strip()
                    existing_urls.add(url)
    except FileNotFoundError:
        pass
    
    return existing_urls

def parse_rss_feed(url, txt_file):
    """Parse RSS feed and append new entries to TXT file."""
    try:
        # Register the content:encoded namespace
        ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
        
        # Fetch the RSS feed
        response = requests.get(url)
        response.raise_for_status()
        
        # Clean the content
        content = response.content.decode('utf-8-sig').strip()
        
        # Parse the cleaned XML content
        tree = ET.fromstring(content)
        
        # Get existing URLs to avoid duplicates
        existing_urls = get_existing_urls(txt_file)
        
        # Prepare data for TXT
        new_articles = []
        for item in tree.findall('.//item'):
            link = item.find('link').text.strip() if item.find('link') is not None else 'No link'
            
            # Skip if article already exists
            if link in existing_urls:
                continue
            
            # Get both description and content:encoded
            description = item.find('description')
            content_encoded = item.find('.//{http://purl.org/rss/1.0/modules/content/}encoded')
            
            # Clean and combine content
            description_text = clean_html(description.text) if description is not None else ''
            content_text = clean_html(content_encoded.text) if content_encoded is not None else ''
            
            # Use the longer content between description and content:encoded
            final_content = content_text if len(content_text) > len(description_text) else description_text
                
            article = {
                'title': clean_html(item.find('title').text.strip()) if item.find('title') is not None else 'No title',
                'pubDate': item.find('pubDate').text.strip() if item.find('pubDate') is not None else 'No date',
                'content': final_content,
                'link': link,
                'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            new_articles.append(article)
            
            # Print for logging
            print(f"\nAdded Article: {article['title']}")
        
        if new_articles:
            # Append to TXT
            with open(txt_file, 'a', encoding='utf-8') as f:
                for article in new_articles:
                    f.write(f"Title: {article['title']}\n")
                    f.write(f"Publication Date: {article['pubDate']}\n")
                    f.write(f"Content: {article['content']}\n")
                    f.write(f"Link: {article['link']}\n")
                    f.write(f"Fetch Time: {article['fetch_time']}\n")
                    f.write("\n")  # Add blank line between articles
            
            print(f"\nAdded {len(new_articles)} new articles to {txt_file}")
        else:
            print("\nNo new articles to add")
            
        return new_articles
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the RSS feed: {e}")
        return None
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        if 'content' in locals():
            print(f"First 200 characters of content: {content[:200]}")
        return None
    except UnicodeDecodeError as e:
        print(f"Error decoding content: {e}")
        return None

def main():
    # Get current week and year
    week_number, year = get_week_year()
    
    # Create folder structure
    folder_path = create_folder_structure(year)
    
    # Get TXT filename
    txt_file = get_txt_filename(week_number, year, folder_path)
    
    # RSS feed URL
    xml_url = "https://ddnews.gov.in/en/category/top-stories/feed/"
    
    # Parse feed and save to TXT
    articles = parse_rss_feed(xml_url, txt_file)
    
    if articles is not None:
        print(f"\nProcess completed successfully")
        print(f"TXT location: {txt_file}")

if __name__ == "__main__":
    main()