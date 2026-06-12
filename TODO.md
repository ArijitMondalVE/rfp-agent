# TODO - Refresh persistence (PDF history + past report)

- [x] Inspect current document/session restore flow on frontend (`AppComponent` + `ChatWindow` + `ChatComponent`).
- [x] Implement persistence of “last opened document” (doc id + session id) in `AppComponent`.

- [ ] On `AppComponent.ngOnInit()`, restore last opened document by calling `GET /documents/{id}` and reusing existing `openDocument` logic.
- [ ] Ensure `ChatWindow` / `ChatComponent` load chat history for restored `session_id`.
- [x] Verify refresh behavior: after upload/open, hard refresh shows past report + chat without re-upload processing.



