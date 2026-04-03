# Postfix SMTP Relay Server — Production Setup Guide

**Target:** Ubuntu 22.04 LTS | **Role:** Central outbound mail relay for SaaS infrastructure

---

## Architecture

```
┌─────────────────────────────────┐
│   App Servers / Easypanel       │  ← SMTP port 25 blocked by OVH/host
│   (51.79.226.156, etc.)         │
└────────────────┬────────────────┘
                 │ Port 25 (internal/trusted)
                 ▼
┌─────────────────────────────────┐
│   Relay Server (n8n-server-2)   │  ← Postfix + OpenDKIM
│   Public IP: RELAY_SERVER_IP    │
└────────────────┬────────────────┘
                 │ Port 587 + STARTTLS + SASL Auth
                 ▼
┌─────────────────────────────────┐
│   Upstream SMTP Provider        │
│   (smtp.n8nclouds.com / SES)    │
└─────────────────────────────────┘
```

---

## Pre-flight Checklist

Before starting, confirm:

| Item | Value |
|---|---|
| Relay server OS | Ubuntu 22.04 LTS |
| Relay server public IP | `RELAY_SERVER_IP` |
| Blocked app server IP | `51.79.226.156` |
| Upstream SMTP host | `smtp.n8nclouds.com` |
| Upstream SMTP port | `587` |
| Your sending domain | `yourdomain.com` |
| Relay hostname (DNS A record) | `relay.yourdomain.com` |

> **DNS requirement:** `relay.yourdomain.com` must have an A record pointing to `RELAY_SERVER_IP`, and a matching PTR (reverse DNS) record — contact your host/OVH to set PTR.

---

## Step 1 — Install Postfix

```bash
apt update && apt install postfix mailutils libsasl2-modules -y
```

When prompted by the installer:
- **Mail configuration type:** `Internet Site`
- **System mail name:** `relay.yourdomain.com`

Verify the installed version:

```bash
postconf mail_version
```

---

## Step 2 — Configure `/etc/postfix/main.cf`

Replace the full contents with a clean, well-documented config:

```ini
# ─── Identity ────────────────────────────────────────────────
myhostname = relay.yourdomain.com
myorigin = /etc/mailname
mydomain = yourdomain.com

# ─── Network ─────────────────────────────────────────────────
inet_interfaces = all
inet_protocols = ipv4

# Trusted senders — ONLY your relay server and blocked app servers
# Never use 0.0.0.0/0 — that creates an open relay
mynetworks = 127.0.0.0/8, 51.79.226.156/32

# ─── Relay ───────────────────────────────────────────────────
relayhost = [smtp.n8nclouds.com]:587

# ─── Outbound SASL Auth (to upstream SMTP) ───────────────────
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous

# ─── Outbound TLS ────────────────────────────────────────────
smtp_use_tls = yes
smtp_tls_security_level = encrypt
smtp_tls_note_starttls_offer = yes
smtp_tls_loglevel = 1
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt

# Disable old/weak protocols
smtp_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_ciphers = high

# ─── Inbound Relay Restrictions ──────────────────────────────
smtpd_recipient_restrictions =
    permit_mynetworks,
    reject_unauth_destination

# ─── Anti-spam / Hardening ───────────────────────────────────
smtpd_helo_required = yes
smtpd_helo_restrictions = permit_mynetworks, reject_invalid_helo_hostname
disable_vrfy_command = yes
message_size_limit = 20480000

# ─── Rate Limiting ───────────────────────────────────────────
smtpd_client_message_rate_limit = 100
smtpd_client_connection_rate_limit = 50

# ─── DKIM Milter (add after Step 6) ──────────────────────────
# milter_default_action = accept
# milter_protocol = 6
# smtpd_milters = inet:localhost:8891
# non_smtpd_milters = inet:localhost:8891
```

---

## Step 3 — Add Upstream SMTP Credentials

```bash
nano /etc/postfix/sasl_passwd
```

Add one line:

