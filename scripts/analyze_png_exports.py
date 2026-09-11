"""Analyze image artifacts from an FGA Lightroom PNG matrix run."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
HASH_BUFFER_SIZE = 1024 * 1024
EXIFTOOL_FIELDS = (
    "-FileName",
    "-Directory",
    "-FileType",
    "-FileSize#",
    "-ImageWidth",
    "-ImageHeight",
    "-BitDepth",
    "-ColorType",
    "-ColorSpace",
    "-ICC_Profile:ProfileDescription",
    "-Orientation",
)


def file_sha2_256(path: Path) -> str:
    """Return the lowercase SHA2-256 digest of one file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(HASH_BUFFER_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def exiftool_metadata(
    image_files: list[Path],
    exiftool: Path | None,
) -> dict[str, dict[str, object]]:
    """Read the selected structural metadata fields when ExifTool is available."""

    if exiftool is None:
        return {}

    completed = subprocess.run(  # noqa: S603 - executable is resolved from PATH
        [
            str(exiftool),
            "-json",
            "-n",
            *EXIFTOOL_FIELDS,
            *(str(path) for path in image_files),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        message = f"ExifTool failed with exit code {completed.returncode}."
        raise RuntimeError(message)

    decoded = cast("object", json.loads(completed.stdout))
    if not isinstance(decoded, list):
        message = "ExifTool returned JSON that was not an array."
        raise TypeError(message)

    metadata_by_path: dict[str, dict[str, object]] = {}
    for item in cast("list[object]", decoded):
        if not isinstance(item, dict):
            message = "ExifTool returned a non-object metadata entry."
            raise TypeError(message)
        entry = cast("dict[str, object]", item)
        source_file = entry.get("SourceFile")
        if not isinstance(source_file, str):
            message = "ExifTool metadata omitted its SourceFile string."
            raise TypeError(message)
        metadata_by_path[str(Path(source_file).resolve()).casefold()] = entry
    return metadata_by_path


def analyze_run_directory(
    run_directory: Path,
    *,
    exiftool: Path | None,
) -> dict[str, object]:
    """Build the JSON-compatible analysis for one matrix run."""

    resolved_run_directory = run_directory.resolve()
    if not resolved_run_directory.is_dir():
        message = f"Run directory does not exist: '{resolved_run_directory}'."
        raise ValueError(message)

    manifest_path = resolved_run_directory / "manifest.json"
    if not manifest_path.is_file():
        message = f"The run directory does not contain manifest.json: '{resolved_run_directory}'."
        raise ValueError(message)

    image_files = sorted(
        (
            path
            for path in resolved_run_directory.rglob("*")
            if path.is_file() and path.suffix.casefold() in IMAGE_EXTENSIONS
        ),
        key=str,
    )
    if not image_files:
        message = f"No PNG or JPEG exports found in '{resolved_run_directory}'."
        raise ValueError(message)

    metadata_by_path = exiftool_metadata(image_files, exiftool)
    images: list[dict[str, object]] = []
    for image_file in image_files:
        resolved_image = image_file.resolve()
        images.append(
            {
                "relativePath": str(resolved_image.relative_to(resolved_run_directory)),
                "fullPath": str(resolved_image),
                "fileSizeBytes": resolved_image.stat().st_size,
                "SHA2-256": file_sha2_256(resolved_image),
                "metadata": metadata_by_path.get(str(resolved_image).casefold()),
            }
        )

    return {
        "schemaVersion": 1,
        "analyzedAt": datetime.now(UTC).isoformat(),
        "runDirectory": str(resolved_run_directory),
        "manifestPath": str(manifest_path),
        "exifToolAvailable": exiftool is not None,
        "imageCount": len(image_files),
        "images": images,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-directory",
        required=True,
        type=Path,
        help="Directory containing the Lightroom matrix manifest and exports.",
    )
    return parser


def main() -> None:
    """Analyze a run directory and write analysis.json beside its manifest."""

    arguments = build_argument_parser().parse_args()
    exiftool_command = shutil.which("exiftool")
    exiftool = Path(exiftool_command) if exiftool_command else None
    if exiftool is None:
        print("ExifTool was not found; the report will contain filesystem and hash data only.")

    analysis = analyze_run_directory(arguments.run_directory, exiftool=exiftool)
    analysis_path = arguments.run_directory.resolve() / "analysis.json"
    analysis_path.write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Analyzed {analysis['imageCount']} image(s): {analysis_path}")


if __name__ == "__main__":
    main()
