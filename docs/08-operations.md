# Operations & Maintenance

## Service Management

```bash
# Check service status
systemctl status postfix
systemctl status opendkim

# Restart services
systemctl restart postfix
systemctl restart opendkim

# View service logs
journalctl -u postfix --since "1 hour ago"
journalctl -u opendkim --since "1 hour ago"
```

---

## Mail Queue

```bash
# View the queue
mailq

# Flush (retry) all queued messages
postqueue -f

# Delete ALL queued messages (use with care)
postsuper -d ALL

# Inspect a specific queued message
postcat -q <QUEUE_ID>

# Delete a specific message
postsuper -d <QUEUE_ID>
```

---

## Log Monitoring

Mail logs are at `/var/log/mail.log`:

```bash
# Live tail
tail -f /var/log/mail.log

# Errors only
tail -f /var/log/mail.err

# Find bounces
grep "status=bounced" /var/log/mail.log

# Find deferred messages
grep "status=deferred" /var/log/mail.log

# Count sent messages today
grep "status=sent" /var/log/mail.log | grep "$(date +%b\ %e)" | wc -l
```

---

## Configuration Changes

### Changing Postfix Settings

Edit `/etc/postfix/main.cf`, then:

```bash
postfix check        # Validate syntax
systemctl reload postfix
```

### Changing SMTP Credentials

```bash
# Edit the credentials file
nano /etc/postfix/sasl_passwd

# Regenerate the hash database
postmap /etc/postfix/sasl_passwd

# Secure permissions
chmod 600 /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db

# Reload Postfix
systemctl reload postfix
```

### Adding Trusted IPs

1. Add the IP to `mynetworks` in `/etc/postfix/main.cf`
2. Add a UFW rule: `ufw allow from <NEW_IP> to any port 25 proto tcp`
3. Reload Postfix: `systemctl reload postfix`

### Rotating DKIM Keys

```bash
# Generate a new key with a new selector
opendkim-genkey -b 2048 -d yourdomain.com \
  -D /etc/opendkim/keys/yourdomain.com -s relay2 -v

# Update /etc/opendkim.conf — change Selector to "relay2"
# Update /etc/opendkim/KeyTable and SigningTable
# Publish the new DKIM DNS record
# Restart opendkim
systemctl restart opendkim
systemctl restart postfix

# Keep the old DNS record for 48h to allow propagation
```

---

## Audit

```bash
# Show all non-default Postfix settings
postconf -n

# Check firewall rules
ufw status verbose

# Check listening ports
ss -tlnp | grep -E '25|587'
```
