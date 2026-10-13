# Capstone Project 2: Agentic RAG for Enterprise Customer Support

**Author:** [Your name]  
**Date:** [Submission date]

## 1. Problem statement and use case
Describe the customer-support problem, expected users, and how grounded answers reduce repetitive support work.

## 2. Dataset and knowledge base
- Source: synthetic customer-support FAQ/policy knowledge base created for this capstone.
- Number of chunks: [fill in verified count]
- Chunking strategy and metadata: [describe from Phase 1]
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector store: FAISS

## 3. Retrieval design
Explain semantic retrieval, BM25 keyword retrieval, and hybrid rank fusion. Add example queries and retrieved source IDs. Mention whether a reranker was implemented or left as future work.

## 4. Baseline RAG and evaluation
Summarize Phase 3 results from `phase3_baseline_evaluation.csv` and `phase3_rouge_scores.csv`. Include ROUGE/BLEU/relevance only if actually calculated. Discuss manual relevance review and limitations of a five-question evaluation set.

## 5. Agentic workflow
Describe LangGraph nodes, planner, retrieval tool, answer generation, validation, retry/query rewrite, state/memory, and workflow traces. Add the LangGraph diagram and Phase 4 evaluation results.

## 6. Feedback loop
Explain thumbs-up/thumbs-down feedback, saved feedback fields, validation failures, retry limit, and how feedback could inform future tuning. State clearly what is implemented versus proposed.

## 7. API and user interface
Describe `GET /health`, `POST /query`, and `POST /feedback`. Include one real request/response example from `/docs` and screenshots of Streamlit.

## 8. CI/CD and deployment validation
Describe GitHub Actions triggers, Python version, Ruff checks, pytest, manual deployed-health validation, secret configuration, and rollback procedure. Include a passing Actions screenshot. State which hosting provider was used, if any; do not claim a public deployment if only tested locally.

## 9. Results and limitations
Compare baseline and agentic outputs using actual metrics and manual review. Discuss local model latency, synthetic/small corpus, source-grounding limits, and deployment/security limitations.

## 10. Future work
Potential work: larger verified corpus, reranking, richer relevance/faithfulness metrics, authentication, monitoring, human escalation, and provider-specific automated deployment.

## 11. Conclusion
Summarize what works, how to reproduce it, and what remains.

## 12. References
List model cards, library documentation, and any external dataset/document sources actually used.
