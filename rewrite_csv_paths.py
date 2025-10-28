#!/usr/bin/env python3
import csv, sys, pathlib, re

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.cwd()
CSV_DIR = ROOT / "csv"

CSV_FILES = [
    "spreadsheet_preference.csv",
    "practice_pairs.csv",
    "interpret_main.csv",
    "interpret_practice.csv",
]

AUDIO_TOP_IN  = "audio"
AUDIO_TOP_OUT = "audio_opt"
IMG_TOP_IN    = "images"
IMG_TOP_OUT   = "images_opt"

def is_url(p: str) -> bool:
    return bool(re.match(r"^https?://", p or ""))

def norm_slash(p: str) -> str:
    return (p or "").strip().replace("\\", "/")

def swap_topdir(p: pathlib.Path, in_top: str, out_top: str) -> pathlib.Path:
    parts = p.parts
    if not parts:
        return p
    if parts[0] == out_top:
        # Already optimized; keep subpath
        return p
    if parts[0] == in_top:
        return pathlib.Path(out_top).joinpath(*parts[1:])
    # No top-level dir → place under out_top at same relative path/name
    return pathlib.Path(out_top, *parts)

def force_ext(p: pathlib.Path, ext: str) -> pathlib.Path:
    # ext should include leading dot, e.g. ".mp3"
    return p.with_suffix(ext)

def map_audio(path: str) -> str:
    s = norm_slash(path)
    if not s or is_url(s):
        return s
    p = pathlib.Path(s)
    # move under audio_opt preserving subdirs
    q = swap_topdir(p, AUDIO_TOP_IN, AUDIO_TOP_OUT)
    # ensure .mp3 exactly once
    q = force_ext(q, ".mp3")
    return q.as_posix()

def map_image(path: str) -> str:
    s = norm_slash(path)
    if not s or is_url(s):
        return s
    p = pathlib.Path(s)
    # move under images_opt preserving subdirs
    q = swap_topdir(p, IMG_TOP_IN, IMG_TOP_OUT)
    # ensure .webp exactly once
    q = force_ext(q, ".webp")
    return q.as_posix()

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
            # pairwise
            for k in ("audio_A", "audio_B"):
                if k in row:
                    row[k] = map_audio(row[k])
            if "image" in row:
                row["image"] = map_image(row["image"])
            # interpretation
            if "audio_filename" in row:
                row["audio_filename"] = map_audio(row["audio_filename"])
            for k in ("M_picture", "F_picture"):
                if k in row:
                    row[k] = map_image(row[k])
            writer.writerow(row)
    print(f"[OK] {fn} -> {dst.name}")

if __name__ == "__main__":
    for fn in CSV_FILES:
        rewrite_file(fn)
    print("Done.")
