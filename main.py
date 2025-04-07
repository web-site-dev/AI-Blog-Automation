import os
import sys
import google.generativeai as genai
import replicate
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

# Get topic and row from command-line arguments
TOPIC = sys.argv[1]
ROW = int(sys.argv[2])

# ========== 1. Configure Gemini ==========
genai.configure(api_key=os.getenv("GEMINI_KEY"))

# Use the correct model name
model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

# Generate blog content
response = model.generate_content(f"Write a 700-word blog post about {TOPIC}")
content = response.text.strip()

# ========== 2. Generate Image with Replicate ==========
image_url = replicate.run(
    "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    input={
        "prompt": f"High-quality illustration of: {TOPIC}",
        "negative_prompt": "text, watermark"
    }
)[0]

# ========== 3. Publish to Blogger ==========
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

# ========== 4. Update Google Sheet ==========
gc = gspread.service_account(filename="google-creds.json")
sheet = gc.open_by_url(os.getenv("SHEET_URL")).worksheet("AI Blog Scheduler")

# Update the row
sheet.update(f'B{ROW}', "PUBLISHED")
sheet.update(f'C{ROW}', content)
sheet.update(f'D{ROW}', image_url)
sheet.update(f'E{ROW}', published_url)
