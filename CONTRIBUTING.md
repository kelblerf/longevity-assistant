# Contributing

Thank you for contributing to `longevity-assistant`.

This repository is still evolving, so the main goal is to keep changes understandable, reviewable, and safe for a public codebase.

## Before you start

- read [README.md](README.md)
- read [SECURITY.md](SECURITY.md)
- avoid committing secrets, personal health data, private exports, or workspace-specific identifiers

## Development expectations

- prefer small, focused pull requests
- keep product, architecture, and code changes aligned
- preserve source attribution and safety-oriented behavior in assistant features
- update documentation when behavior or workflows change

## Local checks

Run the relevant checks before opening a pull request:

```powershell
npm run build:frontend
npm run eval:production
```

If your change touches backend behavior, also run:

```powershell
npm run test:backend
```

## Pull request guidance

- describe what changed and why
- mention any user-facing or architectural impact
- call out privacy or data-handling implications when relevant
- keep screenshots and examples free of personal data

## Documentation and privacy

For public repository hygiene:

- use repository-relative links in docs
- do not add direct links to private knowledge systems
- generalize personal workspace names when they are not essential
- keep `.env`, runtime data, and draft imports out of git

## Review standard

Changes are easiest to review when they are:

- scoped
- tested
- documented
- safe to publish publicly
