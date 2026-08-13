import argparse
import zipfile
from pathlib import Path


EXCLUDED_SUFFIXES = {".zip", ".pyc"}
EXCLUDED_PARTS = {"__pycache__"}


def should_skip(path: Path) -> bool:
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    return False


def build_zip(source_dir: Path, output_zip: Path) -> int:
    source_dir = source_dir.resolve()
    output_zip = output_zip.resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    files = [
        path for path in source_dir.rglob("*")
        if path.is_file() and not should_skip(path.relative_to(source_dir))
    ]

    if not files:
        raise SystemExit(f"No files to package from {source_dir}")

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(files):
            rel = path.relative_to(source_dir)
            arcname = Path(source_dir.name, rel).as_posix()
            zf.write(path, arcname)

    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Kodi-safe addon zip.")
    parser.add_argument("source_dir")
    parser.add_argument("output_zip")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output_zip = Path(args.output_zip)
    count = build_zip(source_dir, output_zip)
    print(f"Built {output_zip} with {count} files")


if __name__ == "__main__":
    main()