# myapp-faas-services

Machine-managed repository of AI-generated MyApp FaaS backend services.

> Do NOT edit by hand. The MyApp backend control plane validates and commits
> every change here through an isolated push worker. Pull requests / manual
> commits are not part of the deployment flow and may be overwritten.

- Runtime: Python + Flask only (strictly validated).
- One directory per user service; see `LAYOUT.md` for the path contract.
- This GitHub repo is the runtime **source of truth**: the MyApp faas-node
  pulls from here and runs the exact service path.

Security boundary: AI Agent runtimes never receive write/read keys for this
repo. Only the backend-owned push worker (read-write) and the faas-node
(read-only) hold per-repo deploy keys.
