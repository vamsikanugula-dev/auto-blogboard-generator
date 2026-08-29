# BlogBoard — Autonomous AI Blog Generator

An intelligent, fully automated blogging platform that autonomously researches, writes, validates, and publishes high-quality technical articles on AI and Machine Learning using multi-agent workflows powered by LangGraph.

## 🌟 Features

- **Multi-Agent Architecture**: Specialized agents for news research, tutorial generation, and content validation
- **Autonomous Workflow**: End-to-end automation from research to publication
- **Advanced Research Tools**:
  - Tavily + The Guardian (general & journalistic news)
  - **arXiv** + **Semantic Scholar** (deep technical research papers)
- **Intelligent Domain Selection**: Automatically maps news to relevant tutorial categories
- **Rich Tutorial Generation**: Tutorials are enriched with real research papers from arXiv and Semantic Scholar
- **Robust Quality Control**:
  - Strong output cleaning (`strip_thinking`)
  - Hard format guards against reasoning/thinking traces
  - Tolerant Validator with fallback approval logic
  - Iterative revision loops (max 3 attempts)
- **Cloud Storage**: Seamless integration with Supabase for article storage
- **Observability**: Integrated monitoring with Sentry and Opik
- **Static Frontend**: Clean, responsive web interface for article display

## 🏗️ Architecture

### Multi-Agent Pipeline
START
↓
News Agent (Research with Tavily/Guardian + Write AI News)
↓
News Validator (Tolerant mode)
├─ Reject → News Agent (Revision)
└─ Approve ↓
Tutorial Agent
├─ Select Domain from News
├─ Research papers (arXiv + Semantic Scholar)
└─ Write rich educational Tutorial
↓
Tutorial Validator (Tolerant mode)
├─ Reject → Tutorial Agent (Revision)
└─ Approve ↓
END (Publish to Supabase)
text### Agents

1. **News Agent**  
   Researches latest AI developments using web search tools and generates clean news articles.

2. **Tutorial Agent**  
   - Analyzes news context and selects the best domain  
   - Performs additional research using **arXiv** and **Semantic Scholar**  
   - Generates in-depth educational tutorials enriched with real papers

3. **Validator Agent**  
   Reviews content quality, cleans thinking traces, generates SEO metadata, and manages revisions. Now includes **tolerant fallback logic** so good articles are not rejected just because of JSON parsing issues.

### Content Domains

- `ainews` — AI News articles  
- `ml` — Machine Learning  
- `dl` — Deep Learning  
- `nlp` — Natural Language Processing  
- `cv` — Computer Vision  
- `genai` — Generative AI  
- `statistics` — Statistics for AI  

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/vamsikanugula-dev/auto-blogboard-generator.git
cd auto-blogboard-generator

Create and activate virtual environment

Bashuv venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

Install dependencies

Bashuv sync
# or
uv pip install -e .
Configuration
Create a .env file in the project root:
env# LLM Settings
llm__api_key=your_groq_api_key
llm__model_name=llama-3.3-70b-versatile   # Recommended (avoid pure reasoning models)

# Supabase Settings
supabase__url=your_supabase_url
supabase__key=your_supabase_key
supabase__bucket_name=blogboard

# Content API Settings
content__tavily_api_key=your_tavily_key
content__guardian_api_key=your_guardian_key
content__semantic_scholar_api_key=your_semantic_scholar_key   # Optional but recommended

# Opik Settings (Optional)
OPIK_API_KEY=your_opik_key
OPIK_PROJECT_NAME=blogboard

# Sentry (Optional)
SENTRY_DSN=your_sentry_dsn
Note: arXiv requires no API key. Semantic Scholar works without a key but has higher rate limits with one.
📖 Usage
Run Complete Pipeline
Bashuv run python blogboard/run.py
Custom Date
Bashuv run python blogboard/run.py --date 2026-08-29
Dry Run
Bashuv run python blogboard/run.py --dry-run
News Only
Bashuv run python blogboard/run.py --ainews
View Frontend
Bashpython -m http.server 8000 --directory blogboard/web
Then open http://localhost:8000
📂 Project Structure
textBlogBoard-AI-Blog-Generator/
├── blogboard/
│   ├── agents/
│   │   ├── news_agent/               # AI news research & generation
│   │   ├── tutorial_agent/           # Domain selection + research + tutorial writing
│   │   └── validator_agent/          # Tolerant validation + metadata
│   ├── config/
│   │   └── settings.py
│   ├── graph/
│   │   ├── graph.py
│   │   └── state.py
│   ├── services/
│   │   ├── llm.py
│   │   ├── llm_output.py             # strip_thinking + JSON parser
│   │   ├── storage.py
│   │   └── prompt_manager.py
│   ├── tools/
│   │   ├── tavily_tool.py
│   │   ├── guardian_tool.py
│   │   ├── arxiv_tool.py             # ← New
│   │   └── semantic_scholar_tool.py  # ← New
│   ├── web/
│   └── run.py
├── pyproject.toml
├── uv.lock
└── README.md
🛠️ Tech Stack

LangGraph — Stateful multi-agent orchestration
LangChain — Tool calling & LLM framework
Groq — Fast LLM inference
arXiv API + Semantic Scholar API — Research paper retrieval
Tavily + The Guardian — News research
Supabase — Article & metadata storage
uv — Fast dependency management
Sentry + Opik — Observability

📊 Output Structure
textblogs/
├── ainews/
│   ├── articles.json
│   └── some-news-slug.md
├── nlp/
│   ├── articles.json
│   └── emerging-concepts-in-nlp.md
└── ...
🔧 Key Improvements (Recent)

Added arXiv and Semantic Scholar tools for deep technical research
Tutorial Agent now automatically researches relevant papers
Stronger strip_thinking to remove <think> and reasoning traces
Hard format guards in both News and Tutorial agents
More tolerant Validator (no longer rejects good articles due to JSON failures)
Better prompts that force clean Markdown output
Emergency fallback content so articles are never completely empty

🤝 Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.
📝 License
This project is licensed under the MIT License.

Made with ❤️ for the AI community