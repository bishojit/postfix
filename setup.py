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
import json
from datetime import datetime, timezone

# â”€â”€â”€ ANSI Colour Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


def print_success(msg): print(green(f"  âœ”  {msg}"))
def print_warn(msg):    print(yellow(f"  âš   {msg}"))
def print_error(msg):   print(red(f"  âœ˜  {msg}"))
def print_info(msg):    print(yellow(f"  â„¹  {msg}"))
def print_step(n, total, title):
    print()
    print(cyan(f"{'â”€' * 60}"))
    print(cyan(f"  Step {n} of {total} â€” {title}"))
    print(cyan(f"{'â”€' * 60}"))


# â”€â”€â”€ Banner â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

BANNER = r"""
  â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—  â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•— â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•—â–ˆâ–ˆâ•—  â–ˆâ–ˆâ•—
  â–ˆâ–ˆâ•”â•â•â–ˆâ–ˆâ•—â–ˆâ–ˆâ•”â•â•â•â–ˆâ–ˆâ•—â–ˆâ–ˆâ•”â•â•â•â•â•â•šâ•â•â–ˆâ–ˆâ•”â•â•â•â–ˆâ–ˆâ•”â•â•â•â•â•â–ˆâ–ˆâ•‘â•šâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•”â•
  â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•”â•â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—   â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—  â–ˆâ–ˆâ•‘ â•šâ–ˆâ–ˆâ–ˆâ•”â•
  â–ˆâ–ˆâ•”â•â•â•â• â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â•šâ•â•â•â•â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•”â•â•â•  â–ˆâ–ˆâ•‘ â–ˆâ–ˆâ•”â–ˆâ–ˆâ•—
  â–ˆâ–ˆâ•‘     â•šâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•”â•â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•”â• â–ˆâ–ˆâ•—
  â•šâ•â•      â•šâ•â•â•â•â•â• â•šâ•â•â•â•â•â•â•   â•šâ•â•   â•šâ•â•     â•šâ•â•â•šâ•â•  â•šâ•â•

        SMTP Relay Server â€” Production Setup v1.0
"""


def print_banner():
    print(cyan(BANNER))
    print(cyan("  Automated Postfix relay configuration for Ubuntu/Debian"))
    print(cyan("  Uses only Python 3 standard library â€” no external dependencies"))
    print()


# â”€â”€â”€ Step tracking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

TOTAL_STEPS = 10
step_results = []   # list of (title, passed: bool, note: str)


def record(title, passed, note=""):
    step_results.append((title, passed, note))


# â”€â”€â”€ Configuration Persistence â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

CONFIG_PATH_ROOT = "/etc/postfix/relay_setup_config.json"
CONFIG_PATH_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "relay_setup_config.json")

CONFIG_FIELDS = [
    "relay_hostname", "sending_domain", "trusted_ips_raw", "smtp_host",
    "smtp_port", "smtp_user", "dkim_selector", "enable_dkim", "enable_ufw",
    "rate_limit", "admin_email", "smtp_spf_include",
]


def get_config_path():
    """Return the config path â€” /etc/postfix location for root, local otherwise."""
    if os.geteuid() == 0:
        return CONFIG_PATH_ROOT
    return CONFIG_PATH_LOCAL


def load_config():
    """Load saved configuration from JSON, return dict (empty if missing)."""
    for path in (get_config_path(), CONFIG_PATH_LOCAL, CONFIG_PATH_ROOT):
        try:
            with open(path, "r") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                print_success(f"Loaded previous config from {path}")
                return data
        except (OSError, json.JSONDecodeError, ValueError):
            continue
    return {}


def save_config(params):
    """Save configuration to JSON (excludes SMTP password)."""
    path = get_config_path()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {"version": 1, "updated": now}
    for key in CONFIG_FIELDS:
        if key in params:
            data[key] = params[key]
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
        os.chmod(path, 0o640)
        print_success(f"Configuration saved to {path}")
    except OSError as exc:
        print_warn(f"Could not save config: {exc}")


# â”€â”€â”€ Utilities â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


