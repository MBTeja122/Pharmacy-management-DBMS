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
| 🤖 **NLP Pharmabot** | Processes natural language queries via a multi-layered NLP pipeline to check stock and sales, tolerating complex spelling typos. |
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
2. **Grammar Normalization (Parrot):** The input is paraphrased and linguistically corrected to ensure standardized syntax.
3. **Intent Extraction (spaCy):** The NLP engine maps word vectors to identify the user's goal (e.g., `CHECK_INVENTORY`).
4. **Entity Matching (FuzzyWuzzy):** The system resolves the typo ("Doolo"), finding the closest database match for "Dolo 650" (92% similarity).
5. **Database Execution:** The Flask backend queries the PostgreSQL relational core for specific batch metadata.
6. **Smart Response:** The UI returns an actionable response: *"Dolo 650 has 14 strips available (Batch Expiry: 10/2026)."*

<br />

## 🛠️ Extensive Technology Stack & Library Attribution

PharmaTrust heavily relies on the incredible work of the open-source community. Below is a detailed attribution of the core libraries and how they are architected within the system:

### 🤖 The Pharmabot NLP Stack
The natural language interface of PharmaTrust relies on a sophisticated, multi-layered pipeline to process, correct, and understand free-text queries.
* **`spaCy` (`en_core_web_md`) - Semantic Intent Classification:** Acts as the core analytical engine. It converts user queries into multi-dimensional word vectors. Instead of rigid keyword matching, spaCy calculates the cosine similarity between the input and predefined intent categories (e.g., `CHECK_STOCK`), allowing the bot to understand the *meaning* behind the sentence.
* **`Parrot` Paraphraser - Linguistic Correction:** Acts as the linguistic bridge, normalizing user input before it hits the intent classifier. By paraphrasing messy or grammatically incorrect queries into standardized syntax, it significantly increases the accuracy of spaCy's intent matching and ensures the bot handles conversational variations gracefully.
* **`FuzzyWuzzy` & `python-Levenshtein` - Entity Resolution:** The typo-tolerance mechanism for complex medical terminology. Pharmacists often misspell generic drug names. FuzzyWuzzy calculates the Levenshtein distance (the minimum number of single-character edits required to change one word into another) using the `WRatio` scoring method, ensuring the chatbot retrieves the correct database entity despite human error.

### 🧠 Machine Learning & Data Logic
* **`scikit-learn`**: The backbone of the predictive analytics engine. Deploys **Linear Regression** for calculating 30-day sales slopes (demand forecasting) and **K-Nearest Neighbors (KNN)** utilizing Cosine Similarity for intelligent product bundling.
* **`pandas` & `NumPy`**: Crucial for data vectorization, transforming raw relational SQL output from PostgreSQL into structured mathematical matrices for ML model consumption.

### 🗄️ Hybrid Database Drivers
* **`psycopg2` (PostgreSQL Adapter)**: Executes optimized raw SQL queries, enforcing strict 3NF referential integrity and ACID compliance for sales, purchases, and batch tracking within the PostgreSQL core.
* **`PyMongo` (MongoDB Driver)**: Enables high-speed binary document storage and retrieval for scanned prescriptions and unstructured clinical metadata within the MongoDB cluster.

### ⚙️ Backend Framework & Middleware
* **`Flask`**: The core backend framework, utilizing a modular `Blueprint` structure to route discrete services cleanly.
* **`Werkzeug`**: Provides cryptographic security via PBKDF2-SHA256 password hashing and secure user session management.
* **Python `socket`**: Auto-detects the host machine's IP address to enable the Zero-Config mobile bridging feature for local network routing.

### 🎨 Frontend & Visualization
* **`Bootstrap 5`**: Delivers the mobile-first, responsive grid architecture and UI components.
* **`Plotly.js`**: Renders the complex, interactive data visualizations on the admin dashboard, turning ML forecasts into readable, hoverable graphs.

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
*Note: The server will automatically output your local network IP in the terminal to connect your mobile device for QR uploads.*
</details>

---
<br />

## 🙏 Acknowledgments & Open Source Attribution

Building a complex, AI-driven system like PharmaTrust would not be possible without the foundational work of the open-source community. We extend our deepest gratitude to the creators, maintainers, and contributors of the following projects:

* **[Parrot Paraphraser](https://github.com/PrithivirajDamodaran/Parrot_Paraphraser):** A special acknowledgment for providing the robust linguistic engine that normalizes and corrects user grammar, significantly enhancing our chatbot's intent accuracy.
* **[spaCy](https://spacy.io/):** For the powerful NLP processing framework and pre-trained word vectors that drive the semantic understanding behind our Pharmabot.
* **[scikit-learn](https://scikit-learn.org/):** For the accessible, highly optimized machine learning algorithms that make our predictive demand forecasting and KNN bundling possible.
* **[FuzzyWuzzy](https://github.com/seatgeek/fuzzywuzzy):** For the brilliant Levenshtein distance string-matching algorithms that allow our system to gracefully handle complex medical spelling errors.
* **[Flask](https://flask.palletsprojects.com/) & [Werkzeug](https://werkzeug.palletsprojects.com/):** For the lightweight yet highly scalable Python backend architecture that serves as the backbone of our application.
* **[PostgreSQL](https://www.postgresql.org/) & [MongoDB](https://www.mongodb.com/):** For providing the rock-solid data infrastructure needed to build our hybrid transactional and document storage system.
<div align="center">
  <i>Developed to optimize healthcare inventory and eliminate dead stock.</i>
</div>
