#!/usr/bin/env python3
import csv, sys, pathlib

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.cwd()
CSV_DIR = ROOT / "csv"

CSV_FILES = [
    "spreadsheet_preference.csv",
    "practice_pairs.csv",
    "interpret_main.csv",
    "interpret_practice.csv",
]

# mapping rules
def map_audio(path: str) -> str:
    path = path.strip()
    if not path: return path
    # drop any leading "audio/" and re-root under audio_opt/
    name = pathlib.Path(path)
    return str(pathlib.Path("audio_opt") / name.with_suffix(".mp3").name) if name.parent == pathlib.Path("") \
        else str(pathlib.Path("audio_opt") / name.name if name.parent.name == "audio" else pathlib.Path("audio_opt") / name)

def map_image(path: str) -> str:
    path = path.strip()
    if not path: return path
    name = pathlib.Path(path)
    # swap to images_opt and webp
    new_name = name.with_suffix(".webp").name if name.suffix.lower() in [".png", ".jpg", ".jpeg"] else name.name
    return str(pathlib.Path("images_opt") / new_name) if name.parent == pathlib.Path("") \
        else str(pathlib.Path("images_opt") / name.name if name.parent.name == "images" else pathlib.Path("images_opt") / name)

def rewrite_file(fn: str):
    src = CSV_DIR / fn
    dst = CSV_DIR / (src.stem + "_opt.csv")
    if not src.exists():
        print(f"[WARN] Missing CSV: {src}")
        return
    with src.open(newline='', encoding="utf-8") as f, dst.open("w", newline='', encoding="utf-8") as g:
        reader = csv.DictReader(f)
        writer = csv.DictWriter(g, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            # pairwise CSVs
            for k in ["audio_A","audio_B"]:
                if k in row: row[k] = map_audio(row[k])
            if "image" in row: row["image"] = map_image(row["image"])
            # interpretation CSVs
            if "audio_filename" in row: row["audio_filename"] = map_audio(row["audio_filename"])
            for k in ["M_picture","F_picture"]:
                if k in row: row[k] = map_image(row[k])
            writer.writerow(row)
    print(f"[OK] {fn} -> {dst.name}")

for fn in CSV_FILES:
    rewrite_file(fn)

print("Done. Use the *_opt.csv files in your PCIbex Template(getCSV(...)) or keep getCSV names and swap files on disk.")
