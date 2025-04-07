import os
import sys
import google.generativeai as genai
import replicate
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

TOPIC = sys.argv[1]
ROW = int(sys.argv[2])

# Gemini: Generate blog content
genai.configure(api_key=os.getenv("GEMINI_KEY"))
model = genai.GenerativeModel("gemini-pro")
response = model.generate_content(f"Write a 700-word blog post about {TOPIC}")
content = response.text

# Replicate: Generate image
image_url = replicate.run(
    "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    input={"prompt": f"High-quality illustration of: {TOPIC}", "negative_prompt": "text, watermark"}
)[0]

# Blogger: Publish
blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{os.getenv('BLOG_ID')}/posts"
blog_response = requests.post(
    blog_url,
    headers={"Authorization": f"Bearer {os.getenv('BLOGGER_TOKEN')}"},
    json={
        "title": TOPIC,
        "content": f"{content}<br><img src='{image_url}'>",
        "labels": ["AI Generated", TOPIC.split()[0]]
    }
)
published_url = blog_response.json().get("url", "")

# Google Sheets: Update
gc = gspread.service_account(filename="google-creds.json")
sheet = gc.open_by_url(os.getenv("SHEET_URL")).worksheet("AI Blog Scheduler")
sheet.update(f'B{ROW}', "PUBLISHED")
sheet.update(f'C{ROW}', content)
sheet.update(f'D{ROW}', image_url)
sheet.update(f'E{ROW}', published_url)
