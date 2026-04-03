# Prerequisites

## System Requirements

| Requirement         | Details                                                  |
| ------------------- | -------------------------------------------------------- |
| **OS**              | Ubuntu 22.04+ LTS or Debian 11+                          |
| **Python**          | 3.6+ (pre-installed on Ubuntu/Debian)                    |
| **Privileges**      | Must run as `root` (or via `sudo`)                       |
| **Package Manager** | `apt` / `apt-get` must be available                      |
| **Network**         | Outbound port 587 must be open to the upstream SMTP host |

## Server Provisioning

You need a VPS or dedicated server **where outbound port 25 is not blocked**. This server will act as your relay.

Common providers with unblocked SMTP:

- Hetzner (on request)
- DigitalOcean (on request)
- Vultr (on request)
- Self-hosted / on-premises

## DNS Requirements

Before running the script, set up these DNS records:

### A Record (required)

Point your relay hostname to the server's public IP:

```
relay.yourdomain.com  →  A  →  <SERVER_PUBLIC_IP>
```

### PTR / Reverse DNS (required)

The reverse DNS (rDNS) of your server IP **must match** the relay hostname. Contact your hosting provider to set this — it cannot be done via your domain registrar.

```
<SERVER_PUBLIC_IP>  →  PTR  →  relay.yourdomain.com
```

> Without a matching PTR record, many mail servers will reject or spam-flag your email.

### Additional DNS Records (after setup)

The script generates the exact SPF, DKIM, and DMARC records you need. See [06-dns-records.md](06-dns-records.md) for details.

## Information You Need

Gather these before running the script:

| Parameter              | Example                | Where to find it                                     |
| ---------------------- | ---------------------- | ---------------------------------------------------- |
| Relay server public IP | `203.0.113.10`         | `curl ifconfig.me` on the server                     |
| Relay hostname (FQDN)  | `relay.yourdomain.com` | Your DNS A record                                    |
| Sending domain         | `yourdomain.com`       | Your organization's domain                           |
| Trusted app server IPs | `51.79.226.156`        | IPs of servers that will send mail through the relay |
| Upstream SMTP host     | `smtp.n8nclouds.com`   | From your SMTP provider                              |
| Upstream SMTP port     | `587`                  | From your SMTP provider (usually 587)                |
| SMTP username          | `user@provider.com`    | From your SMTP provider                              |
| SMTP password          | `••••••••`             | From your SMTP provider                              |
| Admin email            | `admin@yourdomain.com` | For DMARC aggregate reports                          |
