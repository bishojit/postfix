#!/usr/bin/env python3
"""
Postfix SMTP Relay Server — Debug & Diagnostics Tool
Checks system health, service status, DNS records, configuration,
mail queue, and recent log activity. Outputs a color-coded report.
"""

import os
import sys
import json
import socket
import platform
import shutil
import subprocess
import re
from datetime import datetime, timezone
from pathlib import Path

# ─── ANSI Colour Helpers ─────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
DIM    = "\033[2m"


def red(msg):    return f"{RED}{msg}{RESET}"
def green(msg):  return f"{GREEN}{msg}{RESET}"
def yellow(msg): return f"{YELLOW}{msg}{RESET}"
def cyan(msg):   return f"{CYAN}{msg}{RESET}"
def bold(msg):   return f"{BOLD}{msg}{RESET}"
def dim(msg):    return f"{DIM}{msg}{RESET}"


def print_pass(msg):  print(green(f"  ✔  {msg}"))
def print_warn(msg):  print(yellow(f"  ⚠  {msg}"))
def print_fail(msg):  print(red(f"  ✘  {msg}"))
def print_info(msg):  print(yellow(f"  ℹ  {msg}"))

BANNER = r"""
  ██████╗ ███████╗██████╗ ██╗   ██╗ ██████╗
  ██╔══██╗██╔════╝██╔══██╗██║   ██║██╔════╝
  ██║  ██║█████╗  ██████╔╝██║   ██║██║  ███╗
  ██║  ██║██╔══╝  ██╔══██╗██║   ██║██║   ██║
  ██████╔╝███████╗██████╔╝╚██████╔╝╚██████╔╝
  ╚═════╝ ╚══════╝╚═════╝  ╚═════╝  ╚═════╝

        Postfix Relay — Diagnostics & Debug v1.0
"""

# ─── Config paths ────────────────────────────────────────────────────────────

CONFIG_PATH_ROOT = "/etc/postfix/relay_setup_config.json"
CONFIG_PATH_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "relay_setup_config.json")

# ─── Result tracking ────────────────────────────────────────────────────────

checks_passed = 0
checks_warned = 0
checks_failed = 0
check_results = []  # list of dicts for JSON export


def track(section, name, status, detail=""):
    """Track a check result. status: 'pass', 'warn', 'fail'."""
    global checks_passed, checks_warned, checks_failed
    if status == "pass":
        checks_passed += 1
        print_pass(f"{name}: {detail}" if detail else name)
    elif status == "warn":
        checks_warned += 1
        print_warn(f"{name}: {detail}" if detail else name)
    else:
        checks_failed += 1
        print_fail(f"{name}: {detail}" if detail else name)
    check_results.append({
        "section": section,
        "name": name,
        "status": status,
        "detail": detail,
    })


def section_header(title):
    print()
    print(cyan(f"{'━' * 60}"))
    print(cyan(f"  {title}"))
    print(cyan(f"{'━' * 60}"))


# ─── Helpers ─────────────────────────────────────────────────────────────────

def run_cmd(cmd, timeout=10):
    """Run a command, return (success, stdout). Never raises."""
    try:
        result = subprocess.run(
            cmd, shell=isinstance(cmd, str),
            capture_output=True, text=True, timeout=timeout,
        )
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return False, ""


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def dns_resolve_txt(name):
    """Resolve TXT records using dig or nslookup."""
    records = []
    for tool in ("dig", "nslookup"):
        if not shutil.which(tool):
            continue
        try:
            if tool == "dig":
                ok, out = run_cmd(["dig", "+short", "TXT", name])
                if ok and out:
                    for line in out.splitlines():
                        records.append(line.replace('"', '').strip())
                    return records
            else:
                ok, out = run_cmd(["nslookup", "-type=TXT", name])
                if ok and out:
                    for line in out.splitlines():
                        if "text =" in line.lower():
                            txt = line.split("=", 1)[1].strip().strip('"')
                            records.append(txt)
                    return records
        except Exception:
            continue
    return records


def dns_resolve_a(hostname):
    """Resolve A record."""
    try:
        ok, out = run_cmd(["dig", "+short", "A", hostname])
        if ok and out:
            return [ip.strip() for ip in out.splitlines() if ip.strip()]
    except Exception:
        pass
    try:
        return [socket.gethostbyname(hostname)]
    except socket.gaierror:
        return []


