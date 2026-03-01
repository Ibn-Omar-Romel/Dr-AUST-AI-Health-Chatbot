import pandas as pd
import os
import json

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
CSV_PATH = os.path.join(BASE_DIR, 'datasets', 'Disease and their Symptoms.csv')
JSON_PATH = os.path.join(BASE_DIR, 'datasets', 'Major Symptoms.json')

df = None 
major_symptoms_dict = {}

def initialize_disease_model():
    global df, major_symptoms_dict
    if df is not None: return 

    print("⏳ Loading Disease Models...")
    try:
        # 1. Load CSV
        df = pd.read_csv(CSV_PATH)
        df["symptoms"] = df["symptoms"].apply(
            lambda x: [s.strip().lower() for s in x.split(",")] if isinstance(x, str) else []
        )
        
        # 2. Load Major Symptoms JSON
        if os.path.exists(JSON_PATH):
            with open(JSON_PATH, 'r') as f:
                data = json.load(f)
                major_symptoms_dict = {item["disease"]: item["major_symptoms"] for item in data}
            print(f"✅ Major Symptoms loaded for {len(major_symptoms_dict)} diseases.")
        else:
            print("⚠️ Warning: Major Symptoms.json not found.")

        print(f"✅ Disease Dataset Loaded: {len(df)} rows.")
    except Exception as e:
        print(f"❌ Error loading Data: {e}")

# ==========================================
# 2. CORE LOGIC: VALIDATION & QUESTIONING
# ==========================================

def get_next_questions(disease, user_symptoms, all_disease_symptoms):
    """
    Decides what to ask.
    CRITICAL CHANGE: It strictly excludes symptoms the user already has.
    """
    # Get major symptoms for this disease
    majors = major_symptoms_dict.get(disease, [])
    
    # 1. Filter out symptoms the user ALREADY HAS
    missing_majors = [s for s in majors if s not in user_symptoms]
    missing_general = [s for s in all_disease_symptoms if s not in user_symptoms]
    
    # 2. Priority: Ask missing MAJORS first
    if missing_majors:
        return missing_majors, "major"
    else:
        # If all majors are present, ask general symptoms
        return missing_general, "general"

def calculate_confidence(matched_symptoms, all_disease_symptoms):
    if len(all_disease_symptoms) == 0: return 0.0
    return len(matched_symptoms) / len(all_disease_symptoms)

# ==========================================
# 3. PREDICTION ENGINE
# ==========================================

def hybrid_predict(user_symptoms):
    if df is None: initialize_disease_model()
    
    user_symptoms_set = set([s.lower().strip() for s in user_symptoms])
    
    # 1. FIND BEST CANDIDATE
    best_match = None
    highest_overlap = 0
    
    for idx, row in df.iterrows():
        disease_syms = set(row["symptoms"])
        intersection = user_symptoms_set.intersection(disease_syms)
        
        if len(intersection) > highest_overlap:
            highest_overlap = len(intersection)
            best_match = row

    if best_match is None or highest_overlap == 0:
        return {
            "type": "unknown", 
            "message": "I couldn't match your symptoms to any disease yet. Please describe more."
        }

    disease_name = best_match["disease"]
    all_symptoms = best_match["symptoms"]
    matched_symptoms = list(user_symptoms_set.intersection(set(all_symptoms)))
    
    confidence = calculate_confidence(matched_symptoms, all_symptoms)
    
    # ==================================================
    # 4. DECISION GATE (Updated 50% Rule)
    # ==================================================
    THRESHOLD = 0.50  # Changed from 0.40 to 0.50

    # Get questions (excluding what user already has)
    questions, q_type = get_next_questions(disease_name, user_symptoms_set, all_symptoms)
    ask_list = questions[:3] # Ask 3 at a time

    # LOGIC:
    # If Confidence > 50%: Predict (Propability)
    # If Confidence < 50%: Keep asking questions
    
    if confidence >= THRESHOLD:
        return {
            "type": "prediction",
            "prediction": {
                "disease": disease_name,
                "confidence": confidence
            },
            "next_suggestions": ask_list, # Ask remaining symptoms to confirm further
            "message": "prediction_ready" # Let app.py handle the text
        }
    else:
        # Ask Questions
        if q_type == "major":
            msg = f"It could be **{disease_name}**, but I need to check for major symptoms first."
        else:
            msg = f"It could be **{disease_name}**, but I need more details."

        return {
            "type": "rule",
            "possible_diseases": [disease_name],
            "user_symptoms": list(user_symptoms_set),
            "ask_user_about": ask_list,
            "message": f"{msg} Do you have any of these? **{', '.join(ask_list)}**"
        }