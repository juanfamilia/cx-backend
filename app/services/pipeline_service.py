def process_interaction(interaction_id: str):
    print(f"Processing interaction: {interaction_id}")

    transcript = fake_transcription()

    segments = segment_transcript(transcript)

    events = extract_events(segments)

    scores = compute_scores(events)

    insights = generate_insights(events, scores)

    return {
        "transcript": transcript,
        "segments": segments,
        "events": events,
        "scores": scores,
        "insights": insights
    }


def fake_transcription():
    return "Buenos días, en qué puedo ayudarle..."


def segment_transcript(transcript: str):
    return [
        {"speaker": "agent", "text": transcript, "start": 0, "end": 5}
    ]


def extract_events(segments):
    return [
        {
            "event": "greeting",
            "timestamp": "00:01",
            "text": segments[0]["text"]
        }
    ]


def compute_scores(events):
    score = 0

    for e in events:
        if e["event"] == "greeting":
            score += 1

    return {"cortesia": score}


def generate_insights(events, scores):
    return {
        "summary": "Buen inicio de interacción",
        "score": scores
    }
