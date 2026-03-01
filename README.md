<div align="center">
  <img src="https://img.shields.io/badge/Status-Undergraduate%20Thesis-blueviolet" alt="Status">
  <img src="https://img.shields.io/badge/Model-Fine--Tuned%20XLM--R-blue" alt="Model">
  <img src="https://img.shields.io/badge/Frontend-React.js-61DAFB" alt="Frontend">
  <img src="https://img.shields.io/badge/Backend-Python-3776AB" alt="Backend">
  
  <h1>🩺 Dr. AUST</h1>
  <h3>A Bilingual AI Chatbot for Disease & Symptom Detection and Specialist Recommendation</h3>
</div>

<hr />

<h2>📖 Project Overview</h2>
<p align="justify">
  <b>Dr. AUST</b> is an advanced, voice-enabled healthcare chatbot designed to bridge the gap between preliminary symptoms and professional medical care. Developed as an undergraduate thesis project, the system utilizes state-of-the-art Natural Language Processing (NLP) to understand complex medical descriptions in both <b>Bengali</b> and <b>English</b>. It extracts root symptoms, predicts potential diseases, and intelligently recommends the appropriate medical specialist.
</p>

<h2>🌟 Core Capabilities</h2>
<ul>
  <li><b>Bilingual NLP Engine:</b> Seamlessly processes native Bengali and English queries without losing medical context.</li>
  <li><b>Symptom Extraction:</b> Utilizes a custom fine-tuned <b>XLM-RoBERTa (XLM-R)</b> model to parse natural language and extract core symptoms.</li>
  <li><b>Disease Prediction:</b> Maps extracted symptoms against a robust dataset to calculate disease probability.</li>
  <li><b>Specialist Routing:</b> Automatically suggests the correct medical department (e.g., Neurologist, Cardiologist) based on the AI's diagnosis.</li>
  <li><b>Modern Interface:</b> A clean, intuitive React-based web interface designed for patient accessibility.</li>
</ul>

<hr />

<h2>📂 System Architecture</h2>
<pre>
📁 CHATBOT 1.1
├── 📂 backend                 # Python API & Machine Learning core
│   ├── 📂 datasets            # Bengali/English Symptom & Disease mappings
│   ├── 📂 models              # Target directory for the Hugging Face weights
│   ├── 📂 services            # Prediction & Extraction logic scripts
│   └── app.py                 # Main backend server endpoint
├── 📂 frontend-new            # Modern Web Interface
│   ├── 📂 src                 # React components and state management
│   ├── 📂 public              # Static assets
│   └── package.json           # Node.js dependencies
└── 📂 Extra Codes             # Model training and optimization scripts
</pre>

<hr />

<h2>🛠️ Technology Stack</h2>
<table width="100%">
  <tr>
    <th>Domain</th>
    <th>Technologies Used</th>
  </tr>
  <tr>
    <td><b>Machine Learning & NLP</b></td>
    <td>PyTorch, Hugging Face Transformers, XLM-RoBERTa</td>
  </tr>
  <tr>
    <td><b>Backend Server</b></td>
    <td>Python, Flask / FastAPI, Scikit-learn, Pandas</td>
  </tr>
  <tr>
    <td><b>Frontend Web App</b></td>
    <td>React.js, Node.js, Tailwind CSS</td>
  </tr>
</table>

<hr />

<h2>⚙️ Setup & Installation</h2>

<h3>1. Clone the Repository</h3>
<pre>
git clone https://github.com/Ibn-Omar-Romel/Dr-AUST-AI-Health-Chatbot.git
cd Dr-AUST-AI-Health-Chatbot
</pre>

<h3>2. Download the AI Model (Required)</h3>
<p>Due to GitHub's file size limits, the fine-tuned XLM-R model weights are hosted on Hugging Face. You must download them before running the backend.</p>
<ol>
  <li>Go to the project's Hugging Face repository: <a href="https://huggingface.co/romooo/Dr-AUST-XLM-R-Symptom-Extractor/tree/main" target="_blank"><b>Dr-AUST-XLM-R-Symptom-Extractor</b></a>.</li>
  <li>Download all the files listed in the repository (most importantly, the <code>model.safetensors</code> file).</li>
  <li>Navigate to the <code>backend/models/</code> directory in your cloned repository.</li>
  <li>Create a new folder named exactly: <code>xlm-r-model-final</code>.</li>
  <li>Place all the downloaded Hugging Face files inside that <code>xlm-r-model-final</code> folder.</li>
</ol>

<h3>3. Backend Setup (AI & API)</h3>
<pre>
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
</pre>

<h3>4. Frontend Setup (UI)</h3>
<pre>
cd frontend-new
npm install
npm start
</pre>

<hr />

<h2>🎓 Academic Context</h2>
<p>
  This project was researched and developed as part of an Undergraduate Thesis at the <b>Department of Computer Science and Engineering (CSE)</b> at <b>Ahsanullah University of Science and Technology (AUST)</b>.
</p>
<p><b>Lead Developer & Researcher:</b> Romel</p>

<div align="center">
  <p>© 2026 | Dr. AUST AI Healthcare Project</p>
</div>
