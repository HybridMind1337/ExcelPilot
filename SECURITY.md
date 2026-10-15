# Security Policy

## Supported Versions

Only the latest minor release receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | Yes                |

## Reporting a Vulnerability

If you identify a security vulnerability in ExcelPilot, please do not disclose it publicly via GitHub issues.

Send a detailed report to `security@hybridmindlabs.com` containing:
- A description of the issue.
- Steps to reproduce or a minimal proof of concept spreadsheet.
- The affected version and platform details.

We will acknowledge receipt within 48 hours and coordinate remediation before public disclosure.

## Security Architecture Highlights

- **Formula Evaluation**: User-defined metrics are processed via a strict AST mathematical whitelist. Arbitrary code execution (`eval`, `exec`, attribute access) is prevented.
- **Formula Injection Mitigation**: Untrusted cell strings written to Excel output are sanitised to prevent CSV/Formula injection (DDE attack vectors).
- **Non-Root Execution**: Docker images run under an unprivileged user (`excelpilot`, UID 10001).