```
[smtp.n8nclouds.com]:587   YOUR_SMTP_USERNAME:YOUR_SMTP_PASSWORD
```

Hash the file and lock it down:

```bash
postmap /etc/postfix/sasl_passwd
chmod 600 /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db
```

> `postmap` generates the `.db` binary lookup file Postfix actually reads. You must re-run it any time you edit `sasl_passwd`.

---

## Step 4 — Configure the Firewall

Allow inbound SMTP only from your trusted app servers:

```bash
ufw allow from 51.79.226.156 to any port 25 proto tcp comment "App server relay"
ufw allow out 587/tcp comment "Outbound to upstream SMTP"
ufw enable
ufw status verbose
```

> Do **not** open port 25 to `0.0.0.0/0`. Combine firewall rules with `mynetworks` for defense-in-depth.

---

## Step 5 — Start and Enable Postfix

```bash
systemctl restart postfix
systemctl enable postfix
systemctl status postfix
```

---

## Step 6 — DKIM Signing with OpenDKIM

DKIM is **critical for deliverability**. Skip this and your emails will land in spam.

### Install

```bash
apt install opendkim opendkim-tools -y
```

### Generate a key pair

```bash
mkdir -p /etc/opendkim/keys/yourdomain.com
opendkim-genkey -b 2048 -d yourdomain.com -D /etc/opendkim/keys/yourdomain.com -s relay -v
chown -R opendkim:opendkim /etc/opendkim/keys/
chmod 600 /etc/opendkim/keys/yourdomain.com/relay.private
```

### Configure `/etc/opendkim.conf`

```ini
AutoRestart         yes
AutoRestartRate     10/1h
Syslog              yes
SyslogSuccess       yes
LogWhy              yes

Canonicalization    relaxed/simple
Mode                sv
SubDomains          no

Selector            relay
Domain              yourdomain.com
KeyFile             /etc/opendkim/keys/yourdomain.com/relay.private

Socket              inet:8891@localhost
PidFile             /run/opendkim/opendkim.pid
UMask               007
UserID              opendkim

TrustAnchorFile     /usr/share/dns/root.key
```

### Create key table and signing table

```bash
echo "relay._domainkey.yourdomain.com yourdomain.com:relay:/etc/opendkim/keys/yourdomain.com/relay.private" \
  > /etc/opendkim/KeyTable

echo "@yourdomain.com relay._domainkey.yourdomain.com" \
  > /etc/opendkim/SigningTable
```

Update `/etc/opendkim.conf` to reference them:

```ini
KeyTable        /etc/opendkim/KeyTable
SigningTable    refile:/etc/opendkim/SigningTable
```

### Start OpenDKIM and wire it to Postfix

```bash
systemctl restart opendkim
systemctl enable opendkim
```

Uncomment the milter lines in `/etc/postfix/main.cf`:

```ini
milter_default_action = accept
milter_protocol = 6
smtpd_milters = inet:localhost:8891
non_smtpd_milters = inet:localhost:8891
```

```bash
systemctl restart postfix
```

### Publish DNS records

Get the public key to publish:

```bash
cat /etc/opendkim/keys/yourdomain.com/relay.txt
```

Add these DNS records for `yourdomain.com`:

| Type | Host | Value |
|---|---|---|
| TXT | `@` | `v=spf1 ip4:RELAY_SERVER_IP include:n8nclouds.com ~all` |
| TXT | `relay._domainkey` | *(contents of relay.txt — the `p=...` value)* |
| TXT | `_dmarc` | `v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com; adkim=r; aspf=r` |

> Allow 30–60 minutes for DNS propagation before testing.

---

## Step 7 — Test the Relay

### From the relay server itself

```bash
echo "Relay test body" | mail -s "Relay Test - $(date)" you@yourdomain.com
```

Watch the log in real time:

```bash
tail -f /var/log/mail.log
```

A successful delivery shows: `status=sent (250 OK)`

### From your blocked app server

