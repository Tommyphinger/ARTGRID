"""
Utility script to bulk import images from the uploads/ folder into the database.
- Scans the uploads/ directory for image files.
- Inserts metadata into the Artwork table (title, medium, category, file_url, thumbnail_url).
- Commits in small batches (default 50) to avoid locking issues in SQLite.
- Prevents duplicates by checking file_url.
"""

import sys
from pathlib import Path
from PIL import Image

# ---------------------------------------------------------
# 1. Allow imports from project root (where server.py lives)
# ---------------------------------------------------------
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import the Flask app, database, and Artwork model from server.py
from server import app, db, Artwork


# ---------------------------------------------------------
# 2. Helper functions
# ---------------------------------------------------------

def generate_thumbnail(image_path: Path, max_size=(512, 512)) -> str | None:
    """
    Generate a lightweight thumbnail (JPEG) for a given image.
    Returns the relative thumbnail path if successful, else None.
    """
    try:
        thumb_path = image_path.with_suffix(image_path.suffix + ".thumb.jpg")
        if not thumb_path.exists():
            with Image.open(image_path) as im:
                im.thumbnail(max_size)
                im.save(thumb_path, "JPEG", quality=80, optimize=True)
        return str(thumb_path.relative_to(Path(__file__).resolve().parents[1])).replace("\\", "/")
    except Exception as e:
        print(f"⚠️ Thumbnail generation failed for {image_path.name}: {e}")
        return None


def scan_images(root: Path):
    """
    Recursively scan a folder and yield all image files with valid extensions.
    """
    valid_ext = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    for p in root.rglob("*"):
        if p.suffix.lower() in valid_ext and p.is_file():
            yield p


# ---------------------------------------------------------
# 3. Main import process
# ---------------------------------------------------------

def main():
    base_dir = Path(__file__).resolve().parents[1]
    uploads = base_dir / "uploads"

    if not uploads.exists():
        print("❌ The 'uploads/' folder does not exist.")
        sys.exit(1)

    files = list(scan_images(uploads))
    total = len(files)
    print(f"📂 Found {total} image files in {uploads}")

    batch_size = 50
    created, skipped = 0, 0

    with app.app_context():
        for i, path in enumerate(files, start=1):
            rel_path = str(path.relative_to(base_dir)).replace("\\", "/")

            # Skip if already in DB (avoid duplicates)
            exists = db.session.query(Artwork.id).filter_by(file_url=rel_path).first()
            if exists:
                skipped += 1
            else:
                thumb = generate_thumbnail(path)
                artwork = Artwork(
                    user_id=1,  # TODO: replace with real uploader logic if needed
                    title=path.stem,
                    description="",
                    medium="photo",       # adjust depending on domain
                    category="image",     # adjust depending on domain
                    file_url=rel_path,
                    thumbnail_url=thumb
                )
                db.session.add(artwork)
                created += 1

            # Commit every batch_size rows
            if i % batch_size == 0:
                db.session.commit()
                print(f"✅ Committed batch up to {i}/{total}")

        # Final commit for remaining records
        db.session.commit()

        # Print summary
        print("-------------------------------------------------")
        print(f"✅ Import finished")
        print(f"   → New artworks created: {created}")
        print(f"   → Duplicates skipped:  {skipped}")
        print(f"   → Total in DB now:     {db.session.query(Artwork).count()}")


if __name__ == "__main__":
    main()
