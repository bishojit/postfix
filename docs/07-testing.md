# Testing

## From the Relay Server

### Send a Test Email

```bash
echo "Relay test body" | mail -s "Relay Test - $(date)" you@example.com
```

### Watch the Mail Log

```bash
tail -f /var/log/mail.log
```

A successful delivery shows:

```
status=sent (250 OK)
```

### Check the Mail Queue

```bash
mailq
```

An empty queue means all messages were delivered. If messages are stuck, see [10-troubleshooting.md](10-troubleshooting.md).

---

## From an App Server

### Verify Port 25 Connectivity

```bash
telnet <RELAY_SERVER_IP> 25
```

Expected: an SMTP banner like `220 relay.yourdomain.com ESMTP Postfix`.

If you get `Connection refused` or timeout, check:

- UFW rules on the relay server
- Network/security group rules at the hosting provider
- The app server IP is in the trusted IPs list

### Send a Test Message

```bash
echo "Test from app server" | sendmail -v -S <RELAY_SERVER_IP>:25 you@example.com
```

Or configure your application's SMTP settings:

| Setting      | Value                            |
| ------------ | -------------------------------- |
| Host         | `<RELAY_SERVER_IP>`              |
| Port         | `25`                             |
| Encryption   | None (internal trusted network)  |
| Username     | _(leave empty — IP-whitelisted)_ |
| Password     | _(leave empty)_                  |
| From address | `noreply@yourdomain.com`         |

---

## Verify Email Authentication

### Online Tools

- **[mail-tester.com](https://www.mail-tester.com)** — Send to the provided address for a full score
- **[MXToolbox Header Analyzer](https://mxtoolbox.com/EmailHeaders.aspx)** — Paste email headers for analysis

### What to Check

| Check    | Expected Result      |
| -------- | -------------------- |
| SPF      | `pass`               |
| DKIM     | `pass`               |
| DMARC    | `pass`               |
| PTR/rDNS | Matches `myhostname` |

### Verify DKIM Signing Locally

```bash
opendkim-testkey -d yourdomain.com -s relay -vvv
```

Expected output includes `key OK`.

---

## Verify Postfix Configuration

```bash
# Syntax check
postfix check

# Show all non-default configuration values
postconf -n
```
