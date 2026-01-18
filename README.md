# filex
Google search for your file system. NWHacks 2026 
A local service that indexes and analyses a directory so that users can search a variety of files semantically based on document content (ex: `.txt`, `.docx` `.c`) and also image content (`.png`, `.jpg`, `.webp`). 
It uses a combination of text embeddings, large language models, and computer vision to generate its metadata to track files. 
A website is included to allow users to access their system efficiently, running locally for security.

## MVP
Support two file types: `.txt` and `.png` with reliable and efficient data extraction.
One embedding backend (hosted or local), used consistently for both documents and queries.

Minimal endpoints:
- POST /files (upload + index)
- GET /files/{id} (status/metadata)
- POST /search (query + returns top chunks)
- Basic UX: return top snippets with file name + chunk text so users can confirm relevance quickly.
​​
