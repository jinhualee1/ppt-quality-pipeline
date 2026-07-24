# Security and Data Handling

This repository is designed for synthetic or explicitly approved data.

Do not commit:

- browser profiles, cookies, login databases, or session storage;
- internal URLs, access tokens, user IDs, query IDs, or request dumps;
- collected user documents or screenshots without publication rights;
- private evaluation results or proprietary prompts;
- machine-specific `.env` files.

The review server binds to `127.0.0.1` by default and has no authentication.
Do not expose it to an untrusted network.

Before publishing a derived integration, run a secret scanner and verify data
ownership. When source-system code is confidential, implement a private
collector adapter rather than adding it to this repository.

Report security issues privately to the repository maintainers.
