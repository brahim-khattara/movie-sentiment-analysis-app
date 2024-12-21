from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


# Preprocess and train the model
def preprocess_and_train(file_path):
    df = pd.read_csv(file_path).head(10000)
    tfidf = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2))
    X = tfidf.fit_transform(df["review"]).toarray()
    y = df["sentiment"].map({"positive": 1, "negative": 0})
    pca = PCA(n_components=50)
    X_reduced = pca.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X_reduced, y, test_size=0.2, random_state=42)
    svm = SVC(C=1, kernel='linear', random_state=42)
    svm.fit(X_train, y_train)
    return tfidf, pca, svm

# Load the model components
file_path = "data/IMDB Dataset.csv"
tfidf, pca, svm = preprocess_and_train(file_path)


@app.route('/classify', methods=['POST'])
def classify():
    data = request.json
    phrase = data.get('phrase', '')
    if not phrase:
        return jsonify({"error": "No phrase provided"}), 400

    X_phrase = tfidf.transform([phrase]).toarray()
    X_phrase_reduced = pca.transform(X_phrase)
    decision = svm.decision_function(X_phrase_reduced)  # Get decision score
    prediction = svm.predict(X_phrase_reduced)

    # Calculate confidence percentages
    confidence_positive = 1 / (1 + np.exp(-decision[0])) * 100
    confidence_negative = 100 - confidence_positive

    sentiment = "Positive" if prediction[0] == 1 else "Negative"
    return jsonify({
        "sentiment": sentiment,
        "confidence_positive": confidence_positive,
        "confidence_negative": confidence_negative
    })


@app.route('/')
def home():
    return "Hello, Render!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')  # Make the app accessible on the local network

