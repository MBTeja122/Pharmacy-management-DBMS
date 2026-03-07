<div align="center">
  
  # 💊 PharmaTrust 
  **AI-Driven & Hybrid-Architecture Pharmacy Management System**

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/Flask-Backend-black.svg?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
    <img src="https://img.shields.io/badge/PostgreSQL-13+-336791.svg?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
    <img src="https://img.shields.io/badge/MongoDB-4.4+-47A248.svg?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB" />
    <img src="https://img.shields.io/badge/scikit--learn-ML-F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn" />
  </p>

  > *Transforming traditional pharmacy POS systems into intelligent, data-driven healthcare hubs using Machine Learning and NLP.*

</div>

<br />

## ✨ Core Innovations

| Feature | Description |
| :--- | :--- |
| 📈 **Predictive Forecasting** | Analyzes 30-day sales velocity using **Linear Regression** to generate proactive 7-day revenue and stock projections. |
| 📦 **Smart Bundling (KNN)** | Conducts Market Basket Analysis using **Cosine Similarity** to automatically recommend frequently co-purchased items. |
| 🤖 **NLP Pharmabot** | Processes natural language queries via **spaCy** to check stock and sales, with **FuzzyWuzzy** handling complex spelling typos. |
| 🚨 **Financial Dead Stock** | Quantifies financial exposure by tracking >90 days of dormant inventory, prioritizing alerts by `(Quantity × Cost)`. |
| 📱 **Zero-Config Mobile** | Uses dynamic socket resolution to spin up secure local servers for mobile QR uploads without needing internet access. |

<br />

## 🏗️ System Architecture

PharmaTrust follows a secure, 3-tier architecture with Role-Based Access Control (RBAC), fully separating the UI from the business logic.

* **🖥️ Presentation Layer:** Bootstrap 5 (Responsive UI) and Plotly.js (Interactive Analytics Dashboards).
* **⚙️ Application Layer (Flask):** Modular Blueprint REST routing, PBKDF2-SHA256 hashed security, and dynamic socket bridging.
* **🗄️ Hybrid Data & AI Layer:** * **PostgreSQL:** ACID-compliant relational core for 3NF inventory and financial transactions.
  * **MongoDB:** Flexible NoSQL storage for semi-structured clinical documents and prescriptions.
  * **scikit-learn & spaCy:** The intelligence engine driving predictive ML and semantic NLP processing.

<br />

## 🔄 NLP Query Execution Flow

How the system handles a pharmacist asking: *"Check stock of Doolo 650"*

1. **User Input:** Pharmacist submits natural language text via the dashboard chatbot.
2. **Intent Extraction (spaCy):** The NLP engine maps word vectors to identify the user's goal (e.g., `CHECK_INVENTORY`).
3. **Entity Matching (FuzzyWuzzy):** The system resolves the typo ("Doolo"), finding the closest database match for "Dolo 650" (92% similarity).
4. **Database Execution:** The Flask backend queries the PostgreSQL relational core for specific batch metadata.
5. **Smart Response:** The UI returns an actionable response: *"Dolo 650 has 14 strips available (Batch Expiry: 10/2026)."*

<br />

## 🛠️ Technology Stack & Attribution

A breakdown of the core libraries and how they power the PharmaTrust architecture:

### 🧠 Artificial Intelligence & Data Logic
* **`scikit-learn`**: Drives the predictive analytics engine (Linear Regression for forecasting, KNN for product bundling).
* **`spaCy` & `en_core_web_md`**: Processes pharmacist input into semantic word vectors for intent classification.
* **`FuzzyWuzzy`**: Resolves Levenshtein distance for misspelled generic and brand medicine names.
* **`pandas` & `NumPy`**: Transforms raw SQL output into structured mathematical matrices for ML consumption.

### 🗄️ Hybrid Database Architecture
* **`PostgreSQL` & `psycopg2`**: The relational core enforcing strict 3NF ACID-compliant transactions for sales and inventory.
* **`MongoDB` & `PyMongo`**: The flexible NoSQL storage engine handling semi-structured clinical documents and scanned prescriptions.

### ⚙️ Backend & Frontend
* **`Flask` & `Werkzeug`**: Modular Blueprint architecture handling RESTful routing, secure sessions, and PBKDF2-SHA256 hashing.
* **`Bootstrap 5` & `Plotly.js`**: Renders the responsive grid UI and interactive visualization dashboards.

<br />

## 🚀 Quick Start Guide

<details open>
<summary><b>Local Installation Steps</b></summary>
<br />

**1. Clone the repository**
```bash
git clone [https://github.com/yourusername/PharmaTrust.git](https://github.com/yourusername/PharmaTrust.git)
cd PharmaTrust
```

**2. Setup Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

**4. Environment Variables (`.env`)**
```env
PG_DB=pharmatrust_db
PG_USER=postgres
PG_PASS=yourpassword
MONGO_URI=mongodb://localhost:27017/
```

**5. Launch Server**
```bash
python app.py
```
</details>

---

<div align="center">
  <i>Developed to optimize healthcare inventory and eliminate dead stock.</i>
</div>
