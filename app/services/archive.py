import zipfile
import rarfile
from pathlib import Path
from typing import List, Optional
import io
import re
from app.config import settings

# Import the rarfile configuration
import rarfile
try:
    rarfile.UNRAR_TOOL = settings.unrar_path
except:
    pass

try:
    import py7zr
    CB7_SUPPORT = True
except ImportError:
    CB7_SUPPORT = False
    print("Warning: py7zr not installed. CB7 support disabled.")


class ComicArchive:
    """Unified interface for CBZ, CBR, and CB7 archives"""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.extension = filepath.suffix.lower()
        self.archive = self._open_archive()

    def _open_archive(self):
        """Open the appropriate archive handler"""
        if self.extension == ".cbz":
            return zipfile.ZipFile(self.filepath)
        elif self.extension == ".cbr":
            return rarfile.RarFile(self.filepath)
        elif self.extension == ".cb7":
            if not CB7_SUPPORT:
                raise ValueError("CB7 support not available. Install py7zr package.")
            return py7zr.SevenZipFile(self.filepath)
        else:
            raise ValueError(f"Unsupported format: {self.extension}")

    def get_file_list(self) -> List[str]:
        """Get list of files in archive"""
        if self.extension == ".cbz":
            return self.archive.namelist()
        elif self.extension == ".cbr":
            return self.archive.namelist()
        elif self.extension == ".cb7":
            return self.archive.getnames()

    def get_pages(self) -> List[str]:
        """Get sorted list of image files (pages) - filter out non-images"""
        # Valid image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff'}

        # Files to explicitly ignore (common in comic archives)
        ignore_patterns = {'thumbs.db', '.ds_store', 'comicinfo.xml', '__macosx'}
        ignore_extensions = {'.nfo', '.sfv', '.txt', '.xml', '.db', '.ini'}

        files = self.get_file_list()

        # Filter to valid images only
        pages = []
        for f in files:
            file_path = Path(f)
            filename_lower = file_path.name.lower()

            # Skip ignored files
            if filename_lower in ignore_patterns:
                continue

            # Skip ignored extensions
            if file_path.suffix.lower() in ignore_extensions:
                continue

            # Only include valid image files
            if file_path.suffix.lower() in image_extensions:
                pages.append(f)

        # --- IMPROVED SORTING LOGIC ---
        def sort_key(filename):
            """
            Multi-stage sort key:
            1. Priority: Explicit covers ('fc', 'cover') come first (0 vs 1).
            2. Natural: Numbers sorted numerically (1, 2, 10).
            3. Symbols: Separators de-prioritized so 'c01a' < 'c01-'.
            """
            # 1. Normalize case
            text = filename.lower()

            # 2. COVER PRIORITY
            # Check for explicit cover naming conventions using regex word boundaries.
            # matches " fc ", "fc.", "-fc", etc.
            # 0 = Cover (Highest Priority), 1 = Standard Page
            is_cover = 0 if re.search(r'\b(fc|cover|front)\b', text) else 1

            # 3. SEPARATOR HACK (From previous fix)
            # Replace separators with high-ASCII char '~' to ensure letters sort before symbols.
            # 'c01a' (a=97) < 'c01-' (~=126)
            text = text.replace('-', '~').replace('_', '~')

            # 4. NATURAL SORT SPLIT
            # Split into [text, number, text, number...]
            natural_parts = [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]

            # Return tuple: (Priority, Natural_Sort_Parts)
            return (is_cover, natural_parts)

        # ------------------------------
        pages.sort(key=sort_key)

        return pages

    def read_file(self, filename: str) -> bytes:
        """Read a specific file from the archive"""
        if self.extension == ".cbz":
            return self.archive.read(filename)
        elif self.extension == ".cbr":
            return self.archive.read(filename)
        elif self.extension == ".cb7":
            return self.archive.read([filename])[filename].read()

    def get_comicinfo(self) -> Optional[bytes]:
        """Extract ComicInfo.xml if it exists"""
        files = self.get_file_list()
        comicinfo = next((f for f in files if f.lower() == "comicinfo.xml"), None)

        if comicinfo:
            return self.read_file(comicinfo)
        return None

    def close(self):
        """Close the archive"""
        self.archive.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()