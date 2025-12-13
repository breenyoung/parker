# Parker Comic Server

Parker is a self‑hosted comic book server for CBZ/CBR archives. It’s designed to be simple to run, easy to use, and powerful enough to organize large collections.

---

## 🚀 Quickstart

1. Get the docker image (recommended)

Parker publishes two Docker image channels:

- **Stable (recommended):**
The latest tag is built from versioned releases and is the recommended option for most users.

  ```bash
  docker run -d \
    -p 8000:8000 \
    -v /some/path/config:/app/storage \
    -v /some/path/comics:/comics \
    ghcr.io/parker-server/parker:latest
  ```
 
- **Edge**:
The edge tag is built automatically from every commit to master.
It includes the newest features and fixes, but may be less stable

  ```bash
  docker run -d \
    -p 8000:8000 \
    -v /some/path/config:/app/storage \
    -v /some/path/comics:/comics \
    ghcr.io/parker-server/parker:edge
  ```

**or**

1. Clone the repository:
   ```bash
   git clone https://github.com/parker-server/parker.git
   cd parker
   
2. ```docker-compose up -d --build```
3. Access Parker at http://localhost:8000. Default user: admin/admin
4. Admin tools found at http://localhost:8000/admin

## ✨ What You Get
- Browse comics by Library → Series → Volume → Issue
- Web Reader with manga mode, double‑page spreads, and swipe navigation
- Smart Lists and Pull Lists to organize your reading
- Reports Dashboard to spot missing issues, duplicates, and storage usage
- User accounts with library permissions
- Optional OPDS feed for external reader apps
- Optional WebP transcoding for faster remote reading

## 📌 Status- Current version: 1.1 (Stable)
- Core features are ready to use
- Expect ongoing updates and improvements

## 🤝 Contributing
Parker is open source and evolving. Feedback, bug reports, and pull requests are welcome!

## 📜 License
MIT License


