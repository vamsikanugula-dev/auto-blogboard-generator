import json

from typing import Optional, List, Dict, Any

from supabase import create_client

from blogboard.config.settings import app_settings


class SupabaseStorageService:
    """
    Storage service for BlogBoard.

    Uses Supabase Storage to store and retrieve
    generated blog articles and article metadata.
    """

    def __init__(self):
        """Initialize Supabase Storage."""

        self.supabase = create_client(
            app_settings.supabase.URL,
            app_settings.supabase.KEY
        )

        self.bucket_name = (
            app_settings.supabase.BUCKET_NAME.strip()
        )

        print("  [Storage] Supabase")

    def get_object(self, key: str) -> Optional[str]:
        """Fetch raw string data from Supabase Storage."""

        try:
            response = (
                self.supabase
                .storage
                .from_(self.bucket_name)
                .download(key)
            )

            return response.decode("utf-8")

        except Exception as e:
            print(
                f"[ERROR] Supabase error in get_object "
                f"({key}): {e}"
            )
            return None

    def put_object(
        self,
        key: str,
        data: str,
        content_type: str = "text/plain"
    ) -> bool:
        """Upload string data to Supabase Storage."""

        try:
            self.supabase.storage.from_(
                self.bucket_name
            ).upload(
                path=key,
                file=data.encode("utf-8"),
                file_options={
                    "content-type": content_type,
                    "upsert": "true"
                }
            )

            print(
                f"  [Storage] Uploaded to Supabase: "
                f"{self.bucket_name}/{key}"
            )

            return True

        except Exception as e:
            print(
                f"[ERROR] Failed to upload "
                f"{key} to Supabase: {e}"
            )

            return False

    def get_json(
        self,
        key: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch and parse JSON from Supabase Storage."""

        data = self.get_object(key)

        if data:
            try:
                return json.loads(data)

            except json.JSONDecodeError:
                print(
                    f"[WARN] Failed to decode JSON from {key}. "
                    "Starting fresh."
                )
                return []

        return []

    def get_articles_json(
        self,
        domain: str
    ) -> List[Dict[str, Any]]:
        """Fetch articles registry for a domain."""

        return self.get_json(
            f"blogs/{domain}/articles.json"
        ) or []

    def save_articles_json(
        self,
        domain: str,
        articles: List[Dict[str, Any]]
    ) -> bool:
        """Save articles registry for a domain."""

        json_str = json.dumps(
            articles,
            indent=2,
            ensure_ascii=False
        )

        return self.put_object(
            f"blogs/{domain}/articles.json",
            json_str,
            content_type="application/json"
        )

    def get_recent_history(
        self,
        domain: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Fetch recent articles for context."""

        articles = self.get_articles_json(domain)

        sorted_articles = sorted(
            articles,
            key=lambda x: x.get("date", ""),
            reverse=True
        )

        recent = sorted_articles[:limit]

        return [
            {
                "title": a.get("title"),
                "topic": a.get("topic"),
                "subtopics": a.get("subtopics", "")
            }
            for a in recent
        ]

    def get_all_domains_last_updated(
        self
    ) -> Dict[str, str]:
        """Return latest update dates for all domains."""

        latest_dates = {}

        for domain_slug in app_settings.tags.model_dump().keys():

            articles = self.get_articles_json(domain_slug)

            if not articles:
                latest_dates[domain_slug] = "Never"

            else:
                sorted_articles = sorted(
                    articles,
                    key=lambda x: x.get("date", ""),
                    reverse=True
                )

                latest_dates[domain_slug] = (
                    sorted_articles[0].get(
                        "date",
                        "Unknown"
                    )
                )

        return latest_dates