```bash
# Verify port 25 is reachable
telnet RELAY_SERVER_IP 25

# Send a test message
echo "Test from app server" | sendmail -v -S RELAY_SERVER_IP:25 you@yourdomain.com
```

### Verify DKIM signing

Use [mail-tester.com](https://www.mail-tester.com) or [MXToolbox Email Header Analyzer](https://mxtoolbox.com/EmailHeaders.aspx) to confirm:
- ✅ DKIM `pass`
- ✅ SPF `pass`
- ✅ DMARC `pass`

---

## Step 8 — Configure App Servers / n8n / Easypanel

On your blocked server, configure SMTP as:

| Setting | Value |
|---|---|
| Host | `RELAY_SERVER_IP` |
| Port | `25` |
| Encryption | None (internal trusted network) |
| Username | *(leave empty — IP-whitelisted)* |
| Password | *(leave empty)* |
| From address | `noreply@yourdomain.com` |

---

## Operations Reference

### Queue management

```bash
mailq                    # view queue
postqueue -f             # flush (retry) all queued messages
postsuper -d ALL         # ⚠️  delete entire queue (use with care)
postcat -q <ID>          # inspect a specific queued message
```

### Log tailing

```bash
tail -f /var/log/mail.log          # live mail log
tail -f /var/log/mail.err          # errors only
grep "status=bounced" /var/log/mail.log   # find bounces
```

### Configuration testing

```bash
postfix check            # syntax check main.cf
postconf -n              # show all non-default values (great for auditing)
```

### DKIM verification

```bash
opendkim-testkey -d yourdomain.com -s relay -vvv
```

---

## Security Hardening Checklist

- [ ] `mynetworks` contains only specific trusted IPs (no `/16` or broader)
- [ ] Port 25 firewalled to trusted IPs only (not world-open)
- [ ] `disable_vrfy_command = yes` set
- [ ] `smtpd_helo_required = yes` set
- [ ] TLS v1.0 and v1.1 disabled
- [ ] `sasl_passwd` and `.db` are `chmod 600`
- [ ] PTR/rDNS record matches `myhostname`
- [ ] DKIM, SPF, DMARC all publishing and passing
- [ ] Fail2ban installed and monitoring `/var/log/mail.log`
- [ ] Tested with an open-relay checker (e.g., [MXToolbox](https://mxtoolbox.com/diagnostic.aspx))

---

## Troubleshooting

| Symptom | Check |
|---|---|
| `Connection refused` on port 25 | UFW rule + `inet_interfaces = all` |
| `Relay access denied` | Source IP not in `mynetworks` |
| `Authentication failed` | Re-run `postmap /etc/postfix/sasl_passwd` |
| `TLS handshake failed` | Verify upstream SMTP cert; check `smtp_tls_CAfile` |
| Emails in spam | DKIM/SPF/DMARC not passing; check DNS records |
| Queue growing, not draining | Run `mailq` + `postqueue -f`; check upstream SMTP credentials |
| OpenDKIM not signing | Check milter socket is `inet:localhost:8891`; check `opendkim` service status |

---

## Next Steps (Roadmap)

| Feature | Notes |
|---|---|
| **Multi-domain DKIM** | Add additional `KeyTable` / `SigningTable` entries per domain |
| **Per-tenant SMTP routing** | Use Postfix `transport_maps` to route by sender domain |
| **Fail2ban for mail abuse** | Monitor `mail.log` for repeated auth failures |
| **Prometheus + Grafana metrics** | Use `postfix-exporter` for queue depth, delivery rate dashboards |
| **Multi-upstream failover** | See note below |
| **TLS inbound (port 587)** | Add `submission` service in `master.cf` with cert for client auth |

### Multi-upstream failover (Postfix doesn't natively load-balance, but you can use primary + backup):

```ini
# In /etc/postfix/transport
*   smtp:[smtp1.n8nclouds.com]:587

# And configure /etc/postfix/master.cf for a fallback transport
# Or use a commercial load balancer in front of multiple relay instances
```

---

*Last reviewed: 2026-04-02*