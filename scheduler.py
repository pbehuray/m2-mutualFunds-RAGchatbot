#!/usr/bin/env python3
"""
Unified Data Pipeline Scheduler
Chains all phases: Scrape -> Extract -> Chunk -> Embed
Can run locally or be triggered by GitHub Actions.
Each step runs in its own subprocess to avoid import conflicts
and free memory between phases.
"""

import os
import sys
import json
import time
import logging
import subprocess
import traceback
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configure logging
# ---------------------------------------------------------------------------
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"scheduler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("scheduler")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.resolve()

RAW_HTML_DIR = PROJECT_ROOT / "phase_2" / "scraped-data" / "raw_html"
EXTRACTED_JSON_DIR = PROJECT_ROOT / "phase_2" / "scraped-data" / "extracted_json"
CHUNKED_JSON_DIR = PROJECT_ROOT / "phase_2" / "scraped-data" / "chunked_json"
VECTOR_DB_DIR = PROJECT_ROOT / "phase_3" / "vector_db"

# ---------------------------------------------------------------------------
# Subprocess runner
# ---------------------------------------------------------------------------
def _run_step(name: str, cwd: Path, script: str, extra_env: dict = None) -> dict:
    """
    Run a pipeline step in a fresh subprocess.

    Returns:
        {"status": "ok" | "failed", "returncode": int, "stdout": str, "stderr": str}
    """
    logger.info(f"--- Starting: {name} ---")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if extra_env:
        env.update(extra_env)

    cmd = [sys.executable, script]
    start = time.time()

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,  # 30 min per step
        )
    except subprocess.TimeoutExpired as exc:
        logger.error(f"{name} timed out after 30 minutes")
        return {
            "status": "failed",
            "returncode": -1,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "duration": 1800,
        }

    duration = round(time.time() - start, 2)

    if proc.returncode != 0:
        logger.error(f"{name} failed (exit {proc.returncode}) in {duration}s")
        logger.error(proc.stderr[-2000:] if proc.stderr else "No stderr")
        return {
            "status": "failed",
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "duration": duration,
        }

    logger.info(f"{name} completed in {duration}s")
    # Print last lines of stdout so user sees progress
    last_lines = "\n".join(proc.stdout.strip().splitlines()[-15:])
    if last_lines:
        for line in last_lines.splitlines():
            logger.info(f"  {line}")

    return {
        "status": "ok",
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "duration": duration,
    }


# ---------------------------------------------------------------------------
# Step wrappers
# ---------------------------------------------------------------------------
def run_scraper() -> dict:
    logger.info("=" * 60)
    logger.info("STEP 1/4: Web Scraping")
    logger.info("=" * 60)
    return _run_step(
        "Scraper",
        cwd=PROJECT_ROOT / "phase_2" / "2.1-web-scraping",
        script="scraper.py",
    )


def run_extraction() -> dict:
    logger.info("=" * 60)
    logger.info("STEP 2/4: Content Extraction")
    logger.info("=" * 60)
    return _run_step(
        "Content Extraction",
        cwd=PROJECT_ROOT / "phase_2" / "2.2-content-extraction",
        script="pipeline.py",
    )


def run_chunking() -> dict:
    logger.info("=" * 60)
    logger.info("STEP 3/4: Document Chunking")
    logger.info("=" * 60)
    return _run_step(
        "Chunking",
        cwd=PROJECT_ROOT / "phase_2" / "2.3-document-chunking",
        script="pipeline.py",
    )


def run_embedding() -> dict:
    logger.info("=" * 60)
    logger.info("STEP 4/4: Embedding Generation")
    logger.info("=" * 60)
    return _run_step(
        "Embedding",
        cwd=PROJECT_ROOT / "phase_3" / "3.3-embedding-generation",
        script="pipeline.py",
    )


# ---------------------------------------------------------------------------
# Main scheduler
# ---------------------------------------------------------------------------
def run_pipeline(skip_scrape: bool = False):
    """
    Run the full data pipeline end-to-end.

    Args:
        skip_scrape: If True, skip scraping and use existing raw HTML.
    """
    start_time = time.time()
    report = {
        "started_at": datetime.now().isoformat(),
        "steps": {},
        "status": "running",
    }

    try:
        if not skip_scrape:
            report["steps"]["scrape"] = run_scraper()
            if report["steps"]["scrape"]["status"] != "ok":
                raise RuntimeError("Scraper step failed")
        else:
            logger.info("Skipping scraping (--skip-scrape)")
            report["steps"]["scrape"] = {"status": "skipped"}

        report["steps"]["extract"] = run_extraction()
        if report["steps"]["extract"]["status"] != "ok":
            raise RuntimeError("Extraction step failed")

        report["steps"]["chunk"] = run_chunking()
        if report["steps"]["chunk"]["status"] != "ok":
            raise RuntimeError("Chunking step failed")

        report["steps"]["embed"] = run_embedding()
        if report["steps"]["embed"]["status"] != "ok":
            raise RuntimeError("Embedding step failed")

        report["status"] = "success"
        report["duration_seconds"] = round(time.time() - start_time, 2)

    except Exception as e:
        report["status"] = "failed"
        report["error"] = str(e)
        report["traceback"] = traceback.format_exc()
        report["duration_seconds"] = round(time.time() - start_time, 2)
        logger.error(f"Pipeline failed: {e}")

    finally:
        report["finished_at"] = datetime.now().isoformat()
        report_file = PROJECT_ROOT / "logs" / "scheduler_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Report saved to {report_file}")

    logger.info("=" * 60)
    if report["status"] == "success":
        logger.info("ALL STEPS COMPLETE")
    else:
        logger.info("PIPELINE FAILED")
    logger.info("=" * 60)
    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    skip_scrape = "--skip-scrape" in sys.argv
    report = run_pipeline(skip_scrape=skip_scrape)
    sys.exit(0 if report["status"] == "success" else 1)
