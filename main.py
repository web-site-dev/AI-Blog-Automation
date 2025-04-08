import os
import sys
import json
import requests
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials

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
# 2. Unsplash: Get Image Related to Topic
# ----------------------------
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
image_url = "https://via.placeholder.com/300x200?text=No+Image"

try:
    res = requests.get(
        "https://api.unsplash.com/search/photos",
        params={"query": TOPIC, "per_page": 1},
        headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    )
    data = res.json()
    if "results" in data and len(data["results"]) > 0:
        image_url = data["results"][0]["urls"]["regular"]
    else:
        print("No image found from Unsplash.")
except Exception as e:
    print("Error getting image from Unsplash:", str(e))

# ----------------------------
# 3. Blogger: Publish Post
# ----------------------------
published_url = ""
blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{os.getenv('BLOG_ID')}/posts"

blog_data = {
    "title": TOPIC,
    "content": f"<p>{content}</p><br><img src='{image_url}'/>",
    "labels": ["AI Generated", TOPIC.split()[0]],
}

try:
    blog_response = requests.post(
        blog_url,
        headers={
            "Authorization": f"Bearer {os.getenv('BLOGGER_TOKEN')}",
            "Content-Type": "application/json"
        },
        json=blog_data
    )
    print("Blogger status:", blog_response.status_code)
    print("Blogger response:", blog_response.text)
    blog_response.raise_for_status()
    published_url = blog_response.json().get("url", "")
except Exception as e:
    print("❌ Error publishing to Blogger!")
    print("Exception:", str(e))

# ----------------------------
# 4. Update Google Sheet
# ----------------------------
try:
    creds = Credentials.from_service_account_file("google-creds.json")
    gc = gspread.authorize(creds)
    sheet = gc.open_by_url(os.getenv("SHEET_URL")).worksheet("AI Blog Scheduler")

    sheet.update(f'B{ROW}', "PUBLISHED")
    sheet.update(f'C{ROW}', content)
    sheet.update(f'D{ROW}', image_url)
    sheet.update(f'E{ROW}', published_url)
except Exception as e:
    print("Error updating Google Sheet:", str(e))
