# Troubleshooting

## Common Issues

### Connection refused on port 25

| Cause                                   | Fix                                            |
| --------------------------------------- | ---------------------------------------------- |
| UFW blocking the source IP              | `ufw allow from <IP> to any port 25 proto tcp` |
| Postfix not listening on all interfaces | Verify `inet_interfaces = all` in `main.cf`    |
| Postfix not running                     | `systemctl start postfix`                      |
| Cloud provider blocking port 25         | Contact provider or use a different server     |

```bash
# Check if Postfix is listening
ss -tlnp | grep :25

# Check UFW status
ufw status verbose
```

---

### Relay access denied

The sending server's IP is not in `mynetworks`.

```bash
# Check current mynetworks value
postconf mynetworks

# Add the IP to /etc/postfix/main.cf
# Then reload
systemctl reload postfix
```

---

### Authentication failed (upstream SMTP)

```bash
# Verify credentials file
cat /etc/postfix/sasl_passwd

# Regenerate the hash database
postmap /etc/postfix/sasl_passwd

# Restart Postfix
systemctl restart postfix
```

Check `mail.log` for the specific error:

```bash
grep "authentication failed" /var/log/mail.log
```

---

### TLS handshake failed

```bash
# Check upstream SMTP supports STARTTLS
openssl s_client -starttls smtp -connect smtp.provider.com:587

# Verify CA certificates file exists
ls -la /etc/ssl/certs/ca-certificates.crt

# If missing, reinstall
apt install --reinstall ca-certificates
```

---

### Emails landing in spam

| Check            | Command                                            |
| ---------------- | -------------------------------------------------- |
| SPF record       | `dig TXT yourdomain.com +short`                    |
| DKIM record      | `dig TXT relay._domainkey.yourdomain.com +short`   |
| DMARC record     | `dig TXT _dmarc.yourdomain.com +short`             |
| DKIM signing     | `opendkim-testkey -d yourdomain.com -s relay -vvv` |
| PTR record       | `dig -x <SERVER_IP> +short`                        |
| Open relay check | [MXToolbox](https://mxtoolbox.com/diagnostic.aspx) |

All of SPF, DKIM, and DMARC must pass. Use [mail-tester.com](https://www.mail-tester.com) for a comprehensive score.

---

### Queue growing / messages not draining

```bash
# View the queue
mailq

# Check for error patterns
grep "status=deferred" /var/log/mail.log | tail -20

# Force retry all queued messages
postqueue -f
```

Common causes:

- Upstream SMTP credentials are wrong
- Upstream SMTP is down or rate-limiting you
- DNS resolution failure on the relay server

---

### OpenDKIM not signing emails

```bash
# Check OpenDKIM is running
systemctl status opendkim

# Check the milter socket exists
ls -la /var/spool/postfix/opendkim/opendkim.sock

# Verify Postfix milter config
postconf smtpd_milters non_smtpd_milters

# Check OpenDKIM logs
journalctl -u opendkim --since "1 hour ago"
```

Common fixes:

- Restart `opendkim` before `postfix`
- Ensure `postfix` user is in the `opendkim` group: `usermod -aG opendkim postfix`
- Check socket path matches between `opendkim.conf` and `main.cf`

---

### Script fails at "debconf-set-selections"

This usually means `debconf-utils` is not installed:

```bash
apt install debconf-utils -y
# Then re-run setup.py
```

---

## Diagnostic Commands

```bash
# Full Postfix config audit
postconf -n

# Syntax validation
postfix check

# Check service logs
journalctl -u postfix -u opendkim --since "1 hour ago" --no-pager

# Test SMTP connection manually
telnet localhost 25

# Check DNS resolution from the server
dig MX yourdomain.com
dig A relay.yourdomain.com
```