def ask(prompt_text, default="", secret=False, validator=None, optional=False):
    """
    Prompt the user for input.
    - Shows [default] hint when a default exists.
    - Hides input for secret fields.
    - Retries on failed validation.
    - optional=True allows blank answers (returns "").
    """
    hint = f" [{default}]" if default else (" [optional]" if optional else "")
    full_prompt = yellow(f"  â†’ {prompt_text}{hint}: ")
    while True:
        if secret:
            value = getpass.getpass(full_prompt)
        else:
            value = input(full_prompt).strip()
        if not value:
            value = default
        if validator and value:
            error = validator(value)
            if error:
                print_error(error)
                continue
        if not value and not optional:
            print_error("This field is required.")
            continue
        return value


def ask_yes_no(prompt_text, default="yes"):
    """Ask a yes/no question, return True for yes."""
    hint = "[Y/n]" if default.lower() == "yes" else "[y/N]"
    full_prompt = yellow(f"  â†’ {prompt_text} {hint}: ")
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


# â”€â”€â”€ Validators â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€â”€ Parameter collection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def collect_parameters():
    # Load previous config for auto-fill defaults
    saved = load_config()
    if saved:
        print_info("Previous configuration loaded â€” press Enter to keep saved values.\n")

    print(cyan("\n  â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—"))
    print(cyan("  â•‘         CONFIGURATION PARAMETERS                    â•‘"))
    print(cyan("  â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"))
    print(yellow("  Please answer the following questions.\n"
                 "  Press Enter to accept the [default] value where shown.\n"))

    params = {}

    # Relay hostname
    print(yellow("  [/13] Relay Hostname"))
    print(yellow("         Fully qualified domain name for this relay server\n"
                 "         (must match your DNS A record)."))
    params["relay_hostname"] = ask(
        "Relay hostname",
        default=saved.get("relay_hostname", "relay.yourdomain.com"),
        validator=validate_hostname,
    )

    # Sending domain
    print()
    print(yellow("  [/13] Sending Domain"))
    print(yellow("         Your primary email sending domain (e.g. yourdomain.com)."))
    params["sending_domain"] = ask(
        "Sending domain",
        default=saved.get("sending_domain", ""),
        validator=validate_domain,
    )

    # Trusted IPs
    print()
    print(yellow("  [/13] Trusted App Server IPs"))
    print(yellow("         Comma-separated list of app server IPs allowed to relay\n"
                 "         through this server (e.g. 51.79.226.156).\n"
                 "         127.0.0.0/8 is always included automatically."))
    raw_ips = ask(
        "Trusted IPs (comma-separated)",
        default=saved.get("trusted_ips_raw", "127.0.0.0/8"),
    )
    params["trusted_ips_raw"] = raw_ips
    params["mynetworks"] = normalize_ip_list(raw_ips)

    # SMTP host
    print()
    print(yellow("  [/13] Upstream SMTP Host"))
    print(yellow("         The upstream SMTP relay host your server will forward\n"
                 "         all outbound mail through."))
    params["smtp_host"] = ask(
        "Upstream SMTP host",
        default=saved.get("smtp_host", "smtp.n8nclouds.com"),
        validator=validate_hostname,
    )

    # SMTP port
    print()
    print(yellow("  [/13] Upstream SMTP Port"))
    print(yellow("         Upstream SMTP port â€” usually 587 for STARTTLS."))
    params["smtp_port"] = ask(
        "Upstream SMTP port",
        default=saved.get("smtp_port", "587"),
        validator=validate_port,
    )

    # SMTP user
    print()
    print(yellow("  [/13] SMTP Username"))
    print(yellow("         Username for authenticating to the upstream SMTP server."))
    params["smtp_user"] = ask(
        "SMTP username",
        default=saved.get("smtp_user", ""),
    )

    # SMTP password
    print()
    print(yellow("  [/13] SMTP Password"))
    print(yellow("         Password for the upstream SMTP account.\n"
                 "         Input will be hidden. (Never saved to config file)"))
    smtp_pass = ask("SMTP password", secret=True)

    # DKIM selector
    print()
    print(yellow("  [/13] DKIM Selector"))
    print(yellow("         DKIM key selector name.\n"
                 "         Will appear as <selector>._domainkey in DNS."))
    params["dkim_selector"] = ask(
        "DKIM selector",
        default=saved.get("dkim_selector", "relay"),
    )

    # Enable DKIM
    print()
    print(yellow("  [/13] Enable DKIM"))
    print(yellow("         Install and configure OpenDKIM for outbound email signing.\n"
                 "         Strongly recommended for deliverability."))
    dkim_default = "yes" if saved.get("enable_dkim", True) else "no"
    params["enable_dkim"] = ask_yes_no(
        "Enable DKIM signing?", default=dkim_default
    )

    # Enable UFW
    print()
    print(yellow("  [/13] Enable UFW Firewall Rules"))
    print(yellow("          Add UFW rules to restrict port 25 to trusted IPs only.\n"
                 "          Recommended to prevent open-relay abuse."))
    ufw_default = "yes" if saved.get("enable_ufw", True) else "no"
    params["enable_ufw"] = ask_yes_no(
        "Enable UFW firewall rules?", default=ufw_default
    )

    # Rate limit
    print()
    print(yellow("  [/13] Rate Limit"))
    print(yellow("          Maximum messages per client connection\n"
                 "          (smtpd_client_message_rate_limit)."))
    params["rate_limit"] = ask(
        "Rate limit (msgs/client)",
        default=saved.get("rate_limit", "100"),
        validator=validate_rate,
    )

    # Admin email
    print()
    print(yellow("  [12/13] Admin Email"))
    print(yellow("          Admin email address used as the 'rua' tag in the\n"
                 "          generated DMARC DNS record for receiving reports."))
    params["admin_email"] = ask(
        "Admin email",
        default=saved.get("admin_email", ""),
        validator=validate_email,
    )

    # Upstream SMTP SPF include
    print()
    print(yellow("  [13/13] Upstream SMTP Provider SPF Mechanism (optional)"))
    print(yellow("          SPF mechanism for your upstream SMTP provider\n"
                 "          so SPF passes when THEY deliver mail on your behalf.\n"
                 "          The upstream IP appears in Gmail headers, not your relay IP.\n"
                 "          Examples:\n"
                 "            include:n8nclouds.com\n"
                 "            ip4:51.79.177.39\n"
                 "          Leave blank to skip (you can add it to DNS manually)."))
    params["smtp_spf_include"] = ask(
        "Upstream SMTP SPF mechanism",
        default=saved.get("smtp_spf_include", ""),
        optional=True,
    )

    return params, smtp_pass


