import pandas as pd
import os
import json

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
CSV_PATH = os.path.join(BASE_DIR, 'datasets', 'Disease and their Symptoms.csv')
JSON_PATH = os.path.join(BASE_DIR, 'datasets', 'Major Symptoms.json')
DEF_PATH = os.path.join(BASE_DIR, 'datasets', 'SymptomDefinitions.json')
SPECIALIST_PATH = os.path.join(BASE_DIR, 'datasets', 'Specialist.csv')
TREATMENT_PATH = os.path.join(BASE_DIR, 'datasets', 'Treatment.json')

df = None 
major_symptoms_dict = {}
definitions_dict = {}
specialist_df = None
treatment_dict = {}

def initialize_disease_model():
    global df, major_symptoms_dict, definitions_dict, specialist_df, treatment_dict
    if df is not None: return 

    print("⏳ Loading Disease Models...")
    try:
        df = pd.read_csv(CSV_PATH)
        df["symptoms"] = df["symptoms"].apply(
            lambda x: [s.strip().lower() for s in x.split(",")] if isinstance(x, str) else []
        )
        
        if os.path.exists(JSON_PATH):
            with open(JSON_PATH, 'r') as f:
                data = json.load(f)
                major_symptoms_dict = {item["disease"]: item["major_symptoms"] for item in data}
        
        if os.path.exists(DEF_PATH):
            with open(DEF_PATH, 'r') as f:
                definitions_dict = json.load(f)

        if os.path.exists(SPECIALIST_PATH):
            specialist_df = pd.read_csv(SPECIALIST_PATH)
            specialist_df['disease'] = specialist_df['disease'].str.strip().str.lower()

        if os.path.exists(TREATMENT_PATH):
            with open(TREATMENT_PATH, 'r') as f:
                t_data = json.load(f)
                treatment_dict = {item["symptom"]: item["advice"] for item in t_data}

        print(f"✅ Disease Dataset Loaded: {len(df)} rows.")
    except Exception as e:
        print(f"❌ Error loading Data: {e}")

# ==========================================
# 2. HELPERS
# ==========================================
def get_specialist_info(disease_name):
    if specialist_df is None: return None
    row = specialist_df[specialist_df['disease'] == disease_name.lower()]
    if not row.empty:
        return {"specialist": row.iloc[0]['specialist'], "why": row.iloc[0]['why']}
    return None

def get_treatments(user_symptoms):
    advice_list = {}
    for symptom in user_symptoms:
        clean_sym = symptom.lower().strip()
        if clean_sym in treatment_dict:
            advice_list[symptom] = treatment_dict[clean_sym]
    return advice_list

def get_symptom_objects(symptom_list):
    objects = []
    for s in symptom_list:
        definition = definitions_dict.get(s, s.replace("_", " ").title())
        objects.append({"id": s, "definition": definition})
    return objects

# ==========================================
# 3. ADVANCED LOGIC (Rules 1-4)
# ==========================================

def calculate_metrics(candidate_row, active_symptoms, negative_symptoms):
    """
    Calculates metrics to determine if a disease is a Valid Candidate or Impossible.
    """
    disease_syms = set(candidate_row["symptoms"])
    total_syms = len(disease_syms)
    if total_syms == 0: return 0, 0, 0, 0

    # Intersection with what user HAS
    matched_syms = active_symptoms.intersection(disease_syms)
    overlap = len(matched_syms)
    
    # Intersection with what user does NOT have
    negated_syms = negative_symptoms.intersection(disease_syms)
    
    # Rule 2 Logic: Max Possible Score
    # If the disease has 10 symptoms, and user said NO to 6, max score is 4/10 (0.4).
    # Since 0.4 < 0.55, this disease is IMPOSSIBLE. We should drop it.
    max_possible_overlap = total_syms - len(negated_syms)
    max_possible_score = max_possible_overlap / total_syms
    
    current_score = overlap / total_syms
    
    # Priority for Rule 1 (Ambiguity)
    majors = set(major_symptoms_dict.get(candidate_row["disease"], []))
    major_match = len(matched_syms.intersection(majors))
    
    return overlap, current_score, max_possible_score, major_match

