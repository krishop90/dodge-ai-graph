# Dodge AI - Assessment

**Dodge AI** is a specialized RAG-based query system designed to provide precise answers restricted strictly to a provided dataset. By leveraging a relational PostgreSQL backbone and a dynamic graph visualization, the system ensures data integrity while offering an intuitive way to explore connections.

## Overview
This project was developed during an intensive 48-hour sprint to transform a static dataset into an interactive, queryable intelligence tool. The primary goal was **strict data adherence**: the LLM is restricted from using external knowledge, ensuring every response is grounded directly in the uploaded records.

* **Deployed App:** [https://dodge-ai-graph-omega.vercel.app/](https://dodge-ai-graph-omega.vercel.app/)
* **Video Demo:** [https://drive.google.com/file/d/10sYS_-iDfdcIo0P03mQFQnSdZjvNJs5U/view?usp=sharing/](https://drive.google.com/file/d/10sYS_-iDfdcIo0P03mQFQnSdZjvNJs5U/view?usp=sharing)
* **LLM Chat:** [https://gemini.google.com/share/f1e978bf49af/](https://gemini.google.com/share/f1e978bf49af)
---

## Tech Stack

* **Frontend:** React / Next.js (Deployed on Vercel)
* **Backend:** Python (FastAPI)
* **Database:** PostgreSQL (Relational storage for high-precision querying)
* **LLM:** Groq (used Gemini but i was getting rate limits)
* **Visualization:** Graph-based UI for mapping data relationships (React , ReactFlow)

---

## Development Journey

### Phase 1: The Neo4j Experiment
The initial approach involved using **Neo4j AuraDB** to create a knowledge graph. While I successfully reached a level where I could see the graph and run queries, the data ingestion was incomplete and the initial graph libraries produced "weird" or "whack" visualizations. To prioritize data integrity and meet my deadline, I chose to scrap this version and pivot.

### Phase 2: PostgreSQL & Relational Logic
I shifted to a robust relational model to ensure 100% accuracy:
1.  **Manual Build:** Moved away from AI-heavy IDEs and asked LLM to step-by-step guide me for manual coding approach to fully understand the backend flow.
2.  **Ingestion:** Developed `ingest.py` to parse dataset files and populate PostgreSQL tables.
3.  **Refined Scope:** Focused on high-quality ingestion of core data files to ensure the DB was reliable.

### Phase 3: Prompt Engineering & Guardrails
To prevent "hallucinations" (the AI making things up), I implemented:
* **Strict System Prompts:** Detailed instructions forcing the model to look *only* at the database schema and content.
* **Few-Shot Prompting:** Provided specific examples (e.g., product fetching) to teach the LLM how to translate natural language into accurate data retrieval.
* **Guardrails:** Added a validation layer that rejects queries falling outside the dataset's scope.

---

## Key Features

* **Restricted Intelligence:** The AI acts as a direct interface for the database, not as a general-purpose chatbot.
* **Graph Visualization:** A custom-built graph view that renders data nodes and their relationships dynamically.
* **Hybrid Search:** Combines structured SQL-like precision with natural language understanding.

---

## Lessons Learned
* **Tool Selection:** Sometimes a reliable relational database (Postgres) is more effective than a complex graph database (Neo4j) for specific dataset constraints.
* **Step-by-Step Logic:** Moving away from "Antigravity" or "Cursor" and asking LLMs for step-by-step methods helped me see exactly where errors (like network issues) were occurring.
* **Sprint Efficiency:** Successfully built, debugged, and deployed the entire system in a high-pressure window right before academic exams.
