# RAG Architecture — current demo implementation

## Ranh giới hệ thống

- React/Vite gọi FastAPI; frontend không kết nối SQLite trực tiếp.
- SQLite là nguồn sự thật cho SKU, giá, tồn kho, session và đơn. RAG chỉ tra cứu tài liệu; order actions vẫn đi qua validation hiện hữu.
- `src/rag.py` ingest manifest, cắt theo Markdown H2, vector hóa hashed word/character n-gram term frequency và tìm top-k bằng cosine. Đây là lexical retrieval chạy local, không phải semantic embedding. Không cần Ollama cho đường RAG hiện tại.
- `src/router.py` tách mixed query theo dấu câu và liên từ tiếng Việt có dấu/không dấu. Với một số chủ đề có nhiều điều kiện, retriever thêm từ khóa truy vấn để đưa đúng section vào top-k; riêng câu hỏi vừa hỏi cách vệ sinh vừa hỏi cảnh báo bình giữ nhiệt sẽ trả nội dung từ cả hai chunk và chỉ cite đúng hai nguồn đó. Nếu thiếu một trong hai chunk, route abstains thay vì trả lời một nửa như thể đã đủ evidence.

## Request flow

```text
Browser + session cookie
        |
        v
FastAPI: origin/session checks; staff/admin role token gate
        |
        v
src/router.py
  |-- knowledge --> role-filtered retrieval --> answer + citations
  |-- mixed ------> knowledge answer + independently validated action
  |-- order ------> inherited extraction + DB checks
  |-- safety/handoff --> safe rejection or demo handoff
```

Pure handoff requests do not go through model extraction. Existing pending order follow-ups can continue only through the session-scoped pending state path.

## Ingestion and bundles

Manifest entries require document ID, filename, title, version, access level and author. Files must be Markdown, non-empty, UTF-8, unique by ID/name and resolved inside the corpus root. Chunk IDs are stable `{doc_id}#cNN`; access level is copied from required manifest metadata and never defaults to public.

Bundle metadata records corpus/index version, vectorizer ID/revision, query/document encoding, normalization, cosine metric, chunking config, source hashes, dimensions and counts. Loading checks the bundle SHA-256, count/dimension consistency, unique chunk IDs, allowed access levels and finite vector values. The checksum detects accidental corruption; it is not a signature against an attacker who can rewrite the file.

## Access and demo authentication

Retrieval filters chunks before ranking. `customer` gets public, `staff` gets public+staff, and `admin` gets all. Backend role resolution accepts customer by default; staff/admin require a configured server-side `DEMO_STAFF_TOKEN` or `DEMO_ADMIN_TOKEN` and matching `X-Demo-Role-Token`. Blank tokens disable those roles. The UI selector is not an authority source. This is a local demo gate, not enterprise identity, SSO, token rotation, or multi-tenant authorization.

Chat and re-index writes validate browser origin. Re-index also requires a valid demo session and admin token, loads and verifies a known bundle, records an audit event, then atomically replaces `artifacts/active_index.json`. Each process checks that pointer when serving an index request and reloads if the selected bundle changes. The filesystem pointer supports local multi-worker visibility; it is not a distributed coordination protocol for multiple hosts.

## Answers, citations, and limits

Answers use deterministic topic-specific templates from the local corpus, not an LLM generation call. Multi-source care/caution answers use text from each retrieved chunk and cite those chunks. Return-policy topic hints and query expansion prioritize requested time-limit, condition and fee sections. The evaluator separately reports expected-answer fact match, retrieved-evidence lexical coverage and cited-evidence lexical support. These are exact normalized string checks against chunk text/source title, not human entailment review; citation resolution alone still does not prove a claim. Mixed action-intent accuracy checks router labels only; separate API tests cover selected action execution paths, not every offline evaluation case.

The retrieval vectorizer is lexical and can miss paraphrases outside the authored suite. Before production, add signed/versioned artifact provenance, durable multi-host activation coordination, identity-backed authorization, independent reviewed evaluation and a measured semantic embedder if quality requires it. Do not load customer PII into this demo.
