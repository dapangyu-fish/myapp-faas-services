# Repository layout contract

Each generated service lives at:

```
<uid[0:2]>/<uid[2:4]>/<uid>/<service_id>/
  app.py            # Flask app exposing `app` (or `application`)
  requirements.txt  # flask / pydantic / python-dateutil only
  service.json      # declared routes + metadata (machine-written)
  README.md
```

Example, user id `9aebdab8-3318-4dfa-99ff-54973bd28cf4`:

```
9a/eb/9aebdab8-3318-4dfa-99ff-54973bd28cf4/<service_id>/
```

Rules:
- `uid` is path-sanitized; non-path-safe ids fall back to a deterministic hash.
- A user may own at most N services (backend-configured, default 5).
- `service_id` is unique per user; the same id re-deployed replaces that
  service in place (update = new commit + faas-node pull + restart).
