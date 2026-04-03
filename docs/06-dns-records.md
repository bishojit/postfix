# DNS Records

After running `setup.py`, you must publish DNS records for your sending domain. The script displays the exact values in **Step 9** and then **verifies them live** in **Step 10**. Add any missing records at your domain registrar or DNS provider.

> Allow 30–60 minutes for DNS propagation before testing. You can re-run `setup.py` or `debug.py` to re-check.

---

## A Record

Points the relay hostname to your server's public IP.

| Type | Host                   | Value                |
| ---- | ---------------------- | -------------------- |
| A    | `relay.yourdomain.com` | `<SERVER_PUBLIC_IP>` |

---

## PTR / Reverse DNS

The reverse DNS of your server IP **must match** the relay hostname. This is set at your hosting provider, not your DNS registrar.

```
<SERVER_PUBLIC_IP>  →  PTR  →  relay.yourdomain.com
```

Contact your provider (OVH, Hetzner, DigitalOcean, etc.) to configure this.

---

## SPF Record

Specifies which servers are authorized to send email for your domain.

| Type | Host             | Value                                               |
| ---- | ---------------- | --------------------------------------------------- |
| TXT  | `yourdomain.com` | `v=spf1 ip4:<RELAY_IP> a:relay.yourdomain.com ~all` |

The script auto-generates this from your trusted IPs. If you have an existing SPF record, **merge** the `ip4:` entries rather than creating a duplicate TXT record (only one SPF record per domain is allowed).

---

## DKIM Record

Publishes the DKIM public key so receiving servers can verify email signatures.

| Type | Host                              | Value                                      |
| ---- | --------------------------------- | ------------------------------------------ |
| TXT  | `relay._domainkey.yourdomain.com` | `v=DKIM1; h=sha256; k=rsa; p=<PUBLIC_KEY>` |

The exact value is displayed by the script (step 9) and also available in:

```bash
cat /etc/opendkim/keys/yourdomain.com/relay.txt
```

> Some DNS providers have a 255-character limit per TXT record string. If your key is long, split it into multiple quoted strings — most providers handle this automatically.

### Verify DKIM DNS

```bash
opendkim-testkey -d yourdomain.com -s relay -vvv
```

Expected output: `key OK`

---

## DMARC Record

Tells receiving servers what to do with email that fails SPF/DKIM checks.

| Type | Host                    | Value                                                                                            |
| ---- | ----------------------- | ------------------------------------------------------------------------------------------------ |
| TXT  | `_dmarc.yourdomain.com` | `v=DMARC1; p=quarantine; rua=mailto:admin@yourdomain.com; ruf=mailto:admin@yourdomain.com; fo=1` |

The `rua` and `ruf` addresses use the admin email you provided during setup.

### DMARC Policy Options

| Policy       | Behavior                                 |
| ------------ | ---------------------------------------- |
| `none`       | Monitor only (good for initial rollout)  |
| `quarantine` | Send failing mail to spam (the default)  |
| `reject`     | Reject failing mail entirely (strictest) |

Start with `quarantine` and move to `reject` once you've confirmed everything passes.

---

## DNS Verification Checklist

After adding all records, verify with:

```bash
# SPF
dig TXT yourdomain.com +short

# DKIM
dig TXT relay._domainkey.yourdomain.com +short

# DMARC
dig TXT _dmarc.yourdomain.com +short

# PTR
dig -x <SERVER_PUBLIC_IP> +short

# A record
dig A relay.yourdomain.com +short
```
