# Postfix SMTP Relay Server

Automated production setup for a Postfix SMTP relay server on Ubuntu/Debian. A single Python 3 script configures Postfix, OpenDKIM, SASL authentication, UFW firewall, and generates DNS records — with zero external dependencies.

## Quick Start

```bash
# First-time setup (or reconfigure)
sudo python3 setup.py

# Diagnostics & health check
sudo python3 debug.py
```

**Re-run friendly:** On subsequent runs, `setup.py` auto-fills previous configuration from `relay_setup_config.json` — just press Enter to keep saved values.

## Documentation

| Doc | Description |
|-----|-------------|
| [01-overview.md](docs/01-overview.md) | Architecture, features, and project structure |
| [02-prerequisites.md](docs/02-prerequisites.md) | System requirements and DNS setup |
| [03-installation.md](docs/03-installation.md) | How to run the setup script |
| [04-configuration.md](docs/04-configuration.md) | All 12 parameters explained |
| [05-setup-steps.md](docs/05-setup-steps.md) | What each automated step does |
| [06-dns-records.md](docs/06-dns-records.md) | SPF, DKIM, DMARC, and PTR records |
| [07-testing.md](docs/07-testing.md) | Verification procedures |
| [08-operations.md](docs/08-operations.md) | Queue management, logs, maintenance |
| [09-security.md](docs/09-security.md) | Security hardening checklist |
| [10-troubleshooting.md](docs/10-troubleshooting.md) | Common issues and fixes |