# â”€â”€â”€ Summary & confirmation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def show_summary(params):
    print()
    print(cyan("  â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—"))
    print(cyan("  â•‘              CONFIGURATION SUMMARY                  â•‘"))
    print(cyan("  â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"))
    rows = [
        ("Relay hostname",        params["relay_hostname"]),
        ("Sending domain",        params["sending_domain"]),
        ("Trusted IPs",           params["mynetworks"]),
        ("Upstream SMTP host",    params["smtp_host"]),
        ("Upstream SMTP port",    params["smtp_port"]),
        ("SMTP username",         params["smtp_user"]),
        ("SMTP password",         "â—â—â—â—â—â—â—â—"),
        ("DKIM selector",         params["dkim_selector"]),
        ("Enable DKIM",           "yes" if params["enable_dkim"] else "no"),
        ("Enable UFW",            "yes" if params["enable_ufw"] else "no"),
        ("Rate limit",            params["rate_limit"]),
        ("Admin email",           params["admin_email"]),
        ("Upstream SPF mechanism", params.get("smtp_spf_include") or "(none)"),
    ]
    for label, value in rows:
        print(f"  {cyan(label + ':'):<38}  {bold(value)}")
    print()


# â”€â”€â”€ main.cf template â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

MAIN_CF_TEMPLATE = """\
# â”€â”€â”€ Generated by setup.py on {timestamp} â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# â”€â”€â”€ Identity â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
myhostname = {relay_hostname}
myorigin = /etc/mailname
mydomain = {sending_domain}

# â”€â”€â”€ Network â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
inet_interfaces = all
inet_protocols = ipv4
mynetworks = {mynetworks}

# â”€â”€â”€ Relay â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
relayhost = [{smtp_host}]:{smtp_port}

# â”€â”€â”€ Outbound SASL Auth â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous

# â”€â”€â”€ Outbound TLS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
smtp_use_tls = yes
smtp_tls_security_level = encrypt
smtp_tls_note_starttls_offer = yes
smtp_tls_loglevel = 1
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
smtp_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_ciphers = high

# â”€â”€â”€ Inbound Relay Restrictions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
smtpd_recipient_restrictions =
    permit_mynetworks,
    reject_unauth_destination

# â”€â”€â”€ Anti-spam / Hardening â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

# â”€â”€â”€ Rate Limiting â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
smtpd_client_message_rate_limit = {rate_limit}
smtpd_client_connection_count_limit = 20
smtpd_client_connection_rate_limit = 30
anvil_rate_time_unit = 60s

# â”€â”€â”€ Queue / Delivery â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
maximal_queue_lifetime = 1d
bounce_queue_lifetime = 6h
maximal_backoff_time = 1h
minimal_backoff_time = 5m

# â”€â”€â”€ Message Size â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
message_size_limit = 10240000

# â”€â”€â”€ Sender Address Rewriting â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Rewrites the envelope sender and From: header for locally-submitted mail
# (e.g. mail/sendmail commands) so it appears as the sending domain, not
# the raw system user@short-hostname (e.g. root@vmi2558887).
sender_canonical_maps = static:noreply@{sending_domain}
sender_canonical_classes = envelope_sender, header_sender

# â”€â”€â”€ Misc â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
append_dot_mydomain = no
readme_directory = no
compatibility_level = 3.6
{milter_section}
"""

