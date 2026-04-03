# Configuration Parameters

The setup wizard collects 12 parameters. Each has input validation and most have sensible defaults.

---

## 1. Relay Hostname

```
Prompt:    Relay hostname [relay.yourdomain.com]
Validator: Must contain a dot (FQDN)
```

The fully qualified domain name of this relay server. Must match:

- The DNS **A record** pointing to this server's IP
- The **PTR (reverse DNS)** record of this server's IP

Used as `myhostname` in Postfix.

---

## 2. Sending Domain

```
Prompt:    Sending domain
Validator: Must contain a dot
```

Your organization's primary email domain (e.g. `yourdomain.com`). Used for:

- `mydomain` in Postfix
- DKIM key configuration
- DNS record generation (SPF, DKIM, DMARC)

---

## 3. Trusted App Server IPs

```
Prompt:    Trusted IPs (comma-separated) [127.0.0.0/8]
```

Comma-separated list of IP addresses or CIDR ranges allowed to relay mail through this server. `127.0.0.0/8` is always included automatically.

- Single IPs (e.g. `51.79.226.156`) are auto-converted to `/32` notation
- CIDR ranges are accepted as-is (e.g. `10.0.0.0/24`)
- **Never use `0.0.0.0/0`** — this creates an open relay

Used as `mynetworks` in Postfix and for UFW firewall rules.

---

## 4. Upstream SMTP Host

```
Prompt:    Upstream SMTP host [smtp.n8nclouds.com]
Validator: Must contain a dot (FQDN)
```

The SMTP server this relay forwards all outbound mail to. Examples:

- `smtp.n8nclouds.com`
- `email-smtp.us-east-1.amazonaws.com` (AWS SES)
- `smtp.mailgun.org`

Used in the `relayhost` directive.

---

## 5. Upstream SMTP Port

```
Prompt:    Upstream SMTP port [587]
Validator: Integer between 1–65535
```

The port for the upstream SMTP connection. Common values:

- `587` — STARTTLS (recommended)
- `465` — Implicit TLS

---

## 6. SMTP Username

```
Prompt:    SMTP username
Validator: Required (non-empty)
```

Username for authenticating to the upstream SMTP server. Stored in `/etc/postfix/sasl_passwd`.

---

## 7. SMTP Password

```
Prompt:    SMTP password (hidden input)
Validator: Required (non-empty)
```

Password for the upstream SMTP account. Input is hidden using `getpass`. Stored in `/etc/postfix/sasl_passwd` (mode `0600`, root-only).

The password is cleared from memory after the SASL configuration step completes.

---

## 8. DKIM Selector

```
Prompt:    DKIM selector [relay]
Validator: Required (non-empty)
```

The DKIM key selector name. Appears in DNS as `<selector>._domainkey.yourdomain.com`.

Common values: `relay`, `mail`, `default`, `dkim`.

---

## 9. Enable DKIM

```
Prompt:    Enable DKIM signing? [Y/n]
Default:   yes
```

Whether to install and configure OpenDKIM for outbound DKIM signing. **Strongly recommended** — without DKIM, emails will likely land in spam.

When enabled, the script:

- Installs `opendkim` and `opendkim-tools`
- Generates a 2048-bit RSA key pair
- Configures OpenDKIM with KeyTable, SigningTable, and TrustedHosts
- Wires the milter into Postfix
- Displays the DKIM DNS record to publish

---

## 10. Enable UFW Firewall

```
Prompt:    Enable UFW firewall rules? [Y/n]
Default:   yes
```

Whether to configure UFW to restrict inbound port 25 to trusted IPs only. **Recommended** to prevent open-relay abuse.

When enabled, the script:

- Allows SSH (to prevent lockout)
- Allows port 25 from each trusted IP/CIDR
- Allows loopback traffic
- Denies port 25 from all other sources
- Force-enables UFW

---

## 11. Rate Limit

```
Prompt:    Rate limit (msgs/client) [100]
Validator: Positive integer
```

Sets `smtpd_client_message_rate_limit` in Postfix — the maximum number of messages a single client can send per time unit (60 seconds by default).

Additionally, the script sets:

- `smtpd_client_connection_count_limit = 20`
- `smtpd_client_connection_rate_limit = 30`
- `anvil_rate_time_unit = 60s`

---

## 12. Admin Email

```
Prompt:    Admin email
Validator: Must contain @ and a dot in the domain part
```

Used as the `rua` (aggregate report) and `ruf` (forensic report) address in the generated DMARC DNS record. DMARC reports will be sent here.
