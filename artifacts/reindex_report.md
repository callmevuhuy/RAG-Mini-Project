# Re-index and rollback report

## Bundles

- `artifacts/index_bundle.json`: corpus v1.0; 12 documents, 31 chunks.
- `artifacts/index_bundle_v1_1.json`: candidate corpus v1.1; same document/chunk count.
- Both bundles are validated on load and carry SHA-256 integrity hashes. The hash detects accidental corruption but is not a cryptographic signature for source authenticity.

## API activation

`POST /api/v1/rag/reindex?version=1.1` or `version=1.0` requires an active demo session, an allowed browser origin when supplied, `X-User-Role: admin`, and a matching backend `DEMO_ADMIN_TOKEN`. It loads and validates the selected known bundle, records an audit entry, then atomically replaces `artifacts/active_index.json`. Other workers on the same filesystem read this pointer and reload the selected bundle on their next index access.

This is local/same-host coordination. There is no distributed lock or multi-host deployment protocol. Re-index must not be exposed on an untrusted network with shared demo tokens.

## Verify behavior

```powershell
# After setting a demo admin token and starting the API, call v1.1 then v1.0:
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/rag/reindex?version=1.1 -WebSession $session -Headers $adminHeaders
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/rag/reindex?version=1.0 -WebSession $session -Headers $adminHeaders
```

Query “Thời hạn đổi trả hàng là bao nhiêu ngày?” and confirm answer/citation version follows active status: v1.1 should cite the 14-day policy; v1.0 should cite the 07-day policy. API status exposes the active version. The pointer persists selection across process restart on the same host.

Automated isolated TestClient coverage activates v1.1, confirms status reload and the 14-day answer/citation, rolls back to v1.0, then confirms the 07-day answer/citation and audit version/count. It also verifies unauthorized requests return 403 and internal documents remain inaccessible to customers. This verifies the API path with an isolated temporary DB and pointer, not a live UI-assisted demonstration or multi-host coordination. Never infer sub-100ms performance without measuring the target environment.