MILTER_SECTION_ENABLED = """\
# â”€â”€â”€ OpenDKIM Milter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
milter_default_action = accept
milter_protocol = 6
smtpd_milters = local:opendkim/opendkim.sock
non_smtpd_milters = local:opendkim/opendkim.sock
"""

MILTER_SECTION_DISABLED = """\
# â”€â”€â”€ OpenDKIM Milter (disabled) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# milter_default_action = accept
# milter_protocol = 6
# smtpd_milters = local:opendkim/opendkim.sock
# non_smtpd_milters = local:opendkim/opendkim.sock
"""


# â”€â”€â”€ OpenDKIM config templates â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€â”€ Step functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def step_system_check(params):
    """Step 1 â€” System Check"""
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
        msg = f"OS '{distro_id}' is not Ubuntu/Debian â€” setup may fail"
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
    """Step 2 â€” Install Packages"""
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
        print_info("Running apt update â€¦")
        run("apt-get update -qq", env_extra=env)
        print_success("apt update complete")

        # Package list
        packages = ["postfix", "mailutils", "libsasl2-modules"]
        if params["enable_dkim"]:
            packages += ["opendkim", "opendkim-tools"]

        pkg_str = " ".join(packages)
        print_info(f"Installing: {pkg_str} â€¦")
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
    """Step 3 â€” Configure /etc/mailname"""
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
    """Step 4 â€” Write /etc/postfix/main.cf"""
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


def step_configure_sasl(params, smtp_pass):
    """Step 5 â€” Configure SASL credentials"""
    step_name = "Configure SASL Credentials"
    try:
        print_warn("SMTP password will be stored in plaintext in /etc/postfix/sasl_passwd")
        print_warn("Access is restricted to root (mode 0600). Keep this file secure.")
        # Build credentials string and write it; clear from local variable afterwards
        sasl_passwd = (
            f"[{params['smtp_host']}]:{params['smtp_port']} "
            f"{params['smtp_user']}:{smtp_pass}\n"
        )
        # noqa: S106 â€” intentional plaintext credential storage required by Postfix SASL
        write_file("/etc/postfix/sasl_passwd", sasl_passwd, mode=0o600)
        sasl_passwd = None  # clear sensitive data from local scope
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
    """Step 6 â€” Configure OpenDKIM"""
    step_name = "Configure OpenDKIM"
    if not params["enable_dkim"]:
        print_info("DKIM disabled â€” skipping")
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
            print_warn(f"DKIM private key already exists: {private_key} â€” skipping generation")
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
            print(cyan("  â”Œâ”€â”€â”€ DKIM DNS Record (add to your DNS zone) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"))
            for line in dkim_dns.strip().splitlines():
                print(cyan(f"  â”‚  {line}"))
            print(cyan("  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"))
            # Store for final summary
            params["_dkim_dns"] = dkim_dns.strip()

        record(step_name, True)
        return True
    except (OSError, RuntimeError) as exc:
        print_error(str(exc))
        record(step_name, False, str(exc))
        return False


