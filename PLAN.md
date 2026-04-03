# Postfix Setup Script — Improvement Plan

**Date:** 2026-04-03
**Scope:** Three enhancement tasks for `setup.py` + new `debug.py` utility

---

## Task 1: DNS Record Enforcement & DMARC/DKIM Verification

**Goal:** After setup completes, actively verify that DNS records (A, SPF, DKIM, DMARC) are correctly published—not just display them. Warn loudly when records are missing or incorrect.

### Changes in `setup.py`

1. **Add DNS lookup helpers** using `socket` and raw DNS queries (stdlib only — no `dnspython`).
   - `resolve_txt(domain)` — fetch TXT records via `dig` or `nslookup` (subprocess fallback).
   - `resolve_a(hostname)` — resolve A record.
2. **New Step 10: "Verify DNS Records"** (bump `TOTAL_STEPS` to 10).
   - Check A record for `relay_hostname` → matches server IP.
   - Check SPF TXT on `sending_domain` → contains the relay IP & `~all`/`-all`.
   - Check DKIM TXT on `<selector>._domainkey.<domain>` → exists and contains `p=`.
   - Check DMARC TXT on `_dmarc.<domain>` → exists and contains `v=DMARC1`.
   - For each: print ✔ PASS / ⚠ MISSING with the **exact record value that should be added**.
   - Record pass/fail in `step_results`.
3. **Enforce DMARC policy recommendation** — if DMARC record found but policy is `p=none`, suggest upgrading to `p=quarantine` or `p=reject`.

### Why stdlib-only?
The project promises zero external dependencies. We'll shell out to `dig` (installed with `dnsutils` / `bind9-dnsutils`) or fall back to `nslookup`.

---

## Task 2: Persistent Configuration (JSON)

**Goal:** Save collected parameters to a JSON config file so re-runs auto-fill previous values as defaults.

### Changes in `setup.py`

1. **Config file path:** `/etc/postfix/relay_setup_config.json` (production) with a local fallback `./relay_setup_config.json` when not root.
2. **`load_config()`** — read JSON file if it exists, return dict.
3. **`save_config(params)`** — write params dict (excluding `smtp_pass`) as pretty-printed JSON. Store with mode `0640`.
4. **Integrate into `collect_parameters()`** — load previous config at start; use its values as defaults in each `ask()` call instead of hardcoded defaults.
5. **Save after successful setup** — call `save_config()` right before the final summary.
6. **Security:** SMTP password is NEVER saved to the JSON file. It is always re-prompted.

### Config JSON structure

```json
{
  "version": 1,
  "created": "2026-04-03T12:00:00Z",
  "updated": "2026-04-03T12:00:00Z",
  "relay_hostname": "relay.example.com",
  "sending_domain": "example.com",
  "trusted_ips_raw": "10.0.0.5, 10.0.0.6",
  "smtp_host": "smtp.n8nclouds.com",
  "smtp_port": "587",
  "smtp_user": "user@example.com",
  "dkim_selector": "relay",
  "enable_dkim": true,
  "enable_ufw": true,
  "rate_limit": "100",
  "admin_email": "admin@example.com"
}
```

---

## Task 3: Create `debug.py`

**Goal:** A standalone diagnostic script that checks system health, service status, DNS records, configuration integrity, mail queue, and recent log activity — all in one report.

### Sections in `debug.py`

1. **System Info** — OS, hostname, IP, uptime, Python version.
2. **Service Status** — `postfix` running? `opendkim` running? listening on port 25?
3. **Configuration Audit**
   - `/etc/postfix/main.cf` exists & key directives present.
   - `/etc/postfix/sasl_passwd` exists & secured (mode 0600).
   - `/etc/mailname` matches config.
   - OpenDKIM config + key files exist.
4. **DNS Verification** — same checks as Task 1's Step 10 (shared helper).
5. **Mail Queue Stats** — total queued, deferred count, active count.
6. **Recent Log Analysis** — last 50 lines of `/var/log/mail.log`, count sent/bounced/deferred/rejected.
7. **Saved Config Check** — load `relay_setup_config.json`, display summary, flag missing fields.
8. **Overall Score** — X/Y checks passed, color-coded.

### Output

Console report with ANSI colors, same style as `setup.py`. Optionally write a `debug_report.json` with structured results.

---

## Documentation Updates

| File | Update |
|------|--------|
| `README.md` | Add `debug.py` usage, mention config persistence |
| `docs/01-overview.md` | Add DNS verification step, mention debug tool |
| `docs/03-installation.md` | Note config auto-fill on re-run |
| `docs/05-setup-steps.md` | Document new Step 10 (DNS verification) |
| `docs/06-dns-records.md` | Note that script now verifies records live |
| `docs/07-testing.md` | Add `debug.py` as a testing/diagnostic tool |
| `docs/10-troubleshooting.md` | Reference `debug.py` for diagnostics |

---

## Implementation Order

1. ✅ Create this plan
2. ✅ Task 2 (config persistence) — `load_config()`/`save_config()` in setup.py, JSON at `/etc/postfix/relay_setup_config.json`
3. ✅ Task 1 (DNS verification) — Step 10 `step_verify_dns()` with `dns_resolve_txt()`/`dns_resolve_a()` helpers
4. ✅ Task 3 (debug.py) — 7-section diagnostic report with JSON export
5. ✅ Documentation updates — README, 01-overview, 03-installation, 05-setup-steps, 06-dns-records, 07-testing, 10-troubleshooting
