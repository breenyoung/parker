import logging
from pathlib import Path
import multiprocessing
from multiprocessing import Queue
from typing import Tuple, Dict, Any, List
from sqlalchemy.orm import Session

from app.core.settings_loader import get_cached_setting
from app.database import SessionLocal
from app.models.comic import Comic, Volume
from app.models.library import Library
from app.models.series import Series
from app.services.images import ImageService

def _apply_batch(db, batch, stats_queue):

    from app.models.comic import Comic

    for item in batch:

        comic_id = item.get("comic_id")

        if item.get("error"):
            stats_queue.put({"comic_id": comic_id, "status": "error"})
            continue

        comic = db.query(Comic).get(comic_id)
        if not comic:
            stats_queue.put({"comic_id": comic_id, "status": "missing"})
            continue

        comic.thumbnail_path = item.get("thumbnail_path")
        palette = item.get("palette")

        if palette:
            comic.color_primary = palette.get("primary")
            comic.color_secondary = palette.get("secondary")
            comic.color_palette = palette

        stats_queue.put({"comic_id": comic_id, "status": "processed"})

    db.commit()

def _thumbnail_worker(task: Tuple[int, str]) -> Dict[str, Any]:
    """
    Pure CPU worker: given (comic_id, file_path), generate thumbnail + palette.

    Returns a small dict that can be sent over a Queue to the writer.
    """
    comic_id, file_path = task
    from app.services.images import ImageService  # import here to avoid issues after fork

    image_service = ImageService()
    target_path = Path(f"./storage/cover/comic_{comic_id}.webp")

    try:
        result = image_service.process_cover(str(file_path), target_path)

        if not result.get("success"):
            return {
                "comic_id": comic_id,
                "error": True,
                "message": "Image processing failed",
            }

        payload: Dict[str, Any] = {
            "comic_id": comic_id,
            "thumbnail_path": str(target_path),
            "palette": result.get("palette"),
            "error": False,
        }
        return payload

    except Exception as e:
        # Keep it small and serializable
        return {
            "comic_id": comic_id,
            "error": True,
            "message": str(e),
        }


def _thumbnail_writer(queue: Queue, stats_queue: Queue, batch_size: int = 100) -> None:
    """
    Dedicated writer process: reads worker results from `queue`,
    applies DB updates via a single SQLAlchemy session, and pushes
    per-item stats to `stats_queue`.

    Terminates when it receives a `None` sentinel.
    """
    from app.database import SessionLocal
    from app.models.comic import Comic

    db = SessionLocal()
    processed = 0
    errors = 0
    skipped = 0

    batch = []

    try:
        while True:

            item = queue.get()

            if item is None:
                break

            batch.append(item)

            # If batch is full, write it
            if len(batch) >= batch_size:
                _apply_batch(db, batch, stats_queue)
                processed += sum(1 for i in batch if not i.get("error"))
                errors += sum(1 for i in batch if i.get("error"))
                batch.clear()

        # Flush remaining items
        if batch:
            _apply_batch(db, batch, stats_queue)
            processed += sum(1 for i in batch if not i.get("error"))
            errors += sum(1 for i in batch if i.get("error"))

    finally:
        stats_queue.put(
            {
                "summary": True,
                "processed": processed,
                "errors": errors,
                "skipped": skipped,
            }
        )
        db.close()


