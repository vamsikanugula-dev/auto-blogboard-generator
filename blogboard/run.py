import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Windows consoles default to cp1252 and crash on emoji / non-ASCII model output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Project paths ─────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent
ROOT_DIR = BACKEND_DIR.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# ── Load .env ─────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv

    env_path = ROOT_DIR / ".env"
    load_dotenv(dotenv_path=env_path)

except ImportError:
    pass


# ── Sentry ───────────────────────────────────────────────────────────────────
import os
import sentry_sdk

sentry_dsn = os.getenv("SENTRY_DSN")

if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        _experiments={
            "continuous_profiling_auto_start": True,
        },
    )


# ── Import compiled graph ─────────────────────────────────────────────────────
from blogboard.graph.graph import graph


# ─────────────────────────────────────────────────────────────────────────────
# Date helper
# ─────────────────────────────────────────────────────────────────────────────

def today_ist() -> str:
    """Return today's date in Indian Standard Time."""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m-%d")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():

    parser = argparse.ArgumentParser(
        description="BlogBoard — LangGraph Daily Article Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples
--------
  # Run the complete daily pipeline:
  python blogboard/run.py

  # Generate for a specific date:
  python blogboard/run.py --date 2026-08-16

  # Dry run:
  python blogboard/run.py --dry-run

  # Run the news pipeline explicitly for testing:
  python blogboard/run.py --ainews

  # Test AI News pipeline without production writes:
  python blogboard/run.py --ainews --dry-run
        """,
    )

    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Target date in YYYY-MM-DD format (default: today in IST)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview mode: skip actual LLM calls/file writes where supported",
    )

    parser.add_argument(
        "--ainews",
        action="store_true",
        help="Explicitly start the AI News pipeline for testing",
    )

    args = parser.parse_args()

    date_str = args.date or today_ist()
    dry_run = args.dry_run

    # ─────────────────────────────────────────────────────────────────────────
    # Banner
    # ─────────────────────────────────────────────────────────────────────────

    print("\n" + "=" * 55)
    print("  BlogBoard — LangGraph Daily Article Generator")
    print(f"  Date    : {date_str}")
    print(f"  Dry run : {dry_run}")
    print("=" * 55)

    # ─────────────────────────────────────────────────────────────────────────
    # Initial state
    # ─────────────────────────────────────────────────────────────────────────

    initial_state = {
        "date": date_str,
        "dry_run": dry_run,
    }

    # -------------------------------------------------------------------------
    # AI NEWS TEST MODE
    #
    # Normally the graph starts the NewsAgent itself.
    #
    # When --ainews is provided, we explicitly tell the graph that this
    # execution is an AI News run.
    # -------------------------------------------------------------------------

    if args.ainews:

        initial_state["domain"] = "ainews"
        initial_state["article_type"] = "ainews"
        initial_state["news_only"] = True

        print("  Mode    : AI News pipeline")

    else:

        print("  Mode    : Daily News + Tutorial pipeline")

    # ─────────────────────────────────────────────────────────────────────────
    # Execute graph
    # ─────────────────────────────────────────────────────────────────────────

    config = {
        "configurable": {
            "thread_id": f"blogboard-{date_str}"
        }
    }

    try:

        final_state = graph.invoke(
            initial_state,
            config=config,
        )

    except Exception as exc:

        print("\n" + "=" * 55)
        print("  Pipeline failed.")
        print(f"  Error: {exc}")
        print("=" * 55)

        raise

    # ─────────────────────────────────────────────────────────────────────────
    # Final summary
    # ─────────────────────────────────────────────────────────────────────────

    print("\n" + "=" * 55)

    # ─────────────────────────────────────────────────────────────────────────
    # DRY RUN SUMMARY
    # ─────────────────────────────────────────────────────────────────────────

    if dry_run:

        print("  [DRY RUN] Pipeline completed.")
        print("  No production files should have been written.")

        domain = final_state.get("domain", "?")
        article_type = final_state.get("article_type", "?")
        topic = final_state.get("topic", "?")
        slug = final_state.get("slug", "?")

        print(f"  Chosen Domain : {domain}")
        print(f"  Article Type  : {article_type}")
        print(f"  Chosen Topic  : {topic}")

        if slug != "?":

            print("  Would generate:")
            print(f"    -> blogs/{domain}/{slug}.md")
            print(f"    -> blogs/{domain}/articles.json")

    # ─────────────────────────────────────────────────────────────────────────
    # NORMAL RUN SUMMARY
    # ─────────────────────────────────────────────────────────────────────────

    else:

        domain = final_state.get("domain", "?")
        article_type = final_state.get("article_type", "?")
        title = final_state.get("title", "?")
        md_path = final_state.get("md_path", "?")
        read_time = final_state.get("read_time", "?")

        if final_state.get("skipped"):
            print("  Pipeline stopped without publishing.")
            print(f"  Domain      : {domain}")
            print(f"  Article Type: {article_type}")
        else:
            print("  Pipeline completed successfully.")
            print(f"  Final Title : {title}")
            print(f"  Domain      : {domain}")
            print(f"  Article Type: {article_type}")
            print(f"  Read time   : {read_time}")
            print(f"  File        : {md_path}")

    print("=" * 55)
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()