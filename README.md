# BlogBoard — Autonomous AI Blog Generator

An intelligent, fully automated blogging platform that autonomously researches, writes, validates, and publishes technical articles on AI and Machine Learning using multi-agent workflows powered by LangGraph.

## 🌟 Features

- **Multi-Agent Architecture**: Specialized agents for news research, tutorial generation, and content validation
- **Autonomous Workflow**: End-to-end automation from research to publication
- **Intelligent Domain Selection**: Automatically maps news to relevant tutorial categories
- **Quality Assurance**: Built-in validation with iterative revision loops
- **Cloud Storage**: Seamless integration with Supabase for article storage
- **Observability**: Integrated monitoring with Sentry and Opik
- **Static Frontend**: Clean, responsive web interface for article display

## 🏗️ Architecture

### Multi-Agent Pipeline

```
START
  ↓
News Agent (Research & Write AI News)
  ↓
News Validator
  ├─ Reject → News Agent (Revision)
  └─ Approve ↓
Tutorial Agent (Select Domain & Write Tutorial)
  ↓
Tutorial Validator
  ├─ Reject → Tutorial Agent (Revision)
  └─ Approve ↓
END (Publish to Supabase)
```

### Agents

1. **News Agent**: Researches latest AI developments using web search tools and generates news articles
2. **Tutorial Agent**: Analyzes news context, selects appropriate domain, and creates educational tutorials
3. **Validator Agent**: Reviews content quality, generates metadata, and manages revisions (max 3 attempts)

### Content Domains

- **ainews**: AI News articles
- **ml**: Machine Learning
- **dl**: Deep Learning
- **nlp**: Natural Language Processing
- **cv**: Computer Vision
- **genai**: Generative AI
- **statistics**: Statistics for AI

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended for dependency management)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/vamsikanugula-dev/auto-blogboard-generator.git
cd auto-blogboard-generator
```

2. **Create virtual environment**
```bash
uv venv
```

3. **Activate virtual environment**
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

4. **Install dependencies**
```bash
uv pip install -e .
```

### Configuration

Create a `.env` file in the project root:

```env
# LLM Settings
llm__api_key=your_groq_or_openai_api_key

# Supabase Settings
supabase__url=your_supabase_url
supabase__key=your_supabase_key
supabase__bucket_name=blogboard

# Content API Settings
content__tavily_api_key=your_tavily_key
content__guardian_api_key=your_guardian_key
content__unsplash_api_key=your_unsplash_key

# Opik Settings (Optional)
OPIK_API_KEY=your_opik_key
OPIK_PROJECT_NAME=blogboard

# Sentry (Optional)
SENTRY_DSN=your_sentry_dsn
```

## 📖 Usage

### Run Complete Pipeline

Generate both news and tutorial articles for today:
```bash
python blogboard/run.py
```

### Custom Date

Generate articles for a specific date:
```bash
python blogboard/run.py --date 2026-08-26
```

### Dry Run

Test the pipeline without making actual LLM calls or storage writes:
```bash
python blogboard/run.py --dry-run
```

### News Pipeline Only

Run only the AI news generation pipeline:
```bash
python blogboard/run.py --ainews
```

### View Frontend

Serve the static website locally:
```bash
python -m http.server 8000 --directory blogboard/web
```
Then visit `http://localhost:8000`

## 📂 Project Structure

```
BlogBoard-AI-Blog-Generator/
├── blogboard/
│   ├── agents/
│   │   ├── news_agent/          # AI news research & generation
│   │   ├── tutorial_agent/      # Tutorial domain selection & generation
│   │   └── validator_agent/     # Content validation & metadata
│   ├── config/
│   │   └── settings.py          # Configuration management
│   ├── graph/
│   │   ├── graph.py             # LangGraph workflow definition
│   │   └── state.py             # Shared state schema
│   ├── services/
│   │   ├── llm.py               # LLM service wrapper
│   │   ├── storage.py           # Supabase storage service
│   │   └── prompt_manager.py    # Prompt template management
│   ├── tools/
│   │   ├── tavily_search.py     # Tavily web search tool
│   │   └── guardian_search.py   # Guardian API search tool
│   ├── web/                     # Static frontend
│   └── run.py                   # Main entry point
├── .env.example                 # Environment variables template
├── pyproject.toml              # Project dependencies
└── README.md
```

## 🛠️ Tech Stack

- **LangGraph**: Stateful workflow orchestration
- **LangChain**: LLM framework and tool integration
- **Groq/OpenAI**: LLM inference (configurable)
- **Supabase**: Cloud storage for articles and metadata
- **Sentry**: Error tracking and monitoring
- **Opik**: LLM observability and tracing
- **Python 3.13+**: Core language

## 📊 Output

Articles are stored in Supabase with the following structure:

```
blogs/
├── ainews/
│   ├── articles.json
│   └── article-slug.md
├── ml/
│   ├── articles.json
│   └── article-slug.md
└── [other domains...]
```

Each `articles.json` contains metadata:
```json
{
  "id": "blogs/ml/article-slug.md",
  "category": "ml",
  "article_type": "tutorial",
  "topic": "Topic name",
  "title": "Article Title",
  "description": "Brief description",
  "date": "2026-08-26",
  "readTime": "5 min",
  "tags": ["ml"],
  "file": "blogs/ml/article-slug.md"
}
```

## 🔧 Advanced Configuration

### Custom LLM Model

Modify `blogboard/config/settings.py`:
```python
MODEL_NAME: str = "openai/gpt-4"  # or any compatible model
TEMPERATURE: float = 0.7
```

### Prompt Customization

The system uses a prompt manager that supports:
- Fallback prompts (hardcoded)
- Custom prompt templates (via external files)

Prompts are located in `blogboard/agents/*/prompts.py`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [LangGraph](https://github.com/langchain-ai/langgraph) for stateful workflow orchestration
- [LangChain](https://github.com/langchain-ai/langchain) for LLM framework
- [Groq](https://groq.com/) for blazing-fast inference
- [Supabase](https://supabase.com/) for storage infrastructure

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Made with ❤️ by the BlogBoard Team**