class ThumbnailService:
    def __init__(self, db: Session, library_id: int = None):
        self.db = db
        self.library_id = library_id
        self.image_service = ImageService()
        self.logger = logging.getLogger(__name__)

    def process_missing_thumbnails(self, force: bool = False):
        """
        Find comics in this library without thumbnails and generate them.
        """

        # GUARD: Ensure we actually have a library ID before running a library-wide scan
        if not self.library_id:
            raise ValueError("Library ID required for library-wide processing")

        comics = self._get_target_comics(force)

        stats = {"processed": 0, "errors": 0, "skipped": 0}

        for comic in comics:
            # Double check existence (if not forcing)
            has_thumb = comic.thumbnail_path and Path(str(comic.thumbnail_path)).exists()
            has_colors = comic.color_primary is not None

            if not force and has_thumb and has_colors:
                stats["skipped"] += 1
                continue

            try:
                # Define path
                target_path = Path(f"./storage/cover/comic_{comic.id}.webp")

                # Generates WebP AND returns Color Palette
                result = self.image_service.process_cover(str(comic.file_path), target_path)

                if result['success']:
                    comic.thumbnail_path = str(target_path)

                    # Update Colors from result
                    if result.get('palette'):
                        palette = result['palette']
                        comic.color_primary = palette.get('primary')
                        comic.color_secondary = palette.get('secondary')
                        comic.color_palette = palette

                    # Commit periodically or per item (Per item is safer for long jobs)
                    self.db.commit()
                    stats["processed"] += 1
                else:
                    stats["errors"] += 1

            except Exception as e:
                print(f"Thumbnail error {comic.id}: {e}")
                self.logger.error(f"Thumbnail error {comic.id}: {e}")
                stats["errors"] += 1

        return stats

    def process_series_thumbnails(self, series_id: int):
        """
        Force regenerate thumbnails for ALL comics in a series.
        """
        # Get all comics for this series
        comics = self.db.query(Comic).join(Volume).filter(Volume.series_id == series_id).all()
        return self._generate_batch(comics)

    def _generate_batch(self, comics: list) -> dict:
        """Helper to process a list of comics"""
        stats = {"processed": 0, "errors": 0, "skipped": 0}

        for comic in comics:
            try:
                target_path = Path(f"./storage/cover/comic_{comic.id}.webp")

                # Force regeneration
                result = self.image_service.process_cover(comic.file_path, target_path)


                if result['success']:
                    comic.thumbnail_path = str(target_path)

                    if result.get('palette'):
                        palette = result['palette']
                        comic.color_primary = palette.get('primary')
                        comic.color_secondary = palette.get('secondary')
                        comic.color_palette = palette

                    self.db.commit()
                    stats["processed"] += 1
                else:
                    stats["errors"] += 1

            except Exception as e:
                print(f"Thumbnail error {comic.id}: {e}")
                self.logger.error(f"Thumbnail error {comic.id}: {e}")
                stats["errors"] += 1

        return stats

    def _get_target_comics(self, force: bool = False) -> List[Comic]:

        if not self.library_id:
            raise ValueError("Library ID required for library-wide processing")

        query = (
            self.db
            .query(Comic)
            .join(Comic.volume)
            .join(Series)
            .filter(Series.library_id == self.library_id)
        )

        if not force:
            # Smart Filter: Get comics missing thumbnails OR missing colors
            # This ensures we backfill colors for existing comics too.
            query = query.filter(
                (Comic.thumbnail_path == None) | (Comic.color_primary == None)
            )

        comics = query.all()

        return comics

    def process_missing_thumbnails_parallel(self, force: bool = False) -> Dict[str, int]:
        """
        Parallel thumbnail generation using multiprocessing.

        - Worker processes: image processing only (no DB).
        - Writer process: single SQLAlchemy session, serial DB updates.

        Returns stats dict: {"processed": int, "errors": int, "skipped": int}
        """
        if not self.library_id:
            raise ValueError("Library ID required for library-wide processing")

        comics = self._get_target_comics(force=force)
        stats = {"processed": 0, "errors": 0, "skipped": 0}

        if not comics:
            return stats

        # Pre-filter "skipped" to avoid sending unnecessary work
        tasks: List[Tuple[int, str]] = []
        for comic in comics:
            has_thumb = comic.thumbnail_path and Path(str(comic.thumbnail_path)).exists()
            has_colors = comic.color_primary is not None

            if not force and has_thumb and has_colors:
                stats["skipped"] += 1
                continue

            tasks.append((comic.id, str(comic.file_path)))

        if not tasks:
            return stats

        # Queues for inter-process communication
        result_queue: Queue = multiprocessing.Queue()
        stats_queue: Queue = multiprocessing.Queue()

        writer_proc = multiprocessing.Process(
            target=_thumbnail_writer, args=(result_queue, stats_queue)
        )
        writer_proc.start()

        # Use a Pool for CPU-bound workers
        requested_workers = get_cached_setting("system.parallel_image_workers", 0)
        self.logger.info(f"Requested {'(Auto)' if requested_workers <= 0 else requested_workers} worker(s) for parallel thumbnail generation")

        if requested_workers <= 0:
            workers = multiprocessing.cpu_count() or 1
        else:
            max_cores = multiprocessing.cpu_count() or 1
            workers = min(requested_workers, max_cores)

        self.logger.info(f"Using {workers} workers for parallel thumbnail generation")

        with multiprocessing.Pool(processes=workers) as pool:
            for payload in pool.imap_unordered(_thumbnail_worker, tasks):
                # Send worker result to writer
                result_queue.put(payload)

        # All worker tasks done; tell writer to finish
        result_queue.put(None)

        # Collect stats from writer
        summary_received = False
        while not summary_received:
            item = stats_queue.get()
            if item.get("summary"):
                stats["processed"] += item.get("processed", 0)
                stats["errors"] += item.get("errors", 0)
                stats["skipped"] += item.get("skipped", 0)
                summary_received = True

        writer_proc.join()

        return stats


