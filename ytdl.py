import os
import csv
import feedparser
import requests
import time
import random
from datetime import datetime

# User-configurable variables
channel_id = 'UCtLKtDt2t_STs8caAC1yg4Q'
rss_feed_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
output_path = 'downloads'
index_file = 'video-index.txt'
shorts_folder = os.path.join(output_path, 'shorts')
videos_folder = os.path.join(output_path, 'videos')

# Function to download a video given its URL
def download_video(video_url, output_path):
    try:
        response = requests.get(video_url)
        if response.status_code == 200:
            video_filename = os.path.join(output_path, f"{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4")
            with open(video_filename, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded video from {video_url}")
            return video_filename
        else:
            print(f"Failed to download video from {video_url}. Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error downloading video {video_url}: {e}")
        return None

# Function to load the index file
def load_index(index_file):
    if not os.path.exists(index_file):
        return []
    with open(index_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return list(reader)

# Function to save the index file
def save_index(index_file, index_data):
    if not index_data:
        return
    with open(index_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=index_data[0].keys())
        writer.writeheader()
        writer.writerows(index_data)

# Function to sanitize video title
def sanitize_title(title):
    # Remove emojis and special characters
    clean_title = ''.join(filter(lambda x: x.isalnum() or x.isspace(), title))
    # Remove hashtags
    clean_title = clean_title.split()
    clean_title = [word for word in clean_title if not word.startswith('#')]
    clean_title = ' '.join(clean_title)
    return clean_title.strip()

# Main script
def main():
    # Ensure output and subdirectories exist
    os.makedirs(shorts_folder, exist_ok=True)
    os.makedirs(videos_folder, exist_ok=True)

    # Load existing index data or initialize an empty list if the file doesn't exist
    index_data = load_index(index_file)
    if not index_data:
        with open(index_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['url', 'title', 'publish_date', 'status', 'last_checked', 'filename'])
            writer.writeheader()

    # Convert index data to a dictionary for quick lookup
    index_dict = {item['url']: item for item in index_data}

    # Fetch video entries from the RSS feed
    feed = feedparser.parse(rss_feed_url)

    for entry in feed.entries:
        video_url = entry.link
        print(f"Processing video: {video_url}")
        if video_url in index_dict:
            # Video already indexed
            if index_dict[video_url]['status'] == 'complete':
                continue
        else:
            # New video, add to index
            sanitized_title = sanitize_title(entry.title)
            index_dict[video_url] = {
                'url': video_url,
                'title': sanitized_title,
                'publish_date': entry.published,
                'status': 'pending',
                'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'filename': ''
            }
            print(f"Added new video to index: {sanitized_title}")

        # Determine if the video is a Short (less than 60 seconds)
        output_directory = shorts_folder if 'short' in sanitized_title.lower() else videos_folder

        # Download video
        video_filename = download_video(video_url, output_directory)
        if video_filename:
            index_dict[video_url]['status'] = 'complete'
            index_dict[video_url]['filename'] = video_filename
        else:
            index_dict[video_url]['status'] = 'failed'

        index_dict[video_url]['last_checked'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Add a delay between requests to avoid rate limiting
        time.sleep(random.uniform(1, 3))

    # Save updated index data
    save_index(index_file, list(index_dict.values()))

if __name__ == '__main__':
    main()
