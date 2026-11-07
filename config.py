"""
Configuration module for LessonForge.
Handles environment variables, default settings, and runtime config updates.
"""
from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env", override=False)


@dataclass
class AppConfig:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "").strip()
    google_books_api_key: str = os.getenv("GOOGLE_BOOKS_API_KEY", "").strip()
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "").strip()
    data_dir: Path = ROOT_DIR / os.getenv("LESSONFORGE_DATA_DIR", "data/lessons")
    environment: str = os.getenv("ENVIRONMENT", "development").strip()

    def __post_init__(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def has_gemini_key(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_tavily_key(self) -> bool:
        return bool(self.tavily_api_key)

    @property
    def has_youtube_key(self) -> bool:
        return bool(self.youtube_api_key)

    @property
    def has_google_books_key(self) -> bool:
        return bool(self.google_books_api_key)


# Global singleton configuration
config = AppConfig()


def reload_config():
    """Reload configuration from disk and environment."""
    load_dotenv(ROOT_DIR / ".env", override=True)
    global config
    config = AppConfig(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
        tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip(),
        google_books_api_key=os.getenv("GOOGLE_BOOKS_API_KEY", "").strip(),
        youtube_api_key=os.getenv("YOUTUBE_API_KEY", "").strip(),
        data_dir=ROOT_DIR / os.getenv("LESSONFORGE_DATA_DIR", "data/lessons"),
        environment=os.getenv("ENVIRONMENT", "development").strip(),
    )
    return config


def update_env_file(key: str, value: str):
    """Safely update or add a key in .env file."""
    env_path = ROOT_DIR / ".env"
    lines = []
    found = False
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    os.environ[key] = value
    reload_config()
