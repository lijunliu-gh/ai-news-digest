# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do NOT open a public issue.**

Instead, please open a [private security advisory](https://github.com/lijunliu-gh/ai-news-digest/security/advisories/new) on this repository.

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact

We will acknowledge receipt within 48 hours and aim to provide a fix or mitigation plan within 7 days.

## Scope

This project is a static site with an automated data-fetching script. The main security concerns are:
- RSS/Atom feed parsing (XML injection)
- Translation API usage
- GitHub Actions workflow integrity
