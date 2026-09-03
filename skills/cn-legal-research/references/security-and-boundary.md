# Security and boundary contract

- Requests are HTTPS-only and are limited to registered official hosts.
- Redirect targets are revalidated before content is accepted.
- No credentials, cookies, authorization headers, browser sessions or login flows are accepted by the public client.
- The client does not disable TLS verification, bypass robots/verification controls, or retry access-denied responses as if they were transient.
- Rate limiting is serialized per client. The caller may choose a slower rate but cannot request concurrent bursts through the bundled CLI.
- Cache writes require an explicit directory. Download writes require an explicit output path. Neither is permitted inside the Skill source by default.
- The adapter returns source metadata and extracted content; it does not decide legal effect, temporal application, authenticity, admissibility, or litigation strategy.
- A network error, access denial, unavailable page, incomplete field or version conflict remains visible in the result and cannot be converted into a verified-source record.
