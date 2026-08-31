# BlogBoard — Autonomous AI Blog Generator

An intelligent multi-agent system that **autonomously researches, writes, validates, and publishes** high-quality technical articles on Artificial Intelligence and Machine Learning.

Built with **LangGraph**, **LangChain**, and powered by modern research tools (arXiv, Semantic Scholar, Tavily, The Guardian).

---

## 🌟 Key Features

- **Multi-Agent Architecture** using LangGraph
  - News Agent → researches latest AI developments
  - Tutorial Agent → selects domain + writes deep educational content
  - Validator Agent → quality control + revision loops
- **Advanced Research Tools**
  - Tavily + The Guardian (news)
  - arXiv + Semantic Scholar (research papers)
- **Intelligent Domain Selection** (ML, DL, NLP, CV, GenAI, Statistics, AI News)
- **Robust Quality Control**
  - Thinking-trace removal
  - Format guards
  - Tolerant validation with fallback logic
  - Up to 3 revision attempts
- **Cloud Storage** with Supabase
- **Observability** with Sentry + Opik
- **Static Frontend** for viewing generated articles

---

## 🏗️ Architecture

```text
START
  ↓
News Agent (Research + Write AI News)
  ↓
News Validator
  ├─ Reject → News Agent (Revision)
  └─ Approve
       ↓
Tutorial Agent
  ├─ Select Domain
  ├─ Research papers (arXiv + Semantic Scholar)
  └─ Write Tutorial
       ↓
Tutorial Validator
  ├─ Reject → Tutorial Agent (Revision)
  └─ Approve
       ↓
Publish to Supabase → END
Agents
```
AgentResponsibilityNews AgentResearch latest AI news and generate clean articlesTutorial AgentSelect domain + research papers + write tutorialsValidator AgentQuality check, SEO metadata, revision management

```text
📂 Project Structure
textauto-blogboard-generator/
├── blogboard/
│   ├── agents/
│   │   ├── news_agent/
│   │   ├── tutorial_agent/
│   │   └── validator_agent/
│   ├── config/
│   ├── graph/
│   ├── services/
│   ├── tools/
│   ├── web/
│   └── run.py
├── storage/blogs/               # Generated articles
├── pyproject.toml
├── uv.lock
└── README.md
```

🛠️ Tech Stack

Orchestration: LangGraph + LangChain
LLM: Groq (Llama 3.3 70B recommended)
Research Tools: arXiv, Semantic Scholar, Tavily, The Guardian
Storage: Supabase
Observability: Sentry + Opik
Package Manager: uv


🚀 Getting Started
Prerequisites

Python 3.13+
uv

Installation
Bashgit clone https://github.com/vamsikanugula-dev/auto-blogboard-generator.git
cd auto-blogboard-generator

uv venv
source .venv/bin/activate      # Linux/Mac
# or
.venv\Scripts\activate         # Windows

uv sync
Configuration
Create a .env file:
envllm__api_key=your_groq_api_key
llm__model_name=llama-3.3-70b-versatile

supabase__url=your_supabase_url
supabase__key=your_supabase_key
supabase__bucket_name=blogboard

content__tavily_api_key=your_tavily_key
content__guardian_api_key=your_guardian_key
content__semantic_scholar_api_key=your_semantic_scholar_key   # Optional

📖 Usage
Bash# Run complete pipeline
uv run python blogboard/run.py

# Custom date
uv run python blogboard/run.py --date 2026-08-29

# Dry run
uv run python blogboard/run.py --dry-run

# Generate only AI News
uv run python blogboard/run.py --ainews
View Frontend
Bashpython -m http.server 8000 --directory blogboard/web
Then open → http://localhost:8000

```text
📊 Output Structure
textstorage/blogs/
├── ainews/
│   ├── articles.json
│   └── some-news-slug.md
├── ml/
├── dl/
├── nlp/
├── cv/
├── genai/
└── statistics/
```

🔧 Recent Improvements

Added arXiv + Semantic Scholar tools for deeper research
Stronger strip_thinking to remove reasoning traces
Hard format guards
More tolerant Validator (reduces false rejections)
Emergency fallback content
Better prompts for clean Markdown output


📝 License
This project is licensed under the MIT License.

Author: Vamsi Kanugula

GitHub · LinkedIn
text---
