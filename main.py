import os
import sys
import google.generativeai as genai
import gspread
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
# 2. Google Custom Search API: Search for Images
# ----------------------------

API_KEY = os.getenv("GOOGLE_API_KEY")  # Add your Google API key here
CSE_ID = os.getenv("GOOGLE_CSE_ID")    # Add your Custom Search Engine ID here

# Function to search for images related to the topic
def search_images(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={CSE_ID}&searchType=image&key={API_KEY}"
    response = requests.get(url)
    results = response.json()
    image_urls = []
    if "items" in results:
        for item in results["items"]:
            image_urls.append(item["link"])  # URL of each image found
    return image_urls

# Search for images related to the topic
image_urls = search_images(TOPIC)

# Get the first image URL (you can add logic to select one)
image_url = image_urls[0] if image_urls else ""

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
