import os
import sys
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

# ----------------------------
# Arguments from GitHub Action
# ----------------------------
TOPIC = sys.argv[1]
ROW = int(sys.argv[2])

# ----------------------------
# 1. Gemini: Generate Blog Content
# ----------------------------
genai.configure(api_key=os.getenv("GEMINI_KEY"))

model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

response = model.generate_content(f"Write a 700-word engaging blog post about {TOPIC}")
content = response.text.strip()

# ----------------------------
# 2. Google Custom Search: Search for Image
# ----------------------------
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

search_url = f"https://www.googleapis.com/customsearch/v1?q={TOPIC}&key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&searchType=image"

# Make the request to Google Custom Search API
search_response = requests.get(search_url)
search_results = search_response.json()

# Get the URL of the first image result
image_url = search_results["items"][0]["link"]

# ----------------------------
# 3. Blogger: Publish Post
# ----------------------------
blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{os.getenv('BLOG_ID')}/posts"

blog_response = requests.post(
    blog_url,
    headers={
        "Authorization": f"Bearer {os.getenv('BLOGGER_TOKEN')}",
        "Content-Type": "application/json"
    },
    json={
        "title": TOPIC,
        "content": f"<p>{content}</p><br><img src='{image_url}'>",
        "labels": ["AI Generated", TOPIC.split()[0]]
    }
)

published_url = blog_response.json().get("url", "")

# ----------------------------
# 4. Update Google Sheet
# ----------------------------
gc = gspread.service_account(filename="google-creds.json")
sheet = gc.open_by_url(os.getenv("SHEET_URL")).worksheet("AI Blog Scheduler")

# Write results to the row
sheet.update(f'B{ROW}', "PUBLISHED")
sheet.update(f'C{ROW}', content)
sheet.update(f'D{ROW}', image_url)
sheet.update(f'E{ROW}', published_url)
