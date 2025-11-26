from shared.services.sentiment_analysis_services import analyze_sentiment_text

# Texto de ejemplo para análisis
texto = "El servicio fue excelente, pero la espera fue larga. No estoy seguro si volvería."

# Ejecuta el análisis de sentimiento
sentiment = analyze_sentiment_text(texto)

# Imprime el resultado
print("RESULTADO DEL ANÁLISIS DE SENTIMIENTO:")
print(sentiment)
