# Security Policy

## Supported version

Security fixes are applied to the current `main` branch. This repository does not currently publish versioned production releases.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's **Security → Report a vulnerability** private reporting flow. Include affected endpoint or commit, reproduction steps, impact, and any suggested remediation. Please avoid accessing data that is not yours and do not run denial-of-service tests.

The maintainers aim to acknowledge a report within 72 hours and will coordinate disclosure after a fix is available.

## Development secret warning

`JWT_SECRET_KEY=your-secret-key` is retained only for local-development compatibility. It is intentionally not considered safe for a public deployment. Every deployed environment must provide a long, unique secret outside Git.
