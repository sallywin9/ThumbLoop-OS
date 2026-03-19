from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "08_config" / "settings.env"


def load_env_file(path: Path) -> dict:
    config = {}
    if not path.exists():
        return config

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        config[key.strip()] = value.strip()
    return config


ENV = load_env_file(ENV_PATH)


def get_path(env_key: str, default: str) -> Path:
    return BASE_DIR / ENV.get(env_key, default)


INPUT_DIR = get_path("INPUT_DIR", "01_input")
EXPERIMENT_DIR = get_path("EXPERIMENT_DIR", "03_experiment")
OUTPUT_DIR = get_path("OUTPUT_DIR", "04_output/thumbnails")
ASSETS_DIR = get_path("ASSETS_DIR", "05_assets")
LOG_DIR = get_path("LOG_DIR", "06_logs")

OPERATIONS_CSV = INPUT_DIR / ENV.get("OPERATIONS_CSV", "thumbnail_operations.csv")
EXPERIMENTS_CSV = EXPERIMENT_DIR / ENV.get("EXPERIMENTS_CSV", "thumbnail_experiments.csv")

FONT_PATH = ASSETS_DIR / ENV.get("FONT_FILE", "fonts/NanumGothicBold.ttf")
DEFAULT_BG = ASSETS_DIR / ENV.get("DEFAULT_BG", "backgrounds/default.jpg")

DEFAULT_STYLE = ENV.get("DEFAULT_STYLE", "default")
DEFAULT_LAYOUT = ENV.get("DEFAULT_LAYOUT", "bottom_big")