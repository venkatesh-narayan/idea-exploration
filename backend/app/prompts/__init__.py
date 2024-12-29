from pathlib import Path
from typing import Dict


def load_prompts() -> Dict[str, Dict[str, str]]:
    """
    Load .txt prompts under /system and /user.
    """
    prompts = {"system": dict(), "user": dict()}
    prompts_dir = Path(__file__).parent

    def load_prompts_from_directory(base_dir: Path) -> dict:
        d = dict()
        for item in base_dir.iterdir():
            if item.is_file() and item.suffix == ".txt":
                d[item.stem] = item.read_text().strip()
        return d

    # System
    system_dir = prompts_dir / "system"
    if system_dir.exists():
        prompts["system"] = load_prompts_from_directory(system_dir)

    # User
    user_dir = prompts_dir / "user"
    if user_dir.exists():
        prompts["user"] = load_prompts_from_directory(user_dir)

    return prompts


PROMPTS = load_prompts()