def hybrid_predict(user_symptoms, negative_symptoms=[], stop_asking_for_disease=None, force_prediction=False):
    if df is None: initialize_disease_model()
    
    active_symptoms = set([s.lower().strip() for s in user_symptoms])
    negatives = set([s.lower().strip() for s in negative_symptoms])
    
    confirmed_diseases = []
    
    # --- RULE 3: ITERATIVE GREEDY LOOP ---
    # We keep looking for diseases until we can't match the remaining symptoms
    
    loop_limit = 5
    loop_count = 0
    
    while len(active_symptoms) > 0 and loop_count < loop_limit:
        loop_count += 1
        
        # 1. Score ALL diseases
        candidates = []
        for idx, row in df.iterrows():
            overlap, s_score, max_poss_score, major_match = calculate_metrics(row, active_symptoms, negatives)
            
            # FILTER: Strict Thresholding (Rule 2)
            # If even if we ask everything, we can't reach 55%, drop it.
            # Unless we are forcing a prediction (user said "no" to inputs)
            THRESHOLD = 0.55
            
            if force_prediction and overlap > 0:
                # In force mode, accept anything with overlap
                pass
            elif max_poss_score < THRESHOLD:
                continue # Impossible to be this disease, skip completely
            elif overlap == 0:
                continue
                
            candidates.append({
                "row": row,
                "overlap": overlap,
                "s_score": s_score,
                "major_match": major_match
            })
        
        if not candidates:
            break # No valid diseases found
            
        # 2. Sort Candidates
        # Prioritize: High Overlap > Major Symptoms > High Coverage
        candidates.sort(key=lambda x: (x['overlap'], x['major_match'], x['s_score']), reverse=True)
        
        # We iterate through candidates to find one we can confirm or ask about
        # If the top candidate needs info but we can't ask (ran out of questions), we move to the next.
        
        selected_action = None 
        
        for best in candidates:
            best_row = best["row"]
            best_disease = best_row["disease"]
            
            # --- Rule 1: Dynamic Disambiguation ---
            # Check if there are other candidates with SIMILAR overlap (Ties)
            # Only do this if we haven't confirmed this disease yet
            if not force_prediction and best['s_score'] < 0.55:
                ties = [c for c in candidates if c['overlap'] == best['overlap']]
                if len(ties) > 1:
                    # Collect all unique symptoms from the tied candidates
                    all_tie_syms = set()
                    for t in ties[:3]: # Top 3 ties
                        all_tie_syms.update(t["row"]["symptoms"])
                    
                    # Distinguishing = Union - Active - Negatives
                    distinguishing = list(all_tie_syms - active_symptoms - negatives)
                    
                    if distinguishing:
                        return {
                            "type": "rule_ambiguity",
                            "checklist": get_symptom_objects(distinguishing[:3]),
                            "message": "Your symptoms match multiple conditions. Please check if you have any of these:"
                        }

            # --- Rule 2: Validity Check ---
            if best['s_score'] >= 0.55 or (force_prediction and best == candidates[0]):
                # CONFIRMED!
                matched_syms = active_symptoms.intersection(set(best_row["symptoms"]))
                
                confirmed_diseases.append({
                    "disease": best_disease,
                    "confidence": best['s_score'],
                    "matched": list(matched_syms)
                })
                
                # Rule 3: Consume Symptoms
                active_symptoms = active_symptoms - matched_syms
                
                # Break inner candidate loop to restart greedy loop with remaining symptoms
                selected_action = "confirmed"
                break 
            
            # --- Verification Loop ---
            # Disease is viable (max_possible > 55%) but not confirmed (< 55%)
            # We need to ask questions.
            
            majors = major_symptoms_dict.get(best_disease, [])
            all_syms = set(best_row["symptoms"])
            
            # Ask Missing Majors first, then General
            missing_majors = [s for s in majors if s not in active_symptoms and s not in negatives]
            missing_general = [s for s in all_syms if s not in active_symptoms and s not in negatives]
            
            ask_list = missing_majors if missing_majors else missing_general
            
            if ask_list:
                # We found a valid question to ask for the best candidate.
                return {
                    "type": "rule_threshold",
                    "target_disease": best_disease,
                    "checklist": get_symptom_objects(ask_list[:3]),
                    "message": "I am analyzing your symptoms. Please check any of the following that apply to you:"
                }
            
            # If ask_list is empty, it means we ran out of questions for this candidate
            # AND we haven't reached 55%. 
            # In the previous code, this was a dead end.
            # NOW: We simply 'continue' the loop to look at the 2nd best candidate.
            continue 
        
        if selected_action != "confirmed":
            # If we went through all candidates and couldn't confirm OR ask a question, stop.
            break

    # --- Rule 4: Residuals ---
    # Whatever is left in active_symptoms is unexplained
    
    residual_symptoms = list(active_symptoms)
    residual_advice = get_treatments(residual_symptoms)

    if confirmed_diseases:
        primary = confirmed_diseases[0]
        return {
            "type": "prediction",
            "prediction": primary,
            "comorbidities": confirmed_diseases[1:],
            "specialist": get_specialist_info(primary["disease"]),
            "treatments": get_treatments(primary["matched"]),
            "residuals": residual_advice,
            "message": "prediction_ready"
        }
    
    elif residual_symptoms:
        return {
            "type": "residuals_only",
            "treatments": residual_advice,
            "message": "symptomatic_care"
        }
    
    else:
        return {
            "type": "unknown",
            "message": "I couldn't identify enough symptoms. Please describe your condition."
        }