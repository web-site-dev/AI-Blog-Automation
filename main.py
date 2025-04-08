import os
import sys
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import requests
import json

# ----------------------------
# 0. Arguments from GitHub Action
# ----------------------------
TOPIC = sys.argv[1]
ROW = int(sys.argv[2])

# ----------------------------
# 1. Gemini: Generate Blog Content
# ----------------------------
genai.configure(api_key=os.getenv("GEMINI_KEY"))

model = genai.GenerativeModel("models/gemini-1.5-pro-latest")

response = model.generate_content(f"Write a 700-word engaging blog post about {TOPIC}")
content = response.text.strip()

# ----------------------------
# 2. Google Custom Search: Search for Image
# ----------------------------
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

search_url = (
    f"https://www.googleapis.com/customsearch/v1"
    f"?q={TOPIC}&key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&searchType=image"
)

image_url = "https://via.placeholder.com/150"  # Default fallback

try:
    search_response = requests.get(search_url)
    search_results = search_response.json()
    print("Search API Response:", json.dumps(search_results, indent=2))

    if "items" in search_results and len(search_results["items"]) > 0:
        image_url = search_results["items"][0]["link"]

except Exception as e:
    print(f"Image search failed: {e}")

# ----------------------------
# 3. Blogger: Publish Post
# ----------------------------
blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{os.getenv('BLOG_ID')}/posts"

blog_data = {
    "title": TOPIC,
    "content": f"<p>{content}</p><br><img src='{image_url}'>",
    "labels": ["AI Generated", TOPIC.split()[0]],
}

published_url = ""

try:
    blog_response = requests.post(
        blog_url,
        headers={
            "Authorization": f"Bearer {os.getenv('BLOGGER_TOKEN')}",
            "Content-Type": "application/json"
        },
        json=blog_data
    )
    blog_response.raise_for_status()  # Raise if Blogger returns an error
    published_url = blog_response.json().get("url", "")
except Exception as e:
    print(f"Error publishing blog: {e}")

# ----------------------------
# 4. Update Google Sheet
# ----------------------------
try:
    creds = Credentials.from_service_account_file("google-creds.json")
    gc = gspread.authorize(creds)

    sheet = gc.open_by_url(os.getenv("SHEET_URL")).worksheet("AI Blog Scheduler")

    # Update the row
    sheet.update(f'B{ROW}', "PUBLISHED")
    sheet.update(f'C{ROW}', content)
    sheet.update(f'D{ROW}', image_url)
    sheet.update(f'E{ROW}', published_url)

except Exception as e:
    print(f"Error updating sheet: {e}")
