import logging
from pathlib import Path
from typing import Optional, Tuple, Annotated, Dict
from io import BytesIO
from PIL import Image, ImageFilter, ImageOps
from colorthief import ColorThief


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

    def extract_palette(self, comic_path: str, num_colors=5) -> Optional[Dict[str, str]]:
        """Extract color palette using ColorThief"""
        try:

            path = Path(comic_path)
            if not path.exists():
                print(f"Image file not found: {path}")
                return None

            # 1. Get Cover Bytes
            cover_bytes, success = self.get_page_image(comic_path, 0)
            if not success or not cover_bytes:
                return None

            color_thief = ColorThief(BytesIO(cover_bytes))
            palette = color_thief.get_palette(color_count=num_colors, quality=10)

            # Convert to HEX
            def rgb_to_hex(rgb_tuple):
                return f"#{rgb_tuple[0]:02x}{rgb_tuple[1]:02x}{rgb_tuple[2]:02x}"

            return {
                'primary': rgb_to_hex(palette[0]),
                'secondary': rgb_to_hex(palette[1]),
                'accent1': rgb_to_hex(palette[2]),
                'accent2': rgb_to_hex(palette[3]),
                'accent3': rgb_to_hex(palette[4]) if len(palette) > 4 else None
            }

        except Exception as e:
            print(f"Color palette extraction failed for {comic_path}: {e}")
            return None

    def extract_dominant_colors(self, comic_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract primary and secondary dominant colors from the comic cover.
        Returns: (Primary Hex, Secondary Hex) or (None, None)
        """
        try:
            # 1. Get Cover Bytes
            cover_bytes, success = self.get_page_image(comic_path, 0)
            if not success or not cover_bytes:
                return None, None

            # 2. Open & Resize (Speed Optimization)
            img = Image.open(BytesIO(cover_bytes))
            img.thumbnail((150, 150))  # Reduce processing time

            # 3. Quantize to reduce palette (e.g., 5 colors)
            # method=2 (Fast Octree) is usually sufficient and faster
            q_img = img.quantize(colors=5, method=2)

            # 4. Get Palette
            # getpalette() returns [r,g,b, r,g,b, ...]
            palette = q_img.getpalette()

            # We need to find the most frequent colors.
            # Pillow's histogram on a quantized image returns counts for indices.
            color_counts = sorted(q_img.getcolors(), key=lambda x: x[0], reverse=True)

            # Helper to convert RGB to Hex
            def rgb_to_hex(r, g, b):
                return f"#{r:02x}{g:02x}{b:02x}"

            # Extract Top 2
            # We iterate to skip "boring" colors if you wanted, but for V1 we just take top 2.
            colors = []
            for count, index in color_counts[:2]:
                # Palette is a flat list, so index * 3 gives the start of the RGB triplet
                start = index * 3
                r, g, b = palette[start], palette[start + 1], palette[start + 2]
                colors.append(rgb_to_hex(r, g, b))

            # Pad if only 1 color found
            if len(colors) == 1:
                colors.append(colors[0])

            return (colors[0], colors[1]) if colors else (None, None)

        except Exception as e:
            print(f"Color extraction failed for {comic_path}: {e}")
            return None, None



