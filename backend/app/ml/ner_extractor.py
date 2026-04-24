from transformers import pipeline
from functools import lru_cache


@lru_cache(maxsize=1)
def load_ner_pipeline():
    """Load biomedical NER pipeline. Loaded once and cached in memory."""
    return pipeline(
        "ner",
        model="d4data/biomedical-ner-all",
        aggregation_strategy="simple"
    )


def extract_medical_entities(text: str) -> dict:
    """Extract medical named entities from clinical text using SciBERT."""
    ner = load_ner_pipeline()

    # Process in chunks to avoid token limit
    max_length = 500
    words = text.split()
    chunks = [" ".join(words[i:i + max_length]) for i in range(0, len(words), max_length)]

    all_entities = []
    for chunk in chunks[:5]:  # limit to 5 chunks
        entities = ner(chunk)
        all_entities.extend(entities)

    # Group by entity type
    grouped = {}
    for ent in all_entities:
        if ent["score"] > 0.8:  # confidence threshold
            entity_type = ent["entity_group"]
            if entity_type not in grouped:
                grouped[entity_type] = []
            word = ent["word"].replace("##", "")
            if word not in grouped[entity_type]:
                grouped[entity_type].append(word)

    return grouped
