# Installation

## Quick Start

```bash
# 1. Copy the script to your relay server
scp setup.py root@relay.yourdomain.com:/root/

# 2. SSH into the server
ssh root@relay.yourdomain.com

# 3. Run the setup
python3 setup.py
```

## Step-by-Step

### 1. Transfer the Script

Copy `setup.py` to the relay server using any method:

```bash
# Option A: SCP
scp setup.py root@<SERVER_IP>:/root/

# Option B: curl from your repo
curl -O https://raw.githubusercontent.com/your-org/postfix/main/setup.py

# Option C: Paste directly
nano /root/setup.py
# (paste contents, save)
```

### 2. Run as Root

```bash
sudo python3 setup.py
```

The script checks for root privileges at startup. If not running as root, it warns you and most steps will fail.

### 3. Follow the Wizard

The script will:

1. Display a banner and version info
2. Ask 12 configuration questions (with defaults you can accept by pressing Enter)
3. Show a configuration summary
4. Ask for confirmation before proceeding
5. Execute 9 setup steps with pass/fail feedback
6. Display DNS records to publish
7. Print a final summary

### 4. Publish DNS Records

After step 9, the script displays the exact DNS records to add. Step 10 then **verifies** whether those records are already published and flags any that are missing or misconfigured.

See [06-dns-records.md](06-dns-records.md).

### 5. Test

Send a test email and verify delivery. See [07-testing.md](07-testing.md).

You can also run the diagnostics tool for a full health check:

```bash
sudo python3 debug.py
```

## Re-running the Script

The script is **idempotent** for most operations:

- Config files are overwritten with the new values
- DKIM keys are **not regenerated** if they already exist (to avoid breaking published DNS records)
- Packages are only installed if missing
- UFW rules are added (duplicates are harmless)
- **Configuration is saved** to `relay_setup_config.json` — on re-run, all 12 prompts are pre-filled with previous values (press Enter to keep them)
- SMTP password is **never saved** and always re-prompted

You can safely re-run the script to change configuration parameters.