def step_configure_ufw(params):
    """Step 7 â€” Configure UFW Firewall"""
    step_name = "Configure UFW"
    if not params["enable_ufw"]:
        print_info("UFW rules disabled â€” skipping")
        record(step_name, True, "skipped (disabled)")
        return True
    try:
        if not shutil.which("ufw"):
            print_warn("ufw not installed â€” installing â€¦")
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
    """Step 8 â€” Restart Services"""
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


# â”€â”€â”€ DNS Resolution Helpers (stdlib only â€” uses dig/nslookup) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def dns_resolve_txt(name):
    """Resolve TXT records for a domain name. Returns list of strings."""
    records = []
    for tool in ("dig", "nslookup"):
        if not shutil.which(tool):
            continue
        try:
            if tool == "dig":
                result = subprocess.run(
                    ["dig", "+short", "TXT", name],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().splitlines():
                        # dig returns quoted strings â€” strip quotes and join parts
                        records.append(line.replace('"', '').strip())
                    return records
            else:
                result = subprocess.run(
                    ["nslookup", "-type=TXT", name],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if "text =" in line.lower():
                            txt = line.split("=", 1)[1].strip().strip('"')
                            records.append(txt)
                    return records
        except (subprocess.TimeoutExpired, OSError):
            continue
    return records


def dns_resolve_a(hostname):
    """Resolve A record for a hostname. Returns list of IPs."""
    try:
        result = subprocess.run(
            ["dig", "+short", "A", hostname],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return [ip.strip() for ip in result.stdout.strip().splitlines() if ip.strip()]
    except (subprocess.TimeoutExpired, OSError):
        pass
    # Fallback to socket
    try:
        return [socket.gethostbyname(hostname)]
    except socket.gaierror:
        return []


def step_verify_dns(params):
    """Step 10 â€” Verify DNS Records & Enforce DKIM/DMARC"""
    step_name = "Verify DNS Records"
    domain = params["sending_domain"]
    relay_hostname = params["relay_hostname"]
    selector = params["dkim_selector"]
    admin_email = params["admin_email"]
    mynetworks = params["mynetworks"]
    local_ip = get_local_ip()
    warnings = []
    errors = []

    print()
    print(cyan("  Checking live DNS records â€¦"))
    print()

    # â”€â”€ A Record â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    a_records = dns_resolve_a(relay_hostname)
    if a_records:
        if local_ip in a_records:
            print_success(f"A record: {relay_hostname} â†’ {', '.join(a_records)} (matches server IP)")
        else:
            msg = (f"A record: {relay_hostname} â†’ {', '.join(a_records)} "
                   f"(does NOT match local IP {local_ip})")
            print_warn(msg)
            warnings.append(msg)
    else:
        msg = f"A record: {relay_hostname} â†’ NOT FOUND"
        print_error(msg)
        print_info(f"  Add:  {relay_hostname}  â†’  A  â†’  {local_ip}")
        errors.append(msg)

    # â”€â”€ SPF Record â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ip_includes = ""
    for net in mynetworks.split():
        if net == "127.0.0.0/8":
            continue
        if net.endswith("/32"):
            ip_includes += f" ip4:{net[:-3]}"
        else:
            ip_includes += f" ip4:{net}"
    spf_upstream = ""
    if params.get("smtp_spf_include"):
        spf_upstream = f" {params['smtp_spf_include']}"
    expected_spf = f"v=spf1{ip_includes}{spf_upstream} a:{relay_hostname} ~all"

    spf_records = dns_resolve_txt(domain)
    spf_found = [r for r in spf_records if r.startswith("v=spf1")]
    if spf_found:
        print_success(f"SPF record found: {spf_found[0]}")
        # Check if relay IP is included
        if relay_hostname in spf_found[0] or local_ip in spf_found[0]:
            print_success("  SPF includes relay server")
        else:
            msg = "SPF record does not include relay server IP/hostname"
            print_warn(msg)
            print_info(f"  Recommended:  {domain}  â†’  TXT  â†’  {expected_spf}")
            warnings.append(msg)
    else:
        msg = f"SPF record: NOT FOUND on {domain}"
        print_error(msg)
        print_info(f"  Add:  {domain}  â†’  TXT  â†’  {expected_spf}")
        errors.append(msg)

    # â”€â”€ DKIM Record â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    dkim_name = f"{selector}._domainkey.{domain}"
    dkim_records = dns_resolve_txt(dkim_name)
    dkim_found = [r for r in dkim_records if "p=" in r]
    if dkim_found:
        print_success(f"DKIM record found: {dkim_name}")
        if "p=" in dkim_found[0] and len(dkim_found[0]) > 20:
            print_success("  DKIM public key present")
        else:
            msg = "DKIM record exists but public key may be empty/invalid"
            print_warn(msg)
            warnings.append(msg)
    else:
        msg = f"DKIM record: NOT FOUND on {dkim_name}"
        print_error(msg)
        if params["enable_dkim"]:
            key_path = f"/etc/opendkim/keys/{domain}/{selector}.txt"
            print_info(f"  Add TXT record from: {key_path}")
            if "_dkim_dns" in params:
                print_info(f"  Value: {params['_dkim_dns']}")
        else:
            print_info("  DKIM is disabled â€” enable it for better deliverability")
        errors.append(msg)

    # â”€â”€ DMARC Record â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    dmarc_name = f"_dmarc.{domain}"
    expected_dmarc = f"v=DMARC1; p=quarantine; rua=mailto:{admin_email}; ruf=mailto:{admin_email}; fo=1"
    dmarc_records = dns_resolve_txt(dmarc_name)
    dmarc_found = [r for r in dmarc_records if r.startswith("v=DMARC1")]
    if dmarc_found:
        print_success(f"DMARC record found: {dmarc_found[0]}")
        # Enforce policy strength
        if "p=none" in dmarc_found[0]:
            msg = "DMARC policy is 'none' â€” upgrade to 'quarantine' or 'reject' for enforcement"
            print_warn(msg)
            print_info(f"  Recommended:  {dmarc_name}  â†’  TXT  â†’  {expected_dmarc}")
            warnings.append(msg)
        elif "p=quarantine" in dmarc_found[0]:
            print_success("  DMARC policy: quarantine (good)")
        elif "p=reject" in dmarc_found[0]:
            print_success("  DMARC policy: reject (strict)")
        # Check rua tag
        if "rua=" not in dmarc_found[0]:
            msg = "DMARC record missing 'rua' reporting tag"
            print_warn(msg)
            warnings.append(msg)
    else:
        msg = f"DMARC record: NOT FOUND on {dmarc_name}"
        print_error(msg)
        print_info(f"  Add:  {dmarc_name}  â†’  TXT  â†’  {expected_dmarc}")
        errors.append(msg)

    # â”€â”€ Summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print()
    if errors:
        print_error(f"DNS verification: {len(errors)} record(s) missing â€” add them before sending mail")
    elif warnings:
        print_warn(f"DNS verification: {len(warnings)} warning(s) â€” review recommendations above")
    else:
        print_success("All DNS records verified successfully!")

    passed = len(errors) == 0
    note = f"{len(errors)} missing, {len(warnings)} warnings" if (errors or warnings) else ""
    record(step_name, passed, note)
    return passed


def step_show_dns_records(params):
    """Step 9 â€” Display DNS records"""
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
    spf_upstream = ""
    if params.get("smtp_spf_include"):
        spf_upstream = f" {params['smtp_spf_include']}"

    spf_record = f"v=spf1{ip_includes}{spf_upstream} a:{relay_hostname} ~all"
    dmarc_record = f"v=DMARC1; p=quarantine; rua=mailto:{admin_email}; ruf=mailto:{admin_email}; fo=1"

    print()
    print(cyan("  â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—"))
    print(cyan("  â•‘             DNS RECORDS TO ADD                              â•‘"))
    print(cyan("  â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"))

    print()
    print(cyan("  A Record (relay server):"))
    print(f"    {bold(relay_hostname)}  â†’  A  â†’  {bold('<YOUR_SERVER_IP>')}")

    print()
    print(cyan("  SPF Record (TXT on root domain):"))
    print(f"    {bold(domain)}  â†’  TXT  â†’  {bold(spf_record)}")

    print()
    if "_dkim_dns" in params:
        print(cyan("  DKIM Record (TXT):"))
        print(f"    {bold(params['_dkim_dns'])}")
    else:
        print(cyan("  DKIM Record (TXT on):"))
        print(f"    {bold(f'{selector}._domainkey.{domain}')}  â†’  TXT  â†’  (see /etc/opendkim/keys/{domain}/{selector}.txt)")

    print()
    print(cyan("  DMARC Record (TXT):"))
    print(f"    {bold('_dmarc.' + domain)}  â†’  TXT  â†’  {bold(dmarc_record)}")

    print()
    record(step_name, True)
    return True


# â”€â”€â”€ Final summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def print_final_summary():
    print()
    print(cyan("  â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—"))
    print(cyan("  â•‘                  FINAL SETUP SUMMARY                        â•‘"))
    print(cyan("  â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"))
    print()
    all_passed = True
    for title, passed, note in step_results:
        if passed:
            status = green("âœ” PASS")
        else:
            all_passed = False
            status = red("âœ˜ FAIL")
        line = f"  {status}  {title}"
        if note:
            line += f"  ({yellow(note)})"
        print(line)

    print()
    if all_passed:
        print(green("  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"))
        print(green("  âœ”  All steps completed successfully!"))
        print(green("  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"))
        print()
        print(yellow("  Next steps:"))
        print(yellow("  1. Add the DNS records shown above to your DNS zone."))
        print(yellow("  2. Wait for DNS propagation (TTL / up to 24 h)."))
        print(yellow("  3. Send a test email: echo 'Test' | mail -s 'Relay test' you@example.com"))
        print(yellow("  4. Check mail logs: tail -f /var/log/mail.log"))
    else:
        print(yellow("  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"))
        print(yellow("  âš   Some steps failed â€” please review errors above."))
        print(yellow("  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"))
        print()
        print(yellow("  Review the failed items and rerun this script, or fix manually."))
    print()


# â”€â”€â”€ Main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main():
    print_banner()

    # Root check (warn early, still let user see prompts)
    if os.geteuid() != 0:
        print_warn("WARNING: Not running as root. Most steps will fail.")
        print_warn("         Re-run with: sudo python3 setup.py")
        print()

    # Collect all parameters first
    params, smtp_pass = collect_parameters()

    # Show summary and ask for confirmation
    show_summary(params)
    if not ask_yes_no(
        "Proceed with the setup using these settings?", default="yes"
    ):
        smtp_pass = None  # clear before exit
        print_info("Setup cancelled by user.")
        sys.exit(0)

    print()
    print(cyan(f"  Starting setup â€” {TOTAL_STEPS} steps"))

    # â”€â”€ Step 1 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_step(1, TOTAL_STEPS, "System Check")
    if not step_system_check(params):
        confirm_continue("System Check")

    # â”€â”€ Step 2 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_step(2, TOTAL_STEPS, "Install Packages")
    if not step_install_packages(params):
        confirm_continue("Install Packages")

    # â”€â”€ Step 3 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_step(3, TOTAL_STEPS, "Configure /etc/mailname")
    if not step_configure_mailname(params):
        confirm_continue("Configure /etc/mailname")

    # â”€â”€ Step 4 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_step(4, TOTAL_STEPS, "Write /etc/postfix/main.cf")
    if not step_write_main_cf(params):
        confirm_continue("Write /etc/postfix/main.cf")

    # â”€â”€ Step 5 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_step(5, TOTAL_STEPS, "Configure SASL Credentials")
    if not step_configure_sasl(params, smtp_pass):
        confirm_continue("Configure SASL Credentials")
    smtp_pass = None  # clear after SASL step regardless of outcome

    # â”€â”€ Step 6 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_step(6, TOTAL_STEPS, "Configure OpenDKIM")
    if not step_configure_opendkim(params):
        confirm_continue("Configure OpenDKIM")

    # â”€â”€ Step 7 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_step(7, TOTAL_STEPS, "Configure UFW Firewall")
    if not step_configure_ufw(params):
        confirm_continue("Configure UFW Firewall")

    # â”€â”€ Step 8 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_step(8, TOTAL_STEPS, "Restart Services")
    if not step_restart_services(params):
        confirm_continue("Restart Services")

    # â”€â”€ Step 9 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_step(9, TOTAL_STEPS, "Display DNS Records")
    step_show_dns_records(params)

    # â”€â”€ Step 10 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_step(10, TOTAL_STEPS, "Verify DNS Records & Enforce DKIM/DMARC")
    if not step_verify_dns(params):
        confirm_continue("Verify DNS Records")

    # â”€â”€ Save configuration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    save_config(params)

    # â”€â”€ Final summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print_final_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warn("Setup interrupted by user (Ctrl+C).")
        print_final_summary()
        sys.exit(130)
