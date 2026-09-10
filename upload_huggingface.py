from pathlib import Path
import argparse

from datasets import Dataset, DatasetDict, Features, Image, Value
from huggingface_hub import login


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_split(split_dir):
    """Load PNG images and their matching MD transcriptions."""

    records = []

    image_files = sorted(split_dir.glob("*.png"))

    for image_path in image_files:
        md_path = image_path.with_suffix(".md")

        if not md_path.exists():
            print(f"WARNING: Missing transcription for {image_path.name}")
            continue

        text = md_path.read_text(encoding="utf-8").strip()

        if not text:
            print(f"WARNING: Empty transcription for {md_path.name}")
            continue

        records.append(
            {
                "image": str(image_path),
                "text": text,
                "filename": image_path.name,
            }
        )

    features = Features(
        {
            "image": Image(),
            "text": Value("string"),
            "filename": Value("string"),
        }
    )

    return Dataset.from_list(records, features=features)


def build_script_dataset(script):
    """Build a DatasetDict containing train, validation and test."""

    script_dir = OUTPUT_DIR / script

    if not script_dir.exists():
        raise FileNotFoundError(
            f"Dataset directory not found:\n{script_dir}"
        )

    print(f"\nPreparing {script} dataset...")

    train = load_split(script_dir / "train")
    validation = load_split(script_dir / "validation")
    test = load_split(script_dir / "test")

    dataset = DatasetDict(
        {
            "train": train,
            "validation": validation,
            "test": test,
        }
    )

    print(f"Train      : {len(train)}")
    print(f"Validation : {len(validation)}")
    print(f"Test       : {len(test)}")
    print(f"Total      : {len(train) + len(validation) + len(test)}")

    return dataset


def upload_script(script, repo_id):
    """Upload one script as a separate Hugging Face dataset subset."""

    dataset = build_script_dataset(script)

    print(f"\nUploading {script} to {repo_id}...")

    dataset.push_to_hub(
        repo_id=repo_id,
        config_name=script,
    )

    print(f"✓ {script} uploaded successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Upload synthetic manuscript dataset to Hugging Face."
    )

    parser.add_argument(
        "--repo-id",
        required=True,
        help="Hugging Face dataset repository, e.g. username/synthetic-manuscript-generator",
    )

    parser.add_argument(
        "--script",
        choices=["devanagari", "modi", "sharada", "all"],
        default="all",
        help="Script subset to upload.",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("HUGGING FACE DATASET UPLOADER")
    print("=" * 60)

    print("\nLogging in to Hugging Face...")
    login()

    if args.script == "all":
        scripts = ["devanagari", "modi", "sharada"]
    else:
        scripts = [args.script]

    for script in scripts:
        upload_script(
            script=script,
            repo_id=args.repo_id,
        )

    print("\n" + "=" * 60)
    print("✓ HUGGING FACE UPLOAD COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()