def load_config():
    """Load saved relay config JSON."""
    for path in (CONFIG_PATH_ROOT, CONFIG_PATH_LOCAL):
        try:
            with open(path, "r") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return data, path
        except (OSError, json.JSONDecodeError):
            continue
    return {}, None


def file_mode(path):
    """Return octal file mode string like '0600'."""
    try:
        mode = os.stat(path).st_mode & 0o7777
        return f"{mode:04o}"
    except OSError:
        return "????"


# ─── Section 1: System Info ─────────────────────────────────────────────────

def check_system_info():
    section_header("SYSTEM INFORMATION")
    sec = "System"

    # OS
    os_info = platform.platform()
    print_info(f"Platform: {os_info}")

    # Hostname
    hostname = socket.gethostname()
    print_info(f"Hostname: {hostname}")

    # IP
    local_ip = get_local_ip()
    print_info(f"Local IP: {local_ip}")

    # Python version
    py_ver = platform.python_version()
    print_info(f"Python:   {py_ver}")

    # Uptime
    ok, out = run_cmd("uptime -p")
    if ok and out:
        print_info(f"Uptime:   {out}")

    # Root check
    if os.geteuid() == 0:
        track(sec, "Root access", "pass")
    else:
        track(sec, "Root access", "warn", "Not running as root — some checks may be limited")

    return local_ip


# ─── Section 2: Service Status ──────────────────────────────────────────────

def check_services():
    section_header("SERVICE STATUS")
    sec = "Services"

    for svc in ("postfix", "opendkim"):
        ok, out = run_cmd(f"systemctl is-active {svc}")
        if ok and out == "active":
            track(sec, f"{svc} service", "pass", "active")
        else:
            # Check if installed at all
            ok2, _ = run_cmd(f"systemctl list-unit-files {svc}.service")
            if svc == "opendkim" and not ok2:
                track(sec, f"{svc} service", "warn", "not installed")
            else:
                track(sec, f"{svc} service", "fail", out or "not running")

    # Port 25 listening
    ok, out = run_cmd("ss -tlnp sport = :25")
    if ok and "LISTEN" in out:
        track(sec, "Port 25 listening", "pass")
    else:
        track(sec, "Port 25 listening", "fail", "nothing listening on port 25")


# ─── Section 3: Configuration Audit ─────────────────────────────────────────

