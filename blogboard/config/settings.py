from typing import Dict

from pydantic import BaseModel, Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseModel):

    API_KEY: str = Field(
        validation_alias=AliasChoices(
            'API_KEY',
            'api_key',
            'GROQ_API_KEY',
            'groq_api_key'
        )
    )

    MODEL_NAME: str = "gemma2-9b-it"

    TEMPERATURE: float = 1.0


class TagSettings(BaseModel):

    ml: Dict[str, str] = {
        "label": "Machine Learning",
        "shortLabel": "ML"
    }

    dl: Dict[str, str] = {
        "label": "Deep Learning",
        "shortLabel": "DL"
    }

    statistics: Dict[str, str] = {
        "label": "Statistics for AI",
        "shortLabel": "Stats"
    }

    nlp: Dict[str, str] = {
        "label": "Natural Language Processing",
        "shortLabel": "NLP"
    }

    cv: Dict[str, str] = {
        "label": "Computer Vision",
        "shortLabel": "CV"
    }

    genai: Dict[str, str] = {
        "label": "Generative AI",
        "shortLabel": "Gen AI"
    }

    ainews: Dict[str, str] = {
        "label": "AI News",
        "shortLabel": "AI News"
    }


class SupabaseSettings(BaseModel):

    URL: str

    KEY: str

    BUCKET_NAME: str = "blogboard"


class ContentAPISettings(BaseModel):

    TAVILY_API_KEY: str = ""

    GUARDIAN_API_KEY: str = ""

    UNSPLASH_API_KEY: str = ""


class Settings(BaseSettings):

    llm: LLMSettings

    tags: TagSettings = Field(
        default_factory=TagSettings
    )

    supabase: SupabaseSettings

    content: ContentAPISettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )


class _LazySettings:
    """Load Settings on first attribute access so imports do not require .env."""

    _cached: Settings | None = None

    def _load(self) -> Settings:
        if self._cached is None:
            object.__setattr__(self, "_cached", Settings())
        return self._cached

    def __getattr__(self, name: str):
        return getattr(self._load(), name)


app_settings = _LazySettings()