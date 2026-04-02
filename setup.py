#!/usr/bin/env python3
"""
Postfix SMTP Relay Server - Production Setup Script
Automates full Postfix relay server configuration on Ubuntu/Debian.
"""

import os
import sys
import subprocess
import socket
import getpass
import platform
import shutil
from datetime import datetime, timezone

# ─── ANSI Colour Helpers ─────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"


def red(msg):    return f"{RED}{msg}{RESET}"
def green(msg):  return f"{GREEN}{msg}{RESET}"
def yellow(msg): return f"{YELLOW}{msg}{RESET}"
def cyan(msg):   return f"{CYAN}{msg}{RESET}"
def bold(msg):   return f"{BOLD}{msg}{RESET}"


def print_success(msg): print(green(f"  ✔  {msg}"))
def print_warn(msg):    print(yellow(f"  ⚠  {msg}"))
def print_error(msg):   print(red(f"  ✘  {msg}"))
def print_info(msg):    print(yellow(f"  ℹ  {msg}"))
def print_step(n, total, title):
    print()
    print(cyan(f"{'─' * 60}"))
    print(cyan(f"  Step {n} of {total} — {title}"))
    print(cyan(f"{'─' * 60}"))


# ─── Banner ──────────────────────────────────────────────────────────────────

BANNER = r"""
  ██████╗  ██████╗ ███████╗████████╗███████╗██╗██╗  ██╗
  ██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝██╔════╝██║╚██╗██╔╝
  ██████╔╝██║   ██║███████╗   ██║   █████╗  ██║ ╚███╔╝
  ██╔═══╝ ██║   ██║╚════██║   ██║   ██╔══╝  ██║ ██╔██╗
  ██║     ╚██████╔╝███████║   ██║   ██║     ██║██╔╝ ██╗
  ╚═╝      ╚═════╝ ╚══════╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝

        SMTP Relay Server — Production Setup v1.0
"""


def print_banner():
    print(cyan(BANNER))
    print(cyan("  Automated Postfix relay configuration for Ubuntu/Debian"))
    print(cyan("  Uses only Python 3 standard library — no external dependencies"))
    print()


# ─── Step tracking ───────────────────────────────────────────────────────────

TOTAL_STEPS = 9
step_results = []   # list of (title, passed: bool, note: str)


def record(title, passed, note=""):
    step_results.append((title, passed, note))


# ─── Utilities ───────────────────────────────────────────────────────────────

