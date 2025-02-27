from flask import Flask, render_template, jsonify, request
import pandas as pd
import re
import os
from nltk.corpus import stopwords
from tqdm import tqdm
import nltk
import zipfile
import requests
import spacy

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')

app = Flask(__name__)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# API Configurations
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
HF_API_TOKEN = os.getenv('HF_API_TOKEN')

# Load dataset
with zipfile.ZipFile("News dataset.zip", "r") as z:
    with z.open("News.csv") as f:
        news_data = pd.read_csv(f, encoding="latin1", index_col=0)

news_data = news_data.drop(["title", "subject", "date"], axis=1)
news_data = news_data.sample(frac=1).reset_index(drop=True)

def preprocess_text(text_data):
    preprocessed_text = []
    stop_words = set(stopwords.words('english'))
    
    for sentence in tqdm(text_data):
        sentence = re.sub(r'[^\w\s]', '', str(sentence))
        preprocessed_text.append(' '.join(token.lower() 
                                  for token in nltk.word_tokenize(sentence)
                                  if token.lower() not in stop_words))
    return preprocessed_text

news_data['processed_text'] = preprocess_text(news_data['text'].values)

def google_search(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': query,
        'num': 5
    }
    response = requests.get(url, params=params)
    return response.json()

def analyze_with_hf(claim, snippets):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    
    payload = {
        "inputs": f"Claim: {claim} \n Context: {snippets}",
        "parameters": {"candidate_labels": ["true", "false", "unverified"]}
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_random_article')
def get_random_article():
    random_article = news_data.sample(1).iloc[0]
    return jsonify({
        'text': random_article['text'],
        'actual_class': 'Real' if random_article['class'] == 1 else 'Fake',
        'index': int(random_article.name)
    })

@app.route('/check_guess', methods=['POST'])
def check_guess():
    user_input = request.get_json()
    actual_class = 'Real' if news_data.loc[user_input['index'], 'class'] == 1 else 'Fake'
    return jsonify({
        'correct': user_input['guess'] == actual_class,
        'actual_class': actual_class
    })

@app.route('/verify_article', methods=['POST'])
def verify_article():
    data = request.get_json()
    user_text = data['text']
    
    try:
        doc = nlp(user_text)
        keywords = [ent.text for ent in doc.ents][:5]
        search_query = " ".join(keywords)
        
        search_results = google_search(search_query)
        snippets = " ".join([item.get('snippet', '') for item in search_results.get('items', [])[:3]])
        
        analysis = analyze_with_hf(user_text, snippets)
        verdict = analysis.get('labels', ['unverified'])[0]
        
        return jsonify({
            'verdict': verdict.capitalize(),
            'sources': [item['link'] for item in search_results.get('items', [])[:3]]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)