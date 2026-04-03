# Security

## Hardening Checklist

- [ ] `mynetworks` contains **only** specific trusted IPs — no `/16` or broader
- [ ] Port 25 firewalled to trusted IPs only (not world-open)
- [ ] `smtpd_helo_required = yes`
- [ ] TLS v1.0 and v1.1 disabled (`!TLSv1, !TLSv1.1` in protocols)
- [ ] `sasl_passwd` and `.db` are `chmod 600`, owned by `root:root`
- [ ] PTR/rDNS record matches `myhostname`
- [ ] DKIM, SPF, DMARC all published and passing
- [ ] Tested with an open-relay checker

---

## What the Script Configures

### Network Restrictions

- `mynetworks` — Only explicitly listed IPs can relay mail
- `smtpd_recipient_restrictions` — `permit_mynetworks, reject_unauth_destination`
- **No open relay** — unauthenticated external senders are rejected

### TLS Enforcement

- `smtp_tls_security_level = encrypt` — All outbound connections require TLS
- Disabled protocols: SSLv2, SSLv3, TLSv1, TLSv1.1
- `smtp_tls_ciphers = high` — Only strong cipher suites

### Anti-spam Measures

- `smtpd_helo_required = yes` — Clients must send HELO/EHLO
- `reject_invalid_helo_hostname` — Rejects malformed HELO
- `reject_non_fqdn_helo_hostname` — Rejects non-FQDN HELO
- `reject_non_fqdn_sender` — Rejects non-FQDN sender addresses
- `reject_unknown_sender_domain` — Rejects senders from non-existent domains

### Rate Limiting

- `smtpd_client_message_rate_limit` — Max messages per client per time unit
- `smtpd_client_connection_count_limit = 20`
- `smtpd_client_connection_rate_limit = 30`
- `anvil_rate_time_unit = 60s`

### Credential Security

- SASL password file restricted to `root:root` with mode `0600`
- Password cleared from script memory after SASL step
- Password input is hidden during the wizard

### Firewall (UFW)

- SSH allowed (prevents lockout)
- Port 25 allowed only from trusted IPs
- Port 25 denied from all other sources
- Loopback traffic allowed

---

## Open Relay Testing

After setup, verify your server is **not** an open relay:

- [MXToolbox Open Relay Test](https://mxtoolbox.com/diagnostic.aspx)
- [mail-abuse.org Relay Test](https://www.mail-abuse.org/)

If the test shows your server relays for external senders, immediately check `mynetworks` and `smtpd_recipient_restrictions`.

---

## Additional Hardening (Manual)

These are **not** automated by the script but recommended:

### Fail2ban

Monitor `/var/log/mail.log` for repeated connection attempts:

```bash
apt install fail2ban -y
```

Create `/etc/fail2ban/jail.d/postfix.conf`:

```ini
[postfix]
enabled  = true
port     = smtp
filter   = postfix
logpath  = /var/log/mail.log
maxretry = 5
bantime  = 3600
```

```bash
systemctl restart fail2ban
```

### Disable VRFY

Add to `/etc/postfix/main.cf`:

```ini
disable_vrfy_command = yes
```

This prevents attackers from enumerating valid email addresses via the SMTP `VRFY` command.
