import threading
import time
from queue import Queue
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.library import Library
from app.services.scanner import LibraryScanner


@dataclass
class ScanTask:
    library_id: int
    force: bool


class ScanManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScanManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.queue = Queue()
        self.current_task: Optional[ScanTask] = None
        self.is_scanning = False
        self._stop_event = threading.Event()

        # Start the background worker
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

        self._initialized = True

    def add_task(self, library_id: int, force: bool = False) -> dict:
        """Add a scan task to the queue"""
        # Optional: Check if library is already in queue to prevent duplicates
        # simple check:
        if self.current_task and self.current_task.library_id == library_id:
            return {"status": "ignored", "message": "Library is currently being scanned"}

        task = ScanTask(library_id=library_id, force=force)
        self.queue.put(task)

        position = self.queue.qsize()
        return {
            "status": "queued",
            "message": "Scan added to queue",
            "position": position
        }

    def get_status(self):
        """Return current status of the scanner"""
        return {
            "is_scanning": self.is_scanning,
            "current_library_id": self.current_task.library_id if self.current_task else None,
            "queue_size": self.queue.qsize()
        }

    def _process_queue(self):
        print("Scan Manager Worker Started")
        while not self._stop_event.is_set():
            try:
                # Block for 1 second waiting for item, allows checking stop_event
                task = self.queue.get(timeout=1)
            except:
                continue

            self.is_scanning = True
            self.current_task = task

            try:
                self._run_scan(task)
            except Exception as e:
                print(f"Error running scan for library {task.library_id}: {e}")
            finally:
                self.is_scanning = False
                self.current_task = None
                self.queue.task_done()

    def _run_scan(self, task: ScanTask):
        # We must create a NEW database session here.
        # We cannot use the session from the FastAPI request because
        # that session closes when the HTTP request finishes.
        db: Session = SessionLocal()
        try:
            library = db.query(Library).filter(Library.id == task.library_id).first()
            if not library:
                print(f"Library {task.library_id} not found during background scan")
                return

            library.is_scanning = True
            db.commit()

            print(f"Starting background scan for: {library.name}")
            scanner = LibraryScanner(library, db)

            # Run the existing scan logic
            # We don't return the results to HTTP, so we just log them
            results = scanner.scan(force=task.force)

            # You might want to save 'results' to a 'ScanHistory' table here
            # or update a 'status' field on the Library model
            print(f"Scan complete for {library.name}. Imported: {results.get('imported')}")

        except Exception as e:
            print(f"Exception inside scanner: {e}")
            db.rollback()
        finally:

            try:
                # We re-fetch the library just to be safe, ensuring we have a valid object
                # attached to the current session state
                library = db.query(Library).filter(Library.id == task.library_id).first()
                if library:
                    library.is_scanning = False
                    db.commit()
            except Exception as e_cleanup:
                print(f"Error resetting scan status for library {task.library_id}: {e_cleanup}")

            db.close()


# Global instance
scan_manager = ScanManager()