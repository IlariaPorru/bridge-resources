#!/usr/bin/env python3
import csv, sys, pathlib, math, zipfile

# Config
MAX_ZIP_MB   = 50
ROOT         = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.cwd()
CSV_DIR      = ROOT / "csv"
AUDIO_DIR    = ROOT / "audio_opt"
IMAGES_DIR   = ROOT / "images_opt"
ZIP_DIR      = ROOT / "zip"
ZIP_DIR.mkdir(parents=True, exist_ok=True)

CSV_PREF = CSV_DIR / "spreadsheet_preference_opt.csv"
CSV_PREF_P = CSV_DIR / "practice_pairs_opt.csv"
CSV_INT  = CSV_DIR / "interpret_main_opt.csv"
CSV_INT_P = CSV_DIR / "interpret_practice_opt.csv"

def read_csv_rows(path):
    if not path.exists(): return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))

def add_file(fileset, relpath):
    p = ROOT / relpath
    if p.exists() and p.is_file():
        fileset.add(p)
    else:
        print(f"[WARN] Missing referenced file: {relpath}")

def collect():
    # Pairwise: audio files A/B 
    prefA = set(); prefB = set(); prefIMG = set()
    for row in read_csv_rows(CSV_PREF) + read_csv_rows(CSV_PREF_P):
        aA = row.get("audio_A","").strip()
        aB = row.get("audio_B","").strip()
        img= row.get("image","").strip()
        if aA: add_file(prefA, aA)
        if aB: add_file(prefB, aB)
        if img: add_file(prefIMG, img)

    # Interpretation: audio + two images
    intAUD = set(); intIMG = set()
    for row in read_csv_rows(CSV_INT) + read_csv_rows(CSV_INT_P):
        aud = row.get("audio_filename","").strip()
        m   = row.get("M_picture","").strip()
        f   = row.get("F_picture","").strip()
        if aud: add_file(intAUD, aud)
        if m:   add_file(intIMG, m)
        if f:   add_file(intIMG, f)

    return prefA | prefB, prefIMG, intAUD, intIMG

def human(n): return f"{n/1024/1024:.1f} MB"

def chunk_and_zip(files, zip_prefix):
    files = list(sorted(files))
    chunk, chunk_size = [], 0
    idx, made = 1, []
    limit = MAX_ZIP_MB * 1024 * 1024

    for p in files:
        sz = p.stat().st_size
        if sz > limit:
            print(f"[WARN] Single file exceeds {MAX_ZIP_MB}MB: {p} ({human(sz)}) — consider re-encoding.")
        if chunk_size + sz > limit and chunk:
            # flush
            zip_name = f"{zip_prefix}_{idx:02d}.zip"
            with zipfile.ZipFile(ZIP_DIR/zip_name, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                for f in chunk:
                    z.write(f, arcname=str(f.relative_to(ROOT)))
            print(f"[OK] {zip_name}  ({human(sum(f.stat().st_size for f in chunk))})   {len(chunk)} files")
            made.append(zip_name)
            idx += 1
            chunk, chunk_size = [], 0
        chunk.append(p)
        chunk_size += sz

    if chunk:
        zip_name = f"{zip_prefix}_{idx:02d}.zip"
        with zipfile.ZipFile(ZIP_DIR/zip_name, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for f in chunk:
                z.write(f, arcname=str(f.relative_to(ROOT)))
        print(f"[OK] {zip_name}  ({human(sum(f.stat().st_size for f in chunk))})   {len(chunk)} files")
        made.append(zip_name)

    return made

def main():
    prefAUD, prefIMG, intAUD, intIMG = collect()

    print("\n== Sizes (approx) ==")
    for label, coll in [("Pairwise audio", prefAUD), ("Pairwise images", prefIMG),
                        ("Interpret audio", intAUD), ("Interpret images", intIMG)]:
        total = sum(p.stat().st_size for p in coll)
        print(f"{label:18}: {len(coll):4d} files, {human(total)}")

    print("\n== Zipping (≤{} MB each) ==".format(MAX_ZIP_MB))
    z1 = chunk_and_zip(prefAUD, "pairpref_audio")
    z2 = chunk_and_zip(prefIMG, "pairpref_images")
    z3 = chunk_and_zip(intAUD,  "interpret_audio")
    z4 = chunk_and_zip(intIMG,  "interpret_images")

    # Emit PreloadZip lines
    print("\n== Paste these in your PCIbex script (after AddHost) ==")
    for z in (z1+z2+z3+z4):
        print(f"PennController.PreloadZip( withSlash(GITHUB_BASE) + 'zip/{z}' );")

if __name__ == "__main__":
    main()