def check_configuration(config):
    section_header("CONFIGURATION AUDIT")
    sec = "Config"

    # main.cf
    main_cf = "/etc/postfix/main.cf"
    if os.path.exists(main_cf):
        track(sec, main_cf, "pass", "exists")
        try:
            with open(main_cf) as f:
                content = f.read()
            # Check key directives
            for directive in ("myhostname", "relayhost", "smtp_sasl_auth_enable",
                              "smtpd_recipient_restrictions", "smtp_tls_security_level"):
                if directive in content:
                    track(sec, f"  {directive}", "pass", "configured")
                else:
                    track(sec, f"  {directive}", "warn", "not found in main.cf")
        except OSError:
            track(sec, f"  Read {main_cf}", "fail", "permission denied")
    else:
        track(sec, main_cf, "fail", "not found")

    # mailname
    mailname_path = "/etc/mailname"
    if os.path.exists(mailname_path):
        try:
            with open(mailname_path) as f:
                mailname = f.read().strip()
            expected = config.get("relay_hostname", "")
            if expected and mailname == expected:
                track(sec, "/etc/mailname", "pass", f"'{mailname}' matches config")
            elif expected:
                track(sec, "/etc/mailname", "warn",
                      f"'{mailname}' differs from config '{expected}'")
            else:
                track(sec, "/etc/mailname", "pass", f"set to '{mailname}'")
        except OSError:
            track(sec, "/etc/mailname", "fail", "cannot read")
    else:
        track(sec, "/etc/mailname", "fail", "not found")

    # SASL credentials
    sasl = "/etc/postfix/sasl_passwd"
    sasl_db = "/etc/postfix/sasl_passwd.db"
    if os.path.exists(sasl):
        mode = file_mode(sasl)
        if mode == "0600":
            track(sec, "sasl_passwd", "pass", f"exists, mode {mode}")
        else:
            track(sec, "sasl_passwd", "warn", f"exists but mode is {mode} (expected 0600)")
    else:
        track(sec, "sasl_passwd", "fail", "not found")

    if os.path.exists(sasl_db):
        track(sec, "sasl_passwd.db", "pass", "exists")
    else:
        track(sec, "sasl_passwd.db", "fail", "not found — run 'postmap /etc/postfix/sasl_passwd'")

    # OpenDKIM config
    dkim_conf = "/etc/opendkim.conf"
    if os.path.exists(dkim_conf):
        track(sec, "opendkim.conf", "pass", "exists")
    else:
        track(sec, "opendkim.conf", "warn", "not found (DKIM may be disabled)")

    # DKIM keys
    domain = config.get("sending_domain", "")
    selector = config.get("dkim_selector", "relay")
    if domain:
        key_dir = f"/etc/opendkim/keys/{domain}"
        priv_key = f"{key_dir}/{selector}.private"
        pub_key = f"{key_dir}/{selector}.txt"
        if os.path.exists(priv_key):
            mode = file_mode(priv_key)
            if mode == "0600":
                track(sec, f"DKIM private key", "pass", f"exists, mode {mode}")
            else:
                track(sec, f"DKIM private key", "warn", f"mode {mode} (expected 0600)")
        else:
            track(sec, f"DKIM private key", "warn",
                  f"not found at {priv_key}")
        if os.path.exists(pub_key):
            track(sec, f"DKIM public key", "pass", "exists")
        else:
            track(sec, f"DKIM public key", "warn", f"not found at {pub_key}")

    # Milter socket directory
    sock_dir = "/var/spool/postfix/opendkim"
    if os.path.exists(sock_dir):
        track(sec, "OpenDKIM socket dir", "pass", "exists")
    else:
        track(sec, "OpenDKIM socket dir", "warn", "not found")


# ─── Section 4: DNS Verification ────────────────────────────────────────────

def check_dns(config, local_ip):
    section_header("DNS VERIFICATION")
    sec = "DNS"

    domain = config.get("sending_domain", "")
    relay_hostname = config.get("relay_hostname", "")
    selector = config.get("dkim_selector", "relay")
    admin_email = config.get("admin_email", "")

    if not domain or not relay_hostname:
        track(sec, "DNS check", "warn", "no saved config — cannot verify DNS records")
        return

    # A record
    a_records = dns_resolve_a(relay_hostname)
    if a_records:
        if local_ip != "unknown" and local_ip in a_records:
            track(sec, f"A record ({relay_hostname})", "pass",
                  f"→ {', '.join(a_records)} (matches server)")
        else:
            track(sec, f"A record ({relay_hostname})", "warn",
                  f"→ {', '.join(a_records)} (does not match local IP {local_ip})")
    else:
        track(sec, f"A record ({relay_hostname})", "fail", "NOT FOUND")

    # SPF
    spf_records = dns_resolve_txt(domain)
    spf_found = [r for r in spf_records if r.startswith("v=spf1")]
    if spf_found:
        track(sec, f"SPF ({domain})", "pass", spf_found[0][:80])
    else:
        track(sec, f"SPF ({domain})", "fail", "NOT FOUND")

    # DKIM
    dkim_name = f"{selector}._domainkey.{domain}"
    dkim_records = dns_resolve_txt(dkim_name)
    dkim_found = [r for r in dkim_records if "p=" in r]
    if dkim_found:
        track(sec, f"DKIM ({dkim_name})", "pass", "public key present")
    else:
        track(sec, f"DKIM ({dkim_name})", "fail", "NOT FOUND")

    # DMARC
    dmarc_name = f"_dmarc.{domain}"
    dmarc_records = dns_resolve_txt(dmarc_name)
    dmarc_found = [r for r in dmarc_records if r.startswith("v=DMARC1")]
    if dmarc_found:
        policy = "unknown"
        if "p=reject" in dmarc_found[0]:
            policy = "reject"
        elif "p=quarantine" in dmarc_found[0]:
            policy = "quarantine"
        elif "p=none" in dmarc_found[0]:
            policy = "none"
        if policy == "none":
            track(sec, f"DMARC ({dmarc_name})", "warn",
                  f"policy={policy} — should be quarantine or reject")
        else:
            track(sec, f"DMARC ({dmarc_name})", "pass", f"policy={policy}")
    else:
        track(sec, f"DMARC ({dmarc_name})", "fail", "NOT FOUND")


