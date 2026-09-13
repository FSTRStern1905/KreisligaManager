from __future__ import annotations

import os
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(r"E:\Kreisligamanager")

OUTPUT_ZIP = PROJECT_ROOT / "KreisligaManager_upload.zip"

INCLUDE_DIRS = [
    "src",
    "tests",
    "config",
    "assets",
    "docs",
]

INCLUDE_FILES = [
    "main.py",
    "requirements.txt",
    "README.md",
]

OPTIONAL_FILES = [
    "data/database/kreisligamanager.db",
]

EXCLUDE_DIR_NAMES = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "backups",
    "cache",
    "temp",
    "exports",
    "imports",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".log",
    ".tmp",
}


def should_exclude(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIR_NAMES:
            return True

    if path.suffix.lower() in EXCLUDE_EXTENSIONS:
        return True

    return False


def add_file_to_zip(
    zip_file: zipfile.ZipFile,
    file_path: Path,
) -> None:
    if not file_path.exists():
        return

    if should_exclude(file_path):
        return

    relative_path = file_path.relative_to(PROJECT_ROOT)

    print(f"Hinzufügen: {relative_path}")

    zip_file.write(
        file_path,
        arcname=str(relative_path),
    )


def add_directory_to_zip(
    zip_file: zipfile.ZipFile,
    directory: Path,
) -> None:
    if not directory.exists():
        return

    for root, dirs, files in os.walk(directory):
        root_path = Path(root)

        dirs[:] = [
            directory_name
            for directory_name in dirs
            if directory_name not in EXCLUDE_DIR_NAMES
        ]

        for file_name in files:
            file_path = root_path / file_name

            add_file_to_zip(
                zip_file,
                file_path,
            )


def create_project_zip() -> None:
    if not PROJECT_ROOT.exists():
        print(
            f"Projektordner nicht gefunden: "
            f"{PROJECT_ROOT}"
        )
        return

    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    with zipfile.ZipFile(
        OUTPUT_ZIP,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zip_file:

        for directory_name in INCLUDE_DIRS:
            directory = PROJECT_ROOT / directory_name

            add_directory_to_zip(
                zip_file,
                directory,
            )

        for file_name in INCLUDE_FILES:
            file_path = PROJECT_ROOT / file_name

            add_file_to_zip(
                zip_file,
                file_path,
            )

        for file_name in OPTIONAL_FILES:
            file_path = PROJECT_ROOT / file_name

            add_file_to_zip(
                zip_file,
                file_path,
            )

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)

    print()
    print("=" * 60)
    print("ZIP erfolgreich erstellt")
    print("=" * 60)
    print(f"Datei: {OUTPUT_ZIP}")
    print(f"Größe: {size_mb:.2f} MB")


if __name__ == "__main__":
    create_project_zip()