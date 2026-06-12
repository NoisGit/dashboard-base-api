# Error contract v1

All failed API requests return the same top-level fields:

- `version`: contract version (`1`)
- `code`: stable machine-readable category
- `message`: safe user-facing summary
- `details`: optional structured validation context
- `request_id`: correlation identifier also returned as `X-Request-ID`
- `detail`: temporary compatibility alias for existing dashboard clients

Validation details never include submitted values. Internal exceptions, SQL errors,
provider payloads and secrets are not returned.
