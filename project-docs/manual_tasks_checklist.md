# Manual Tasks & Offline Checklist

This document tracks the offline, manual, and academic tasks that require human intervention (e.g., Google Colab, Cloud Platforms, Academic Reports). 

## 🔄 In Progress
- [/] **Phase 1 AI Training (Colab):** Run the Supervised Fine-Tuning (SFT) script on Google Colab to generate the initial `best_model.pt` base model.
- [/] **Phase 2 AI Training (Colab - DPO):** Once the base model is trained and we have generated feedback on the UI, run the DPO script on Colab to personalize the AI weights.

## ❌ To Do (Incomplete)
- [ ] **AI Model Evaluation:** Once training finishes, calculate the perplexity/BLEU scores and manually evaluate 20 sample outputs to prove the model works.
- [ ] **Load Testing Report:** Write a Markdown or PDF report detailing the results of the 10,000 concurrent user load test (Week 13 milestone). 
- [ ] **Cross-Laptop Testing (Integration):** Have 3 other teammates follow the `network-setup.md` instructions to connect their laptops to the main server for the 4-laptop cluster presentation.
- [ ] **Cloud Server Rental:** Purchase a domain name (e.g., `promptpolisher.dev`) and rent a cloud VPS (like DigitalOcean, AWS EC2, or Linode) so we can deploy the app to the internet.
- [ ] **Architecture Documentation:** Write the final System Design Document, including network topology diagrams, technology decision rationale, and trade-offs.
- [ ] **Record Demo Video (5 minutes):** Record the final academic presentation video demonstrating:
  - User Registration & Onboarding
  - Setting AI Preferences
  - Generating optimized prompts
  - Showing RAG memory (chat history)
  - Providing Thumbs Up/Down feedback

## ✅ Completed
- [x] **Database Seeding & Export:** Reset the corrupted local database, manually seeded it with fake user feedback, and successfully exported the `dpo_dataset.jsonl` file.
- [x] **Load Test Baseline Scripting:** Ran the local Locust/Python simulation scripts to hit the backend with simulated concurrent users and identified bottlenecks.
- [x] **Network Setup Documentation:** Drafted the initial `network-setup.md` guide for the multi-laptop architecture.
