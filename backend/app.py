print("--- DEBUG: PYTHON IS STARTING ---") 
import pandas as pd
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from services.symptom_extractor import predict_symptoms, initialize_model as init_xlmr
from services.disease_predictor import hybrid_predict, initialize_disease_model as init_disease

app = Flask(__name__)
CORS(app)

print("🚀 Starting Server...")
init_xlmr()
init_disease()

def format_bot_reply(result):
    if result["type"] == "prediction":
        disease = result["prediction"]["disease"]
        msg = f"**Diagnosis:** Based on your symptoms, the most likely condition is **{disease}**.\n\n"
        
        if result.get("comorbidities"):
            secondary = [d['disease'] for d in result['comorbidities']]
            msg += f"⚠️ **Note:** You also show signs of: {', '.join(secondary)}.\n\n"

        spec_info = result.get("specialist")
        if spec_info:
            msg += f"**Recommendation:** You should consult a **{spec_info['specialist']}**. They specialize in {spec_info['why'].lower()}.\n\n"
        
        treatments = result.get("treatments")
        if treatments:
            msg += "**Immediate Care:**\n"
            for symptom, advice_list in treatments.items():
                clean_sym = symptom.replace("_", " ").title()
                msg += f"• **{clean_sym}**: {'; '.join(advice_list)}.\n"
        
        residuals = result.get("residuals")
        if residuals:
            msg += "\n**Care for Other Symptoms:**\n"
            for symptom, advice_list in residuals.items():
                clean_sym = symptom.replace("_", " ").title()
                msg += f"• **{clean_sym}**: {'; '.join(advice_list)}.\n"
        return msg

    elif result["type"] == "residuals_only":
        msg = "**Diagnosis:** I couldn't identify a specific disease pattern, but I can help with your symptoms.\n\n"
        msg += "**Symptomatic Care:**\n"
        treatments = result.get("treatments")
        for symptom, advice_list in treatments.items():
            clean_sym = symptom.replace("_", " ").title()
            msg += f"• **{clean_sym}**: {'; '.join(advice_list)}.\n"
        return msg

    elif result["type"] in ["rule_ambiguity", "rule_threshold"]:
        return result["message"]

    else:
        return result.get("message", "I couldn't make a prediction.")

@app.route('/predict', methods=['POST'])
def chat():
    data = request.json
    user_text = data.get('text', '')
    current_symptoms = data.get('symptoms', []) 
    explicit_symptoms = data.get('explicit_symptoms', []) 
    negative_symptoms = data.get('negative_symptoms', [])
    is_none_selected = data.get('is_none_selected', False)

    print(f"\n📩 User Input: '{user_text}'")
    
    if user_text.strip().lower() in ['reset', 'clear', 'restart']:
        return jsonify({ "reply": "Memory cleared.", "symptoms": [], "negatives": [], "prediction_raw": {} })

    # Handle "None of the above"
    if is_none_selected:
        return jsonify({
            "reply": "Okay. If you feel any other symptoms, please type them below. If not, just type **no** to see your results.",
            "symptoms": current_symptoms, 
            "negatives": negative_symptoms, # Keep negatives!
            "prediction_raw": {} 
        })

    # Extract new
    new_extracted = []
    if user_text.lower().strip() not in ['no', 'none', 'nothing', 'na']:
        try:
            new_extracted = predict_symptoms(user_text)
        except:
            pass

    # Merge
    updated_symptoms = list(set(current_symptoms + new_extracted + explicit_symptoms))
    # Filter negatives
    updated_symptoms = [s for s in updated_symptoms if s not in negative_symptoms]
    
    print(f"🧠 Active: {updated_symptoms}")
    print(f"❌ Negatives: {negative_symptoms}")

    # Check for force stop
    force_stop = (user_text.lower().strip() in ['no', 'none', 'nothing', 'na'])
    
    if not updated_symptoms:
        bot_reply = "I couldn't identify any specific symptoms yet. Please describe how you feel."
        prediction_result = {}
    else:
        prediction_result = hybrid_predict(
            updated_symptoms, 
            negative_symptoms, 
            force_prediction=force_stop
        )
        bot_reply = format_bot_reply(prediction_result)
    
    return jsonify({
        "reply": bot_reply,
        "symptoms": updated_symptoms,
        "negatives": negative_symptoms, 
        "prediction_raw": prediction_result 
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)