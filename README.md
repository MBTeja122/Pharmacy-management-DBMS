<div align="center">
  <h1>💊 PharmaTrust</h1>
  <p><b>An AI-Driven, Hybrid-Architecture Pharmacy Management System</b></p>
  
  ![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?logo=python&logoColor=white)
  ![Flask](https://img.shields.io/badge/Flask-Backend-black.svg?logo=flask&logoColor=white)
  ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-336791.svg?logo=postgresql&logoColor=white)
  ![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-47A248.svg?logo=mongodb&logoColor=white)
  ![scikit-learn](https://img.shields.io/badge/scikit--learn-Machine%20Learning-F7931E.svg?logo=scikit-learn&logoColor=white)
  ![spaCy](https://img.shields.io/badge/spaCy-NLP-09A3D5.svg)
</div>

---

## 📖 Project Overview
PharmaTrust is a modern, full-stack pharmacy management platform designed to transcend traditional point-of-sale systems. By integrating **Machine Learning (ML)** for demand forecasting and **Natural Language Processing (NLP)** for intuitive data querying, it empowers pharmacists to make proactive, data-driven decisions. The system employs a robust **Hybrid Database Architecture**, ensuring ACID-compliant financial transactions alongside flexible clinical document storage.

---

## ✨ Core Innovations & Features

* 📈 **Predictive Demand Forecasting**: Analyzes 30-day sales velocity to generate 7-day revenue and stock projections.
* 📦 **Smart Product Bundling**: Utilizes K-Nearest Neighbors (KNN) for Market Basket Analysis, recommending frequently co-purchased items.
* 🤖 **NLP-Driven Chatbot (Pharmabot)**: Allows pharmacists to query stock availability and revenue summaries using natural language with typo tolerance.
* 🚨 **Financial Dead Stock Alerts**: Quantifies financial exposure by tracking dormant inventory (>90 days) and prioritizing alerts based on value (Quantity × Cost).
* 📱 **Zero-Config Mobile Bridging**: Implements dynamic socket resolution to auto-detect local IPs, spinning up secure local servers for mobile QR prescription uploads without internet dependency.

---

## 🏗️ System Architecture

PharmaTrust follows a secure, 3-tier architecture with Role-Based Access Control (RBAC), completely separating the presentation layer from business and data logic.

```mermaid
graph TD
    %% Styling
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef backend fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef database fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;
    classDef ai fill:#fff3e0,stroke:#e65100,stroke-width:2px;

    %% Nodes
    subgraph Presentation Layer
        UI[Web UI: HTML5, CSS3, Bootstrap 5]:::frontend
        Viz[Dashboards: Plotly.js, Vanilla JS]:::frontend
    end

    subgraph Application Layer (Flask)
        Auth[Auth & RBAC Sessions]:::backend
        API[RESTful Blueprint Endpoints]:::backend
        Sockets[Zero-Config Mobile Sockets]:::backend
    end

    subgraph Data & AI Layer
        SQL[(PostgreSQL: Core Transactions)]:::database
        NoSQL[(MongoDB: Prescriptions)]:::database
        ML[ML Engine: scikit-learn]:::ai
        NLP[NLP Engine: spaCy & FuzzyWuzzy]:::ai
    end

    %% Connections
    UI <--> API
    Viz <--> API
    API <--> Auth
    Auth <--> SQL
    API <--> SQL
    API <--> NoSQL
    API <--> Sockets
    SQL --> ML
    API <--> NLP