# ─── Section 5: Mail Queue Stats ────────────────────────────────────────────

def check_mail_queue():
    section_header("MAIL QUEUE")
    sec = "Queue"

    ok, out = run_cmd("postqueue -p")
    if not ok:
        track(sec, "Mail queue", "warn", "cannot read queue (postfix not running?)")
        return

    if "Mail queue is empty" in out:
        track(sec, "Mail queue", "pass", "empty")
        return

    # Count messages
    lines = out.strip().splitlines()
    msg_count = 0
    deferred = 0
    active = 0
    for line in lines:
        if line and line[0] != '-' and not line.startswith("postqueue"):
            # Queue IDs are 10+ hex chars at start of line
            if re.match(r'^[0-9A-F]{8,}', line):
                msg_count += 1
                if line.rstrip().endswith('*'):
                    active += 1
                elif line.rstrip().endswith('!'):
                    deferred += 1

    # Last line often has summary "-- X Kbytes in Y Requests."
    summary_match = re.search(r'(\d+)\s+Requests?', out)
    if summary_match:
        msg_count = int(summary_match.group(1))

    if msg_count == 0:
        track(sec, "Mail queue", "pass", "empty")
    elif msg_count < 10:
        track(sec, "Mail queue", "pass", f"{msg_count} message(s)")
    elif msg_count < 100:
        track(sec, "Mail queue", "warn", f"{msg_count} message(s) — queue building up")
    else:
        track(sec, "Mail queue", "fail", f"{msg_count} message(s) — queue backlog!")

    print_info(f"  Total: {msg_count}  |  Active: {active}  |  Deferred: {deferred}")


# ─── Section 6: Recent Log Analysis ─────────────────────────────────────────

def check_logs():
    section_header("RECENT LOG ANALYSIS (last 200 lines)")
    sec = "Logs"

    log_path = "/var/log/mail.log"
    if not os.path.exists(log_path):
        track(sec, "Mail log", "warn", f"{log_path} not found")
        return

    ok, out = run_cmd(f"tail -200 {log_path}")
    if not ok or not out:
        track(sec, "Mail log", "warn", "cannot read log (permission denied?)")
        return

    lines = out.splitlines()
    counters = {
        "sent":     0,
        "bounced":  0,
        "deferred": 0,
        "rejected": 0,
        "error":    0,
    }

    for line in lines:
        lower = line.lower()
        if "status=sent" in lower:
            counters["sent"] += 1
        elif "status=bounced" in lower:
            counters["bounced"] += 1
        elif "status=deferred" in lower:
            counters["deferred"] += 1
        elif "reject" in lower:
            counters["rejected"] += 1
        elif "error" in lower or "fatal" in lower:
            counters["error"] += 1

    total_issues = counters["bounced"] + counters["deferred"] + counters["rejected"] + counters["error"]
    summary = (f"Sent: {counters['sent']}  |  Bounced: {counters['bounced']}  |  "
               f"Deferred: {counters['deferred']}  |  Rejected: {counters['rejected']}  |  "
               f"Errors: {counters['error']}")

    if total_issues == 0 and counters["sent"] > 0:
        track(sec, "Log analysis", "pass", summary)
    elif total_issues == 0 and counters["sent"] == 0:
        track(sec, "Log analysis", "warn", f"No recent activity — {summary}")
    elif total_issues < 5:
        track(sec, "Log analysis", "warn", summary)
    else:
        track(sec, "Log analysis", "fail", summary)

    # Show last 5 error/reject lines for quick debugging
    error_lines = [l for l in lines if any(kw in l.lower()
                   for kw in ("reject", "error", "fatal", "status=bounced"))]
    if error_lines:
        print()
        print(cyan("  Recent errors/rejects:"))
        for line in error_lines[-5:]:
            # Truncate long lines
            display = line.strip()[:120]
            print(red(f"    {display}"))


# ─── Section 7: Saved Config Check ──────────────────────────────────────────

