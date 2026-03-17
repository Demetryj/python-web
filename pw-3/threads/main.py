from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from pathlib import Path

import logging
import shutil
import sys


BASE_DIR = Path(__file__).resolve().parent


def collect_folders(source: Path) -> list[Path]:
    """Recursively collect all nested directories starting from source."""
    folders: list[Path] = []
    
    for item in source.iterdir():
        try:
            if item.is_dir():
                folders.append(item)
                inner_dir = collect_folders(item)
                if len(inner_dir):
                    folders.extend(inner_dir)
        except OSError as err:
            logging.error("Cannot read folder %s: %s", source, err)
            
    return folders


def copy_file(folder_path: Path, destination_dir: Path) -> None:
    """Copy files from one folder into destination subfolders grouped by extension."""
    try:
        for item in folder_path.iterdir():
            if item.is_file():
                suffix = item.suffix.lower().lstrip(".")
                ext_folder = suffix if suffix else "no_extension"
                target_folder = destination_dir / ext_folder
                
                try:
                    target_folder.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_folder / item.name)
                except OSError as err:
                    logging.error("Cannot copy %s: %s", item, err)
    except OSError as err:
        logging.error("Cannot scan folder %s: %s", folder_path, err)


def parse_args(argv: list[str]) -> tuple[Path, Path]:
    """Parse CLI arguments and return validated source and destination paths."""
    if len(argv) < 2:
        raise ValueError("Usage: py main.py <source_dir> [destination_dir]")

    source = Path(argv[1]).resolve()
    destination = Path(argv[2]).resolve() if len(argv) > 2 else (BASE_DIR / "dist")

    if not source.exists() or not source.is_dir():
        raise ValueError(f"Source directory does not exist: {source}")

    destination.mkdir(parents=True, exist_ok=True)

    return source, destination


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s %(message)s")

    try:
        source_dir, destination_dir = parse_args(sys.argv)
        folders = [source_dir, *collect_folders(source_dir)]
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(copy_file, folders, repeat(destination_dir))) 

        logging.info("Finished")
    except ValueError as err:
        print(err)
        
