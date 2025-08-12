import os
import requests
import google.generativeai as genai
from flask import Flask, render_template, request
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 初始化 Flask 應用程式
app = Flask(__name__)

# 從環境變數中獲取 API 金鑰
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CUSTOM_SEARCH_ENGINE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

# 設定 Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

# 使用最新的模型名稱
model = genai.GenerativeModel('gemini-1.5-flash-latest') 
# 或者 'gemini-1.5-flash-latest'，後者速度更快、費用更低，適合快速原型開發

def get_gemini_outline(topic):
    """使用 Gemini 生成學習大綱"""
    prompt = f"為這個主題：'{topic}'，生成一個簡潔有條理的學習大綱，並使用 markdown 格式呈現。大綱需包含主要概念和幾個重點。"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API 呼叫失敗: {e}")
        return "無法生成學習大綱，請稍後再試。"

def get_youtube_videos(topic):
    """使用 YouTube Data API 搜尋影片"""
    videos = []
    youtube_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': topic,
        'key': YOUTUBE_API_KEY,
        'maxResults': 5,
        'type': 'video'
    }
    try:
        response = requests.get(youtube_url, params=params)
        response.raise_for_status() # 檢查 HTTP 請求是否成功
        data = response.json()
        for item in data['items']:
            video = {
                'title': item['snippet']['title'],
                'video_id': item['id']['videoId'],
                'thumbnail': item['snippet']['thumbnails']['high']['url']
            }
            videos.append(video)
    except requests.exceptions.RequestException as e:
        print(f"YouTube API 呼叫失敗: {e}")
    return videos

def get_custom_search_results(topic):
    """使用 Google Custom Search API 搜尋文章"""
    articles = []
    cse_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': CUSTOM_SEARCH_ENGINE_ID,
        'q': topic,
        'num': 5
    }
    try:
        response = requests.get(cse_url, params=params)
        response.raise_for_status()
        data = response.json()
        for item in data.get('items', []):
            article = {
                'title': item.get('title'),
                'link': item.get('link'),
                'snippet': item.get('snippet')
            }
            articles.append(article)
    except requests.exceptions.RequestException as e:
        print(f"Custom Search API 呼叫失敗: {e}")
    return articles

@app.route("/", methods=["GET", "POST"])
def index():
    """主頁面和結果顯示"""
    if request.method == "POST":
        topic = request.form.get("topic")
        if topic:
            # 並行執行以提升效能會更好，但為了簡化範例先依序執行
            gemini_outline = get_gemini_outline(topic)
            youtube_videos = get_youtube_videos(topic)
            search_results = get_custom_search_results(topic)
            
            return render_template(
                "index.html",
                topic=topic,
                outline=gemini_outline,
                videos=youtube_videos,
                articles=search_results
            )
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)