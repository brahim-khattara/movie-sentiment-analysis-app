from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Get the IMDB file path from the environment variable
file_path = os.getenv('IMDB_FILE_PATH')

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Preprocess and train the model
def preprocess_and_train(file_path):
    # Load dataset
    df = pd.read_csv(file_path).head(500)
    
    # TF-IDF feature extraction
    tfidf = TfidfVectorizer(max_features=10000, stop_words='english', ngram_range=(1, 2))
    X = tfidf.fit_transform(df["review"]).toarray()
    y = df["sentiment"].map({"positive": 1, "negative": 0})
    
    # Split dataset into training and testing sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Apply PCA on the training set
    pca = PCA(n_components=50)
    X_train_reduced = pca.fit_transform(X_train)

    # Transform the test set using the PCA model
    X_test_reduced = pca.transform(X_test)

    # Train KNN classifier
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(X_train_reduced, y_train)

    return tfidf, pca, knn, X_test_reduced, y_test

# Load the model components
tfidf, pca, knn, X_test_reduced, y_test = preprocess_and_train(file_path)

@app.route('/classify', methods=['POST'])
def classify():
    data = request.json
    phrase = data.get('phrase', '')
    if not phrase:
        return jsonify({"error": "No phrase provided"}), 400

    # Process the input phrase
    X_phrase = tfidf.transform([phrase]).toarray()
    X_phrase_reduced = pca.transform(X_phrase)
    
    # Get the prediction from KNN
    prediction = knn.predict(X_phrase_reduced)
    sentiment = "Positive" if prediction[0] == 1 else "Negative"
    
    return jsonify({"sentiment": sentiment})

@app.route('/')
def home():
    return "Hello, Render!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')  # Make the app accessible on the local network