def check_saved_config():
    section_header("SAVED CONFIGURATION")
    sec = "SavedConfig"

    config, path = load_config()
    if not config:
        track(sec, "Config file", "warn",
              "No saved config found — run setup.py first")
        return {}

    track(sec, f"Config file", "pass", f"loaded from {path}")

    required_fields = [
        "relay_hostname", "sending_domain", "smtp_host", "smtp_port",
        "smtp_user", "dkim_selector", "admin_email",
    ]
    missing = [f for f in required_fields if not config.get(f)]
    if missing:
        track(sec, "Config completeness", "warn",
              f"missing fields: {', '.join(missing)}")
    else:
        track(sec, "Config completeness", "pass", "all required fields present")

    # Display key values
    safe_keys = [
        ("relay_hostname",  "Relay hostname"),
        ("sending_domain",  "Sending domain"),
        ("smtp_host",       "SMTP host"),
        ("smtp_port",       "SMTP port"),
        ("smtp_user",       "SMTP user"),
        ("dkim_selector",   "DKIM selector"),
        ("enable_dkim",     "DKIM enabled"),
        ("enable_ufw",      "UFW enabled"),
        ("rate_limit",      "Rate limit"),
        ("admin_email",     "Admin email"),
        ("updated",         "Last updated"),
    ]
    print()
    for key, label in safe_keys:
        val = config.get(key, dim("(not set)"))
        if isinstance(val, bool):
            val = green("yes") if val else red("no")
        print(f"    {cyan(label + ':'):<40}  {bold(str(val))}")

    return config


# ─── Overall Score ───────────────────────────────────────────────────────────

def print_score():
    total = checks_passed + checks_warned + checks_failed
    print()
    print(cyan("  ╔══════════════════════════════════════════════════════════════╗"))
    print(cyan("  ║                  DIAGNOSTIC SUMMARY                         ║"))
    print(cyan("  ╚══════════════════════════════════════════════════════════════╝"))
    print()
    print(f"    {green('✔ Passed:')}  {checks_passed}")
    print(f"    {yellow('⚠ Warnings:')} {checks_warned}")
    print(f"    {red('✘ Failed:')}  {checks_failed}")
    print(f"    {'Total checks:':<14} {total}")
    print()

    if checks_failed == 0 and checks_warned == 0:
        print(green("  ══════════════════════════════════════════════════════════════"))
        print(green("  ✔  All checks passed — relay server is healthy!"))
        print(green("  ══════════════════════════════════════════════════════════════"))
    elif checks_failed == 0:
        print(yellow("  ══════════════════════════════════════════════════════════════"))
        print(yellow(f"  ⚠  {checks_warned} warning(s) — review items above"))
        print(yellow("  ══════════════════════════════════════════════════════════════"))
    else:
        print(red("  ══════════════════════════════════════════════════════════════"))
        print(red(f"  ✘  {checks_failed} check(s) failed — action required"))
        print(red("  ══════════════════════════════════════════════════════════════"))
    print()


# ─── Export JSON Report ──────────────────────────────────────────────────────

def export_report():
    """Write structured JSON report to disk."""
    report = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hostname": socket.gethostname(),
        "local_ip": get_local_ip(),
        "summary": {
            "passed": checks_passed,
            "warnings": checks_warned,
            "failed": checks_failed,
            "total": checks_passed + checks_warned + checks_failed,
        },
        "checks": check_results,
    }
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "debug_report.json")
    try:
        with open(report_path, "w") as fh:
            json.dump(report, fh, indent=2)
        print_pass(f"Report saved to {report_path}")
    except OSError as exc:
        print_warn(f"Could not save report: {exc}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print(cyan(BANNER))
    print(cyan(f"  Run at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"))
    print(cyan(f"  Host:   {socket.gethostname()}  ({get_local_ip()})"))

    # Section 7 first — load config for use in other sections
    config = check_saved_config()

    # Section 1
    local_ip = check_system_info()

    # Section 2
    check_services()

    # Section 3
    check_configuration(config)

    # Section 4
    check_dns(config, local_ip)

    # Section 5
    check_mail_queue()

    # Section 6
    check_logs()

    # Score
    print_score()

    # Export
    export_report()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warn("Interrupted.")
        sys.exit(130)
