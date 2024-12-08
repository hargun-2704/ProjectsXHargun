import os
import googleapiclient.discovery
from textblob import TextBlob
from flask import Flask, request, render_template, jsonify
import matplotlib.pyplot as plt
import io
import base64
import webbrowser
import threading
from werkzeug.serving import is_running_from_reloader

app = Flask(__name__)

def get_youtube_comments(video_id, api_key):
    try:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        
        api_service_name = "youtube"
        api_version = "v3"
        youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)

        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100
        )
        response = request.execute()
        
        comments = []
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textOriginal']
            comments.append(comment)
        
        return comments
    except Exception as e:
        return []

def analyze_sentiment(comments):
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}

    for comment in comments:
        try:
            analysis = TextBlob(comment)
            if analysis.sentiment.polarity > 0:
                sentiments['positive'] += 1
            elif analysis.sentiment.polarity == 0:
                sentiments['neutral'] += 1
            else:
                sentiments['negative'] += 1
        except Exception as e:
            continue
    
    return sentiments

def plot_sentiments(sentiments):
    labels = list(sentiments.keys())
    sizes = list(sentiments.values())
    colors = ['#66b3ff', '#99ff99', '#ff6666'] 

    plt.figure(figsize=(8, 8))  
    wedges, texts, autotexts = plt.pie(
        sizes, 
        labels=labels, 
        colors=colors, 
        explode=(0.1, 0, 0),  
        autopct='%1.1f%%', 
        startangle=140,  
        wedgeprops=dict(width=0.3)  
    )

    
    for text in texts:
        text.set_fontsize(14)  
        text.set_color('black')  
    for autotext in autotexts:
        autotext.set_fontsize(14)  
        autotext.set_color('black')  
        autotext.set_weight('bold')  

    plt.legend(wedges, labels, title="Sentiments", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    plt.title('Sentiment Analysis of YouTube Comments', fontsize=16, weight='bold')
    plt.axis('equal')  

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')  
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return plot_url


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    api_key = request.form['api_key']
    video_id = request.form['video_id']
    comments = get_youtube_comments(video_id, api_key)
    sentiments = analyze_sentiment(comments)
    plot_url = plot_sentiments(sentiments)
    
    # Combine comments with their sentiment scores
    analyzed_comments = []
    for comment in comments:
        analysis = TextBlob(comment)
        polarity = analysis.sentiment.polarity
        if polarity > 0:
            sentiment = 'positive'
        elif polarity == 0:
            sentiment = 'neutral'
        else:
            sentiment = 'negative'
        analyzed_comments.append({'comment': comment, 'sentiment': sentiment})

    return jsonify({'plot_url': plot_url, 'analyzed_comments': analyzed_comments})

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    if not is_running_from_reloader():
        threading.Timer(1, open_browser).start()
    app.run(debug=True)