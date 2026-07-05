# Quark QR Auth Design

## Goal

Replace the current browser/Cookie-first Quark login experience with a QR-code-first login flow that works directly in the terminal, while keeping Cookie import as a fallback.

## Design

Add a focused `scripts/quark_auth/` package:

- `providers.py` exposes small auth providers. The first provider wraps `quarkpan` API QR login. The fallback provider reuses the existing browser/Cookie helper.
- `storage.py` saves successful credentials into the existing `config.json` shape, so existing save/search code continues reading `quark.cookie`.
- `manager.py` orchestrates login, status, provider fallback, and user-facing messages.

The terminal command `/login quark` calls `QuarkAuthManager.login()`. It first tries QR login and asks the user to scan with the Quark app. If `quarkpan` is missing or QR login fails, it explains the reason and falls back to the old browser/Cookie flow. The agent never prints the Cookie value.

## Error Handling

- Missing `quarkpan` is reported as a provider failure, then fallback starts.
- Empty or invalid QR Cookie is treated as a failed provider result.
- If every provider fails, the command returns a concise failure message.
- Status summaries expose only configured state, source, timestamp, and Cookie length.

## Testing

Unit tests mock the QR provider dependency so no real Quark network call or account login is required. Coverage focuses on provider success, provider fallback, storage redaction, and the terminal command summary.
