from pathlib import Path
from typing import Optional, Tuple, Annotated
from io import BytesIO
from PIL import Image, ImageFilter, ImageOps
import logging

from app.services.archive import ComicArchive
from app.config import settings


class ImageService:
    """Service for extracting and processing comic images"""

    def __init__(self):
        self.thumbnail_size: tuple[float, float] = settings.thumbnail_size
        self.avatar_size: tuple[float, float] = settings.avatar_size

    def get_page_image(self, comic_path: str, page_index: int,
                       sharpen: bool = False,
                       grayscale: bool = False
                       ) -> Tuple[Optional[bytes], bool]:
        """
        Extract a specific page from a comic archive, optionally applying filters.

        Args:
            comic_path: Path to the comic file
            page_index: Zero-based page index
            sharpen: Whether to sharpen the image
            grayscale: Whether to apply grayscale filters

        Returns:
            Image bytes or None if page not found
        """
        try:
            file_path = Path(comic_path)

            if not file_path.exists():
                print(f"Comic file not found: {comic_path}")
                return None, False

            with ComicArchive(file_path) as archive:

                pages = archive.get_pages()

                if page_index < 0 or page_index >= len(pages):
                    print(f"Page index {page_index} out of range (0-{len(pages) - 1})")
                    return None, False

                # Extract Raw Bytes
                image_bytes = archive.read_file(pages[page_index])

                # FAST PATH: If no processing needed, return raw bytes
                if not sharpen and not grayscale:
                    return image_bytes, True

                # SLOW PATH: Pillow Processing
                try:
                    img = Image.open(BytesIO(image_bytes))

                    # Convert to RGB if needed (handle palettes/CMYK)
                    if img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')

                    # A. Apply Grayscale
                    if grayscale:
                        img = ImageOps.grayscale(img)

                    # B. Apply Sharpening (UnsharpMask is best for scans)
                    if sharpen:
                        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

                    # 4. Re-encode to JPEG
                    output = BytesIO()
                    img.save(output, format="JPEG", quality=85)
                    return output.getvalue(), True

                except Exception as e:
                    logging.error(f"Image processing failed: {e}")
                    print(f"Error processing image: {e}")
                    # CRITICAL: Return original bytes, but flag as FAILED processing
                    # so the controller knows not to cache this as the 'filtered' version.
                    return image_bytes, False  # Fallback, just return original bytes

        except Exception as e:
            print(f"Error extracting page {page_index}: {e}")
            return None, False

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
            cover_bytes, is_correct_format = self.get_page_image(comic_path, 0)
            if not cover_bytes or not is_correct_format:
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

    # Avatar Processing Logic
    def process_avatar(self, image_data: bytes, output_path: Path) -> bool:
        """
        Process a raw avatar upload:
        1. Fix Orientation (EXIF)
        2. Normalize Color (RGB/RGBA)
        3. Resize to standard avatar size
        4. Save as WebP
        """
        try:
            img = Image.open(BytesIO(image_data))

            # 1. Fix Orientation (Phone selfies often have rotation flags)
            img = ImageOps.exif_transpose(img)

            # 2. Convert to RGB/RGBA (Handle PNGs, BMPs, etc)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")

            # 3. Resize (Maintain Aspect Ratio)
            img.thumbnail(self.avatar_size, Image.Resampling.LANCZOS)

            # 4. Save
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "WEBP", quality=85)

            return True
        except Exception as e:
            raise ValueError(e)
            logging.error(f"Avatar processing error: {e}")
            return False