def run(cmd, env_extra=None, check=True, capture=False):
    """Run a shell command, return (returncode, stdout, stderr)."""
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    result = subprocess.run(
        cmd,
        shell=isinstance(cmd, str),
        env=env,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        text=True,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip() if capture else ""
        raise RuntimeError(f"Command failed (rc={result.returncode}): {cmd}\n{stderr}")
    return result


def write_file(path, content, mode=0o640):
    """Write content to a file (create or overwrite)."""
    with open(path, "w") as fh:
        fh.write(content)
    os.chmod(path, mode)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def ask(prompt_text, default="", secret=False, validator=None):
    """
    Prompt the user for input.
    - Shows [default] hint when a default exists.
    - Hides input for secret fields.
    - Retries on failed validation.
    """
    hint = f" [{default}]" if default else ""
    full_prompt = yellow(f"  → {prompt_text}{hint}: ")
    while True:
        if secret:
            value = getpass.getpass(full_prompt)
        else:
            value = input(full_prompt).strip()
        if not value:
            value = default
        if validator:
            error = validator(value)
            if error:
                print_error(error)
                continue
        if not value:
            print_error("This field is required.")
            continue
        return value


def ask_yes_no(prompt_text, default="yes"):
    """Ask a yes/no question, return True for yes."""
    hint = "[Y/n]" if default.lower() == "yes" else "[y/N]"
    full_prompt = yellow(f"  → {prompt_text} {hint}: ")
    while True:
        value = input(full_prompt).strip().lower()
        if not value:
            return default.lower() == "yes"
        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False
        print_error("Please enter 'y' or 'n'.")


def confirm_continue(step_name):
    """After a step failure, ask whether to continue or abort."""
    print()
    choice = ask_yes_no(
        f"Step '{step_name}' failed. Continue anyway?", default="no"
    )
    if not choice:
        print_error("Aborting setup at user request.")
        print_final_summary()
        sys.exit(1)


# ─── Validators ──────────────────────────────────────────────────────────────

def validate_hostname(v):
    if not v or "." not in v:
        return "Must be a fully-qualified domain name (e.g. relay.example.com)"
    return None


def validate_domain(v):
    if not v or "." not in v:
        return "Must be a valid domain name (e.g. example.com)"
    return None


def validate_port(v):
    try:
        port = int(v)
        if not (1 <= port <= 65535):
            raise ValueError
        return None
    except (ValueError, TypeError):
        return "Must be a valid port number between 1 and 65535"


def validate_rate(v):
    try:
        n = int(v)
        if n < 1:
            raise ValueError
        return None
    except (ValueError, TypeError):
        return "Must be a positive integer"


def validate_email(v):
    if not v or "@" not in v or "." not in v.split("@")[-1]:
        return "Must be a valid email address (e.g. admin@example.com)"
    return None


def normalize_ip_list(raw):
    """
    Accept comma-separated IPs / CIDRs. Ensure single IPs get /32.
    Always include 127.0.0.0/8.
    Returns a formatted string for mynetworks.
    """
    networks = {"127.0.0.0/8"}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "/" not in part:
            part = f"{part}/32"
        networks.add(part)
    return " ".join(sorted(networks))


# ─── Parameter collection ────────────────────────────────────────────────────

def collect_parameters():
    print(cyan("\n  ╔══════════════════════════════════════════════════════╗"))
    print(cyan("  ║         CONFIGURATION PARAMETERS                    ║"))
    print(cyan("  ╚══════════════════════════════════════════════════════╝"))
    print(yellow("  Please answer the following questions.\n"
                 "  Press Enter to accept the [default] value where shown.\n"))

    params = {}

    # Relay hostname
    print(yellow("  [1/12] Relay Hostname"))
    print(yellow("         Fully qualified domain name for this relay server\n"
                 "         (must match your DNS A record)."))
    params["relay_hostname"] = ask(
        "Relay hostname",
        default="relay.yourdomain.com",
        validator=validate_hostname,
    )

    # Sending domain
    print()
    print(yellow("  [2/12] Sending Domain"))
    print(yellow("         Your primary email sending domain (e.g. yourdomain.com)."))
    params["sending_domain"] = ask(
        "Sending domain",
        validator=validate_domain,
    )

    # Trusted IPs
    print()
    print(yellow("  [3/12] Trusted App Server IPs"))
    print(yellow("         Comma-separated list of app server IPs allowed to relay\n"
                 "         through this server (e.g. 51.79.226.156).\n"
                 "         127.0.0.0/8 is always included automatically."))
    raw_ips = ask(
        "Trusted IPs (comma-separated)",
        default="127.0.0.0/8",
    )
    params["trusted_ips_raw"] = raw_ips
    params["mynetworks"] = normalize_ip_list(raw_ips)

    # SMTP host
    print()
    print(yellow("  [4/12] Upstream SMTP Host"))
    print(yellow("         The upstream SMTP relay host your server will forward\n"
                 "         all outbound mail through."))
    params["smtp_host"] = ask(
        "Upstream SMTP host",
        default="smtp.n8nclouds.com",
        validator=validate_hostname,
    )

    # SMTP port
    print()
    print(yellow("  [5/12] Upstream SMTP Port"))
    print(yellow("         Upstream SMTP port — usually 587 for STARTTLS."))
    params["smtp_port"] = ask(
        "Upstream SMTP port",
        default="587",
        validator=validate_port,
    )

    # SMTP user
    print()
    print(yellow("  [6/12] SMTP Username"))
    print(yellow("         Username for authenticating to the upstream SMTP server."))
    params["smtp_user"] = ask("SMTP username")

    # SMTP password
    print()
    print(yellow("  [7/12] SMTP Password"))
    print(yellow("         Password for the upstream SMTP account.\n"
                 "         Input will be hidden."))
    params["smtp_pass"] = ask("SMTP password", secret=True)

    # DKIM selector
    print()
    print(yellow("  [8/12] DKIM Selector"))
    print(yellow("         DKIM key selector name.\n"
                 "         Will appear as <selector>._domainkey in DNS."))
    params["dkim_selector"] = ask(
        "DKIM selector",
        default="relay",
    )

    # Enable DKIM
    print()
    print(yellow("  [9/12] Enable DKIM"))
    print(yellow("         Install and configure OpenDKIM for outbound email signing.\n"
                 "         Strongly recommended for deliverability."))
    params["enable_dkim"] = ask_yes_no(
        "Enable DKIM signing?", default="yes"
    )

    # Enable UFW
    print()
    print(yellow("  [10/12] Enable UFW Firewall Rules"))
    print(yellow("          Add UFW rules to restrict port 25 to trusted IPs only.\n"
                 "          Recommended to prevent open-relay abuse."))
    params["enable_ufw"] = ask_yes_no(
        "Enable UFW firewall rules?", default="yes"
    )

    # Rate limit
    print()
    print(yellow("  [11/12] Rate Limit"))
    print(yellow("          Maximum messages per client connection\n"
                 "          (smtpd_client_message_rate_limit)."))
    params["rate_limit"] = ask(
        "Rate limit (msgs/client)",
        default="100",
        validator=validate_rate,
    )

    # Admin email
    print()
    print(yellow("  [12/12] Admin Email"))
    print(yellow("          Admin email address used as the 'rua' tag in the\n"
                 "          generated DMARC DNS record for receiving reports."))
    params["admin_email"] = ask(
        "Admin email",
        validator=validate_email,
    )

    return params


# ─── Summary & confirmation ───────────────────────────────────────────────────

def show_summary(params):
    print()
    print(cyan("  ╔══════════════════════════════════════════════════════╗"))
    print(cyan("  ║              CONFIGURATION SUMMARY                  ║"))
    print(cyan("  ╚══════════════════════════════════════════════════════╝"))
    rows = [
        ("Relay hostname",        params["relay_hostname"]),
        ("Sending domain",        params["sending_domain"]),
        ("Trusted IPs",           params["mynetworks"]),
        ("Upstream SMTP host",    params["smtp_host"]),
        ("Upstream SMTP port",    params["smtp_port"]),
        ("SMTP username",         params["smtp_user"]),
        ("SMTP password",         "●●●●●●●●"),
        ("DKIM selector",         params["dkim_selector"]),
        ("Enable DKIM",           "yes" if params["enable_dkim"] else "no"),
        ("Enable UFW",            "yes" if params["enable_ufw"] else "no"),
        ("Rate limit",            params["rate_limit"]),
        ("Admin email",           params["admin_email"]),
    ]
    for label, value in rows:
        print(f"  {cyan(label + ':'):<38}  {bold(value)}")
    print()


# ─── main.cf template ────────────────────────────────────────────────────────

MAIN_CF_TEMPLATE = """\
# ─── Generated by setup.py on {timestamp} ─────────────────────
# ─── Identity ────────────────────────────────────────────────────────────────
myhostname = {relay_hostname}
myorigin = /etc/mailname
mydomain = {sending_domain}

# ─── Network ─────────────────────────────────────────────────────────────────
inet_interfaces = all
inet_protocols = ipv4
mynetworks = {mynetworks}

# ─── Relay ───────────────────────────────────────────────────────────────────
relayhost = [{smtp_host}]:{smtp_port}

# ─── Outbound SASL Auth ──────────────────────────────────────────────────────
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous

# ─── Outbound TLS ────────────────────────────────────────────────────────────
smtp_use_tls = yes
smtp_tls_security_level = encrypt
smtp_tls_note_starttls_offer = yes
smtp_tls_loglevel = 1
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
smtp_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_ciphers = high

# ─── Inbound Relay Restrictions ──────────────────────────────────────────────
smtpd_recipient_restrictions =
    permit_mynetworks,
    reject_unauth_destination

# ─── Anti-spam / Hardening ───────────────────────────────────────────────────
smtpd_helo_required = yes
smtpd_helo_restrictions =
    permit_mynetworks,
    reject_invalid_helo_hostname,
    reject_non_fqdn_helo_hostname,
    permit

smtpd_sender_restrictions =
    permit_mynetworks,
    reject_non_fqdn_sender,
    reject_unknown_sender_domain,
    permit

# ─── Rate Limiting ───────────────────────────────────────────────────────────
smtpd_client_message_rate_limit = {rate_limit}
smtpd_client_connection_count_limit = 20
smtpd_client_connection_rate_limit = 30
anvil_rate_time_unit = 60s

# ─── Queue / Delivery ────────────────────────────────────────────────────────
maximal_queue_lifetime = 1d
bounce_queue_lifetime = 6h
maximal_backoff_time = 1h
minimal_backoff_time = 5m

# ─── Message Size ────────────────────────────────────────────────────────────
message_size_limit = 10240000

# ─── Misc ────────────────────────────────────────────────────────────────────
append_dot_mydomain = no
readme_directory = no
compatibility_level = 3.6
{milter_section}
"""

MILTER_SECTION_ENABLED = """\
# ─── OpenDKIM Milter ─────────────────────────────────────────────────────────
milter_default_action = accept
milter_protocol = 6
smtpd_milters = local:opendkim/opendkim.sock
non_smtpd_milters = local:opendkim/opendkim.sock
"""

MILTER_SECTION_DISABLED = """\
# ─── OpenDKIM Milter (disabled) ──────────────────────────────────────────────
# milter_default_action = accept
# milter_protocol = 6
# smtpd_milters = local:opendkim/opendkim.sock
# non_smtpd_milters = local:opendkim/opendkim.sock
"""


# ─── OpenDKIM config templates ───────────────────────────────────────────────

OPENDKIM_CONF_TEMPLATE = """\
# Generated by setup.py
Syslog                  yes
SyslogSuccess           yes
LogWhy                  yes

Canonicalization        relaxed/simple
Domain                  {sending_domain}
Selector                {dkim_selector}

KeyFile                 /etc/opendkim/keys/{sending_domain}/{dkim_selector}.private

Mode                    sv
PidFile                 /run/opendkim/opendkim.pid
SignatureAlgorithm      rsa-sha256

UserID                  opendkim:opendkim
UMask                   007

Socket                  local:/var/spool/postfix/opendkim/opendkim.sock

OversignHeaders         From
"""

OPENDKIM_TABLE_TEMPLATE = """\
*@{sending_domain}    {sending_domain}:{dkim_selector}:/etc/opendkim/keys/{sending_domain}/{dkim_selector}.private
"""

OPENDKIM_SIGNING_TABLE_TEMPLATE = """\
*@{sending_domain}    {dkim_selector}._domainkey.{sending_domain}
"""

TRUSTED_HOSTS_TEMPLATE = """\
127.0.0.1
localhost
{relay_hostname}
"""


# ─── Step functions ──────────────────────────────────────────────────────────

def step_system_check(params):
    """Step 1 — System Check"""
    step_name = "System Check"
    errors = []

    # Root check
    if os.geteuid() != 0:
        print_error("Not running as root!")
        errors.append("Not running as root")
    else:
        print_success("Running as root")

    # OS check
    os_info = platform.platform()
    print_info(f"Platform: {os_info}")
    distro_id = ""
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    distro_id = line.strip().split("=", 1)[1].strip('"').lower()
                    break
    if distro_id in ("ubuntu", "debian"):
        print_success(f"OS: {distro_id.capitalize()} (supported)")
    else:
        msg = f"OS '{distro_id}' is not Ubuntu/Debian — setup may fail"
        print_warn(msg)
        errors.append(msg)

    # apt check
    if shutil.which("apt") or shutil.which("apt-get"):
        print_success("apt is available")
    else:
        msg = "apt not found"
        print_error(msg)
        errors.append(msg)

    # Hostname / IP
    hostname = socket.gethostname()
    local_ip = get_local_ip()
    print_info(f"Hostname: {hostname}")
    print_info(f"Local IP: {local_ip}")

    passed = len(errors) == 0
    note = "; ".join(errors) if errors else ""
    record(step_name, passed, note)
    return passed


def step_install_packages(params):
    """Step 2 — Install Packages"""
    step_name = "Install Packages"
    try:
        env = {"DEBIAN_FRONTEND": "noninteractive"}

        # Pre-seed debconf using subprocess list to avoid shell injection
        hostname = params['relay_hostname']
        preseed = (
            f"postfix postfix/main_mailer_type select Internet Site\n"
            f"postfix postfix/mailname string {hostname}\n"
        ).encode()
        debconf_proc = subprocess.run(
            ["debconf-set-selections"],
            input=preseed,
            env={**os.environ, **env},
            capture_output=True,
        )
        if debconf_proc.returncode != 0:
            raise RuntimeError(
                f"debconf-set-selections failed: {debconf_proc.stderr.decode().strip()}"
            )
        print_success("Debconf pre-seeded for postfix")

        # apt update
        print_info("Running apt update …")
        run("apt-get update -qq", env_extra=env)
        print_success("apt update complete")

        # Package list
        packages = ["postfix", "mailutils", "libsasl2-modules"]
        if params["enable_dkim"]:
            packages += ["opendkim", "opendkim-tools"]

        pkg_str = " ".join(packages)
        print_info(f"Installing: {pkg_str} …")
        run(
            f"apt-get install -y -qq {pkg_str}",
            env_extra=env,
        )
        print_success(f"Packages installed: {pkg_str}")
        record(step_name, True)
        return True
    except RuntimeError as exc:
        print_error(str(exc))
        record(step_name, False, str(exc))
        return False


def step_configure_mailname(params):
    """Step 3 — Configure /etc/mailname"""
    step_name = "Configure /etc/mailname"
    try:
        write_file("/etc/mailname", params["relay_hostname"] + "\n", mode=0o644)
        print_success(f"/etc/mailname set to '{params['relay_hostname']}'")
        record(step_name, True)
        return True
    except OSError as exc:
        print_error(str(exc))
        record(step_name, False, str(exc))
        return False


def step_write_main_cf(params):
    """Step 4 — Write /etc/postfix/main.cf"""
    step_name = "Write /etc/postfix/main.cf"
    try:
        milter = MILTER_SECTION_ENABLED if params["enable_dkim"] else MILTER_SECTION_DISABLED
        content = MAIN_CF_TEMPLATE.format(
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            relay_hostname=params["relay_hostname"],
            sending_domain=params["sending_domain"],
            mynetworks=params["mynetworks"],
            smtp_host=params["smtp_host"],
            smtp_port=params["smtp_port"],
            rate_limit=params["rate_limit"],
            milter_section=milter,
        )
        write_file("/etc/postfix/main.cf", content, mode=0o644)
        print_success("/etc/postfix/main.cf written")
        record(step_name, True)
        return True
    except (OSError, KeyError) as exc:
        print_error(str(exc))
        record(step_name, False, str(exc))
        return False


def step_configure_sasl(params):
    """Step 5 — Configure SASL credentials"""
    step_name = "Configure SASL Credentials"
    try:
        print_warn("SMTP password will be stored in plaintext in /etc/postfix/sasl_passwd")
        print_warn("Access is restricted to root (mode 0600). Keep this file secure.")
        sasl_passwd = (
            f"[{params['smtp_host']}]:{params['smtp_port']} "
            f"{params['smtp_user']}:{params['smtp_pass']}\n"
        )
        write_file("/etc/postfix/sasl_passwd", sasl_passwd, mode=0o600)
        print_success("/etc/postfix/sasl_passwd written")

        run("postmap /etc/postfix/sasl_passwd")
        print_success("sasl_passwd.db generated with postmap")

        # Secure the files
        run("chown root:root /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db")
        run("chmod 0600 /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db")
        print_success("SASL files secured (root:root 600)")

        record(step_name, True)
        return True
    except (OSError, RuntimeError) as exc:
        print_error(str(exc))
        record(step_name, False, str(exc))
        return False


def step_configure_opendkim(params):
    """Step 6 — Configure OpenDKIM"""
    step_name = "Configure OpenDKIM"
    if not params["enable_dkim"]:
        print_info("DKIM disabled — skipping")
        record(step_name, True, "skipped (disabled)")
        return True
    try:
        domain = params["sending_domain"]
        selector = params["dkim_selector"]
        key_dir = f"/etc/opendkim/keys/{domain}"

        # Directories
        for d in ["/etc/opendkim/keys", key_dir,
                  "/var/spool/postfix/opendkim"]:
            os.makedirs(d, exist_ok=True)
        print_success("OpenDKIM directories created")

        # Main config
        write_file(
            "/etc/opendkim.conf",
            OPENDKIM_CONF_TEMPLATE.format(
                sending_domain=domain, dkim_selector=selector
            ),
            mode=0o644,
        )
        print_success("/etc/opendkim.conf written")

        # Key table
        write_file(
            "/etc/opendkim/KeyTable",
            OPENDKIM_TABLE_TEMPLATE.format(
                sending_domain=domain, dkim_selector=selector
            ),
            mode=0o644,
        )

        # Signing table
        write_file(
            "/etc/opendkim/SigningTable",
            OPENDKIM_SIGNING_TABLE_TEMPLATE.format(
                sending_domain=domain, dkim_selector=selector
            ),
            mode=0o644,
        )

        # Trusted hosts
        write_file(
            "/etc/opendkim/TrustedHosts",
            TRUSTED_HOSTS_TEMPLATE.format(
                relay_hostname=params["relay_hostname"]
            ),
            mode=0o644,
        )
        print_success("OpenDKIM tables and trusted hosts written")

        # Generate key pair (only if it doesn't already exist)
        private_key = f"{key_dir}/{selector}.private"
        if os.path.exists(private_key):
            print_warn(f"DKIM private key already exists: {private_key} — skipping generation")
        else:
            run(
                ["opendkim-genkey", "-b", "2048", "-d", domain,
                 "-D", key_dir, "-s", selector, "-v"],
                capture=True,
            )
            print_success(f"DKIM key pair generated: {key_dir}/{selector}.[private|txt]")

        # Ownership for the socket directory and keys (use list to avoid injection)
        run(["chown", "-R", "opendkim:opendkim",
             "/etc/opendkim", "/var/spool/postfix/opendkim"])
        run(["chmod", "700", key_dir])
        run(["chmod", "600", private_key])

        # Add postfix to opendkim group for socket access
        run("usermod -aG opendkim postfix", check=False)

        # Show public key for DNS
        txt_key_file = f"{key_dir}/{selector}.txt"
        if os.path.exists(txt_key_file):
            with open(txt_key_file) as f:
                dkim_dns = f.read()
            print()
            print(cyan("  ┌─── DKIM DNS Record (add to your DNS zone) ─────────────────"))
            for line in dkim_dns.strip().splitlines():
                print(cyan(f"  │  {line}"))
            print(cyan("  └────────────────────────────────────────────────────────────"))
            # Store for final summary
            params["_dkim_dns"] = dkim_dns.strip()

        record(step_name, True)
        return True
    except (OSError, RuntimeError) as exc:
        print_error(str(exc))
        record(step_name, False, str(exc))
        return False


def step_configure_ufw(params):
    """Step 7 — Configure UFW Firewall"""
    step_name = "Configure UFW"
    if not params["enable_ufw"]:
        print_info("UFW rules disabled — skipping")
        record(step_name, True, "skipped (disabled)")
        return True
    try:
        if not shutil.which("ufw"):
            print_warn("ufw not installed — installing …")
            run("apt-get install -y -qq ufw",
                env_extra={"DEBIAN_FRONTEND": "noninteractive"})

        # Allow SSH first to avoid locking out
        run("ufw allow OpenSSH", capture=True)
        print_success("UFW: SSH access permitted")

        # Allow SMTP only from trusted networks
        for network in params["mynetworks"].split():
            if network == "127.0.0.0/8":
                continue
            run(f"ufw allow from {network} to any port 25 proto tcp", capture=True)
            print_success(f"UFW: port 25 allowed from {network}")

        # Allow loopback for local delivery
        run("ufw allow in on lo", capture=True)
        print_success("UFW: loopback allowed")

        # Deny port 25 from everywhere else
        run("ufw deny 25/tcp", capture=True)
        print_success("UFW: port 25 denied from all other sources")

        # Enable UFW (non-interactive)
        run("ufw --force enable")
        print_success("UFW enabled")

        record(step_name, True)
        return True
    except RuntimeError as exc:
        print_error(str(exc))
        record(step_name, False, str(exc))
        return False


def step_restart_services(params):
    """Step 8 — Restart Services"""
    step_name = "Restart Services"
    errors = []

    services = ["postfix"]
    if params["enable_dkim"]:
        services.insert(0, "opendkim")

    for svc in services:
        try:
            run(f"systemctl restart {svc}")
            run(f"systemctl enable {svc}", check=False)
            print_success(f"Service '{svc}' restarted and enabled")
        except RuntimeError as exc:
            msg = f"Failed to restart {svc}: {exc}"
            print_error(msg)
            errors.append(msg)

    passed = len(errors) == 0
    record(step_name, passed, "; ".join(errors))
    return passed


def step_show_dns_records(params):
    """Step 9 — Display DNS records"""
    step_name = "DNS Records"
    domain = params["sending_domain"]
    relay_hostname = params["relay_hostname"]
    selector = params["dkim_selector"]
    admin_email = params["admin_email"]
    mynetworks = params["mynetworks"]

    # Build SPF record (include all trusted /32 IPs; use 'a:' for relay hostname)
    ip_includes = ""
    for net in mynetworks.split():
        if net == "127.0.0.0/8":
            continue
        if net.endswith("/32"):
            ip_includes += f" ip4:{net[:-3]}"
        else:
            ip_includes += f" ip4:{net}"

    spf_record = f"v=spf1{ip_includes} a:{relay_hostname} ~all"
    dmarc_record = f"v=DMARC1; p=quarantine; rua=mailto:{admin_email}; ruf=mailto:{admin_email}; fo=1"

    print()
    print(cyan("  ╔══════════════════════════════════════════════════════════════╗"))
    print(cyan("  ║             DNS RECORDS TO ADD                              ║"))
    print(cyan("  ╚══════════════════════════════════════════════════════════════╝"))

    print()
    print(cyan("  A Record (relay server):"))
    print(f"    {bold(relay_hostname)}  →  A  →  {bold('<YOUR_SERVER_IP>')}")

    print()
    print(cyan("  SPF Record (TXT on root domain):"))
    print(f"    {bold(domain)}  →  TXT  →  {bold(spf_record)}")

    print()
    if "_dkim_dns" in params:
        print(cyan("  DKIM Record (TXT):"))
        print(f"    {bold(params['_dkim_dns'])}")
    else:
        print(cyan("  DKIM Record (TXT on):"))
        print(f"    {bold(f'{selector}._domainkey.{domain}')}  →  TXT  →  (see /etc/opendkim/keys/{domain}/{selector}.txt)")

    print()
    print(cyan("  DMARC Record (TXT):"))
    print(f"    {bold('_dmarc.' + domain)}  →  TXT  →  {bold(dmarc_record)}")

    print()
    record(step_name, True)
    return True


# ─── Final summary ───────────────────────────────────────────────────────────

def print_final_summary():
    print()
    print(cyan("  ╔══════════════════════════════════════════════════════════════╗"))
    print(cyan("  ║                  FINAL SETUP SUMMARY                        ║"))
    print(cyan("  ╚══════════════════════════════════════════════════════════════╝"))
    print()
    all_passed = True
    for title, passed, note in step_results:
        if passed:
            status = green("✔ PASS")
        else:
            all_passed = False
            status = red("✘ FAIL")
        line = f"  {status}  {title}"
        if note:
            line += f"  ({yellow(note)})"
        print(line)

    print()
    if all_passed:
        print(green("  ══════════════════════════════════════════════════════════════"))
        print(green("  ✔  All steps completed successfully!"))
        print(green("  ══════════════════════════════════════════════════════════════"))
        print()
        print(yellow("  Next steps:"))
        print(yellow("  1. Add the DNS records shown above to your DNS zone."))
        print(yellow("  2. Wait for DNS propagation (TTL / up to 24 h)."))
        print(yellow("  3. Send a test email: echo 'Test' | mail -s 'Relay test' you@example.com"))
        print(yellow("  4. Check mail logs: tail -f /var/log/mail.log"))
    else:
        print(yellow("  ══════════════════════════════════════════════════════════════"))
        print(yellow("  ⚠  Some steps failed — please review errors above."))
        print(yellow("  ══════════════════════════════════════════════════════════════"))
        print()
        print(yellow("  Review the failed items and rerun this script, or fix manually."))
    print()


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print_banner()

    # Root check (warn early, still let user see prompts)
    if os.geteuid() != 0:
        print_warn("WARNING: Not running as root. Most steps will fail.")
        print_warn("         Re-run with: sudo python3 setup.py")
        print()

    # Collect all parameters first
    params = collect_parameters()

    # Show summary and ask for confirmation
    show_summary(params)
    if not ask_yes_no(
        "Proceed with the setup using these settings?", default="yes"
    ):
        print_info("Setup cancelled by user.")
        sys.exit(0)

    print()
    print(cyan(f"  Starting setup — {TOTAL_STEPS} steps"))

    # ── Step 1 ────────────────────────────────────────────────────────────────
    print_step(1, TOTAL_STEPS, "System Check")
    if not step_system_check(params):
        confirm_continue("System Check")

    # ── Step 2 ────────────────────────────────────────────────────────────────
    print_step(2, TOTAL_STEPS, "Install Packages")
    if not step_install_packages(params):
        confirm_continue("Install Packages")

    # ── Step 3 ────────────────────────────────────────────────────────────────
    print_step(3, TOTAL_STEPS, "Configure /etc/mailname")
    if not step_configure_mailname(params):
        confirm_continue("Configure /etc/mailname")

    # ── Step 4 ────────────────────────────────────────────────────────────────
    print_step(4, TOTAL_STEPS, "Write /etc/postfix/main.cf")
    if not step_write_main_cf(params):
        confirm_continue("Write /etc/postfix/main.cf")

    # ── Step 5 ────────────────────────────────────────────────────────────────
    print_step(5, TOTAL_STEPS, "Configure SASL Credentials")
    if not step_configure_sasl(params):
        confirm_continue("Configure SASL Credentials")

    # ── Step 6 ────────────────────────────────────────────────────────────────
    print_step(6, TOTAL_STEPS, "Configure OpenDKIM")
    if not step_configure_opendkim(params):
        confirm_continue("Configure OpenDKIM")

    # ── Step 7 ────────────────────────────────────────────────────────────────
    print_step(7, TOTAL_STEPS, "Configure UFW Firewall")
    if not step_configure_ufw(params):
        confirm_continue("Configure UFW Firewall")

    # ── Step 8 ────────────────────────────────────────────────────────────────
    print_step(8, TOTAL_STEPS, "Restart Services")
    if not step_restart_services(params):
        confirm_continue("Restart Services")

    # ── Step 9 ────────────────────────────────────────────────────────────────
    print_step(9, TOTAL_STEPS, "Display DNS Records")
    step_show_dns_records(params)

    # ── Final summary ─────────────────────────────────────────────────────────
    print_final_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warn("Setup interrupted by user (Ctrl+C).")
        print_final_summary()
        sys.exit(130)
