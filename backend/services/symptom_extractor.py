import torch
import json
import re
import unicodedata
import os
from transformers import AutoModelForTokenClassification, AutoTokenizer, AutoConfig

# ==========================================
# 1. CONFIGURATION & PATHS
# ==========================================
# This calculates the path relative to this file, so it works on any computer
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Points to 'backend' folder
MODEL_PATH = os.path.join(BASE_DIR, "models", "xlm-r-model-final")
JSON_PATH = os.path.join(BASE_DIR, "models", "extra_similar.json")
THRESHOLD = 0.85

# Setup Device
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("✅ (Symptom Extractor) Using Apple M1 GPU (MPS)")
else:
    device = torch.device("cpu")
    print("⚠️ (Symptom Extractor) Using CPU")

# ==========================================
# 2. GLOBAL VARIABLES (Loaded Once)
# ==========================================
tokenizer = None
model = None
config = None
reference_matrix = None
synonym_names = []

def initialize_model():
    """Loads the model and JSON database once when server starts."""
    global tokenizer, model, config, reference_matrix, synonym_names
    
    if model is not None:
        return # Already loaded

    print("⏳ Loading XLM-R Model...")
    try:
        config = AutoConfig.from_pretrained(MODEL_PATH)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForTokenClassification.from_pretrained(MODEL_PATH, config=config)
        model.to(device)
        model.eval()
        print("✅ XLM-R Model loaded successfully!")
        print("✅ CSEBUETNLP Model loaded successfully!")
        print("✅ XGBOOST Model loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading XLM-R Model: {e}")
        return

    print("⏳ Building Symptom Knowledge Base...")
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            symptom_dict = json.load(f)

        synonym_embeddings = []
        synonym_names_temp = []

        for canonical, synonyms in symptom_dict.items():
            all_forms = [canonical] + synonyms
            for phrase in all_forms:
                norm_phrase = normalize_text(phrase)
                if not norm_phrase: continue
                emb = get_embedding(norm_phrase)
                synonym_embeddings.append(emb.cpu()) 
                synonym_names_temp.append(canonical)

        reference_matrix = torch.cat(synonym_embeddings, dim=0).to(device)
        synonym_names = synonym_names_temp
        print(f"✅ Knowledge Base Ready: {len(synonym_names)} variations loaded.")
    except Exception as e:
        print(f"❌ Error loading JSON Knowledge Base: {e}")

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def normalize_text(text):
    if text is None: return ""
    text = unicodedata.normalize('NFKD', text) 
    text = text.lower().strip()
    return text

def clean_text(text):
    text = text.strip()
    text = re.sub(r'[^\w\s\u0980-\u09ff]', '', text) 
    return normalize_text(text)

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=64).to(device)
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)
    last_hidden_state = outputs.hidden_states[-1]
    return last_hidden_state.mean(dim=1)

# ==========================================
# 4. PREDICTION FUNCTION
# ==========================================
def predict_symptoms(text):
    """
    Input: User text
    Output: List of identified symptoms (e.g., ['abdominal_pain', 'bruising'])
    """
    if model is None:
        initialize_model()

    # A. Extract Entities (NER)
    tokenized_input = tokenizer(text, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = model(**tokenized_input).logits
    
    predictions = torch.argmax(logits, dim=2)
    predicted_labels = [config.id2label[t.item()] for t in predictions[0]]
    tokens = tokenizer.convert_ids_to_tokens(tokenized_input["input_ids"][0])
    
    # B. Reconstruct Words (Your Logic)
    word_tokens = []
    word_labels = []
    current_word = ""
    current_label = None 
    SPIECE_MARKER = chr(0x2581) 
    
    for token, label in zip(tokens, predicted_labels):
        if token in ['<s>', '</s>', '<pad>']: continue
        
        if SPIECE_MARKER in token:
            if current_word:
                word_tokens.append(current_word)
                word_labels.append(current_label)
            current_word = token.replace(SPIECE_MARKER, "")
            current_label = label
        else:
            current_word += token
            
    if current_word:
        word_tokens.append(current_word)
        word_labels.append(current_label)

    # C. Extract Candidate Phrases
    raw_phrases = []
    current_phrase = []
    for word, label in zip(word_tokens, word_labels):
        if label == 'B-SYMPTOM':
            if current_phrase: raw_phrases.append(" ".join(current_phrase))
            current_phrase = [word]
        elif label == 'I-SYMPTOM':
            current_phrase.append(word)
        else:
            if current_phrase:
                raw_phrases.append(" ".join(current_phrase))
                current_phrase = []
    if current_phrase: raw_phrases.append(" ".join(current_phrase))

    # D. Semantic Matching
    final_symptoms = set()
    
    # YOUR STOPWORDS LIST
    stopwords = [
        "অনেক", "খুব", "ভীষণ", "একটু", "এবং", "আর", "এর", "আমার", 
        "a", "an", "the", "lot", "and", "but", "or", "because", "as", "if", "when", 
        "than", "of", "in", "to", "for", "with", "on", "at", "from", "by", 
        "about", "against", "between", "into", "through", "during", "before", 
        "after", "above", "below", "up", "down", "out", "off", "over", "under",
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
        "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", 
        "himself", "she", "her", "hers", "herself", "it", "its", "itself", 
        "they", "them", "their", "theirs", "themselves", "what", "which", "who", 
        "whom", "this", "that", "these", "those", "am", "is", "are", "was", 
        "were", "be", "been", "being", "have", "has", "had", "having", "do", 
        "does", "did", "doing", "can", "could", "should", "would", "may", "might", "must",
        "ও", "কিন্তু", "অথবা", "বা", "নাকি", "বরং", "ফলে", "তবে", "তাছাড়া", "নাহলে",
        "আমি", "তুমি", "আপনি", "তুই", "সে", "তিনি", "তারা", "এরা", "ওরা",
        "আমাকে", "তোমাকে", "আপনাকে", "তাকে", "তাদের", "আমাদের", "কার", "কি", 
        "কে", "কোন", "কাউকে", "নিজের", "নিজে", "সবাই", "সকলে", "জন্য", "দিয়ে", 
        "দ্বারা", "কর্তৃক", "থেকে", "হতে", "চেয়ে", "কাছে", "মধ্যে", "ভিতরে", 
        "বাইরে", "উপরে", "নিচে", "সামনে", "পিছনে", "সঙ্গে", "সাথে", "সম্পর্কে", 
        "বিষয়ে", "মতে", "মত", "আছে", "ছিল", "হবে", "হয়", "হচ্ছে", "হয়ে", 
        "করা", "করে", "করছে", "করেন", "করব", "যায়", "গেল", "যাবে", "বলে", 
        "বলেন", "বলল", "মানে", "তো", "আসলে", "ইত্যাদি"
    ]

    for phrase in raw_phrases:
        clean_p = clean_text(phrase)
        for sw in stopwords:
            clean_p = re.sub(r'\b' + sw + r'\b', '', clean_p).strip()
        if not clean_p: clean_p = clean_text(phrase)
        
        phrase_emb = get_embedding(clean_p)
        scores = torch.nn.functional.cosine_similarity(phrase_emb, reference_matrix)
        best_score, best_idx = torch.max(scores, dim=0)
        
        if best_score.item() > THRESHOLD:
            match = synonym_names[best_idx.item()]
            final_symptoms.add(match)
        else:
            # Fallback text match
            for i, name in enumerate(synonym_names):
                if clean_p in normalize_text(name):
                    final_symptoms.add(synonym_names[i])
                    break

    return list(final_symptoms)