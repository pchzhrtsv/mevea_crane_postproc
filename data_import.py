from pathlib import Path
import shutil


def import_results(source_dir: Path, target_dir: Path, mask=None):
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    files = list(source_dir.glob("*.txt"))
    c = 0
    for source_file in files:
        if not mask or mask in source_file.name:
            target_file = target_dir / source_file.name

            shutil.copy2(source_file, target_file)
            c+=1
    print(f"Imported {c} files")