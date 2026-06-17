# TODO - Cancel upload + stop embedding

- [ ] Implement upload job tracking in DB (`upload_jobs` table + helpers) in `backend/app/db/document_store.py`
- [ ] Refactor `/upload` to create background job and return immediately with `job_id` + `session_id`
- [ ] Add background worker that checks cancel flag before creating vector store and before saving doc/chunks/report
- [ ] Add API endpoints:
  - [ ] `POST /upload/{job_id}/cancel`
  - [ ] `GET /upload/{job_id}`
- [ ] Ensure cancelled jobs do not write embeddings/chunks/report, and delete temp uploaded file
- [ ] Run quick python compile/import checks

