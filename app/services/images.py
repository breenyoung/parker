from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO
from PIL import Image

from app.services.archive import ComicArchive
from app.config import settings


class ImageService:
    """Service for extracting and processing comic images"""

    def __init__(self):
        self.thumbnail_size = settings.thumbnail_size

    def get_page_image(self, comic_path: str, page_index: int) -> Optional[bytes]:
        """
        Extract a specific page from a comic archive

        Args:
            comic_path: Path to the comic file
            page_index: Zero-based page index

        Returns:
            Image bytes or None if page not found
        """
        try:
            file_path = Path(comic_path)

            if not file_path.exists():
                print(f"Comic file not found: {comic_path}")
                return None

            with ComicArchive(file_path) as archive:
                pages = archive.get_pages()

                if page_index < 0 or page_index >= len(pages):
                    print(f"Page index {page_index} out of range (0-{len(pages) - 1})")
                    return None

                return archive.read_file(pages[page_index])
        except Exception as e:
            print(f"Error extracting page {page_index}: {e}")
            return None

    def get_page_count(self, comic_path: str) -> int:
        """Get the number of pages in a comic"""
        try:
            file_path = Path(comic_path)
            if not file_path.exists():
                return 0
            with ComicArchive(file_path) as archive:
                return len(archive.get_pages())
        except Exception:
            return 0

    def generate_thumbnail(self, comic_path: str, output_path: Path) -> bool:
        """
        Generate a thumbnail from the comic cover and save it to the specific output path.

        Args:
            comic_path: Source comic file
            output_path: Destination for the .webp thumbnail

        Returns:
            True if successful, False otherwise
        """
        try:
            # 1. Extract Cover
            cover_bytes = self.get_page_image(comic_path, 0)
            if not cover_bytes:
                return False

            # 2. Process Image
            img = Image.open(BytesIO(cover_bytes))

            # Handle Color Modes (CMYK, Palettes, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 3. Resize
            width, height = self.thumbnail_size
            img.thumbnail((width, height), Image.Resampling.LANCZOS)

            # 4. Save to Destination
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            img.save(output_path, format='WEBP', quality=85, method=6)
            return True

        except Exception as e:
            print(f"Error generating thumbnail for {comic_path}: {e}")
            return False