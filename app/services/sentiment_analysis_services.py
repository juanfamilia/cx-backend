# app/services/sentiment_analysis_services.py

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def analyze_sentiment_text(text: str) -> dict:
    vader = SentimentIntensityAnalyzer()
    vader_scores = vader.polarity_scores(text)

    tb = TextBlob(text)
    blob_polarity = tb.sentiment.polarity
    blob_subjectivity = tb.sentiment.subjectivity

    return {
        'vader': vader_scores,
        'textblob': {
            'polarity': blob_polarity,
            'subjectivity': blob_subjectivity
        }
    }
