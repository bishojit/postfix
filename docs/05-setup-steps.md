# Setup Steps

The script executes 9 steps sequentially. Each step reports pass/fail. On failure, you're prompted to continue or abort.

---

## Step 1 — System Check

**Validates the environment before making changes.**

| Check                 | Behavior on failure                    |
| --------------------- | -------------------------------------- |
| Running as root       | Error (most steps need root)           |
| OS is Ubuntu/Debian   | Warning (continues but may fail later) |
| `apt` is available    | Error                                  |
| Hostname and local IP | Informational display                  |

---

## Step 2 — Install Packages

**Installs required system packages via `apt`.**

1. Pre-seeds debconf to suppress interactive prompts during Postfix install
2. Runs `apt-get update`
3. Installs packages:
   - `postfix`
   - `mailutils`
   - `libsasl2-modules`
   - `opendkim` + `opendkim-tools` (if DKIM is enabled)

Uses `DEBIAN_FRONTEND=noninteractive` for unattended operation.

---

## Step 3 — Configure `/etc/mailname`

**Writes the relay hostname to `/etc/mailname`.**

Postfix reads this file to determine the system's mail name when `myorigin = /etc/mailname` is set. File permissions: `0644`.

---

## Step 4 — Write `/etc/postfix/main.cf`

**Generates the full Postfix configuration from a template.**

The generated config includes:

| Section       | Key directives                                                 |
| ------------- | -------------------------------------------------------------- |
| Identity      | `myhostname`, `myorigin`, `mydomain`                           |
| Network       | `inet_interfaces = all`, `inet_protocols = ipv4`, `mynetworks` |
| Relay         | `relayhost = [host]:port`                                      |
| SASL Auth     | `smtp_sasl_auth_enable = yes`, password maps                   |
| TLS           | `encrypt` level, disabled SSLv2/v3/TLSv1/1.1, high ciphers     |
| Restrictions  | `permit_mynetworks`, `reject_unauth_destination`               |
| Anti-spam     | HELO required, sender restrictions                             |
| Rate Limiting | Per-client message and connection limits                       |
| Queue         | 1-day max lifetime, 6h bounce lifetime                         |
| Message Size  | 10 MB limit                                                    |
| Milter        | OpenDKIM socket (enabled or commented out)                     |

File permissions: `0644`.

---

## Step 5 — Configure SASL Credentials

**Sets up upstream SMTP authentication.**

1. Writes `/etc/postfix/sasl_passwd` with the format:
   ```
   [smtp.host]:port username:password
   ```
2. Runs `postmap` to generate the binary `.db` lookup file
3. Sets ownership to `root:root` and permissions to `0600`
4. Clears the password from script memory

> The SMTP password is stored in plaintext in `sasl_passwd` — this is required by Postfix. File permissions restrict access to root only.

---

## Step 6 — Configure OpenDKIM

**Sets up DKIM email signing.** Skipped if DKIM is disabled.

1. Creates directory structure:
   - `/etc/opendkim/keys/<domain>/`
   - `/var/spool/postfix/opendkim/`

2. Writes configuration files:
   - `/etc/opendkim.conf` — main config (domain, selector, socket, algorithm)
   - `/etc/opendkim/KeyTable` — maps domains to key files
   - `/etc/opendkim/SigningTable` — maps sender addresses to DKIM selectors
   - `/etc/opendkim/TrustedHosts` — localhost + relay hostname

3. Generates a 2048-bit RSA key pair (skips if key already exists)

4. Sets file ownership and permissions:
   - Key directory: `700`
   - Private key: `600`
   - Owner: `opendkim:opendkim`

5. Adds `postfix` user to the `opendkim` group for socket access

6. Displays the DKIM public key DNS record

**Socket type:** Uses a Unix domain socket at `/var/spool/postfix/opendkim/opendkim.sock` (inside the Postfix chroot).

---

## Step 7 — Configure UFW Firewall

**Restricts inbound SMTP access.** Skipped if UFW is disabled.

Rules applied (in order):

| Rule                                           | Purpose                              |
| ---------------------------------------------- | ------------------------------------ |
| `ufw allow OpenSSH`                            | Prevent SSH lockout                  |
| `ufw allow from <IP> to any port 25 proto tcp` | Allow SMTP from each trusted IP      |
| `ufw allow in on lo`                           | Allow loopback traffic               |
| `ufw deny 25/tcp`                              | Block port 25 from all other sources |
| `ufw --force enable`                           | Activate the firewall                |

---

## Step 8 — Restart Services

**Restarts and enables all configured services.**

- `opendkim` (if DKIM enabled) — restarted first
- `postfix` — restarted second

Both services are enabled for auto-start on boot via `systemctl enable`.

---

## Step 9 — Display DNS Records

**Generates and displays the DNS records you need to publish.**

Records shown:

| Type | Host                                   | Purpose                   |
| ---- | -------------------------------------- | ------------------------- |
| A    | `relay.yourdomain.com`                 | Points to relay server IP |
| TXT  | `yourdomain.com`                       | SPF record                |
| TXT  | `<selector>._domainkey.yourdomain.com` | DKIM public key           |
| TXT  | `_dmarc.yourdomain.com`                | DMARC policy              |

See [06-dns-records.md](06-dns-records.md) for detailed guidance.
