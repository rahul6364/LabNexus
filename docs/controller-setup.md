# Ansible Controller Setup

This guide prepares the Ubuntu machine that will act as the central Ansible controller.

---

## 1. Requirements

The controller should have:

- **Ubuntu Linux**
- **Python 3** (and `python3-venv`)
- **Network access** to the approved Windows lab PCs
- A **fixed / reserved LAN IP** if possible

> [!IMPORTANT]
> The controller IP must be known and static/reserved because Windows WinRM firewall rules will restrict access specifically to this IP.

---

## 2. Clone the Repository

Clone the project repository to your controller machine:

```bash
git clone <REPOSITORY_URL>
```

Navigate into the cloned directory:

```bash
cd lab-deployment
```

*(If cloned into `cli-prototype`, navigate with `cd cli-prototype`)*

---

## 3. Create Python Virtual Environment

Create an isolated Python virtual environment:

```bash
python3 -m venv .venv
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Upgrade `pip`:

```bash
pip install --upgrade pip
```

---

## 4. Install Required Python Packages

Install Ansible and required dependencies:

```bash
pip install ansible pywinrm pyyaml
```

Verify that Ansible is installed correctly:

```bash
ansible --version
```

---

## 5. Install Ansible Windows Collection

Install the `ansible.windows` collection from Ansible Galaxy:

```bash
ansible-galaxy collection install ansible.windows
```

Verify that the collection is installed:

```bash
ansible-galaxy collection list
```

---

## 6. Configure the Ansible Controller

The repository contains `ansible.cfg` in the project root:

```ini
[defaults]
inventory = inventory.ini
forks = 6
host_key_checking = False
vault_password_file = ~/.vault_pass
```

The configuration defines:
- `inventory.ini` as the default inventory file
- Up to 6 parallel Ansible tasks (`forks = 6`)
- Windows machines as deployment targets
- Automated lookup for the Ansible Vault password file (`~/.vault_pass`)

---

## 7. Generate the Windows Inventory

Generate `inventory.ini` using `gen_inventory.py` by specifying the IP range for approved lab PCs:

```bash
python3 gen_inventory.py <START_IP> <END_IP>
```

Example (for IP range `192.168.1.110` to `192.168.1.115`):

```bash
python3 gen_inventory.py 192.168.1.110 192.168.1.115
```

Inspect the generated inventory file:

```bash
cat inventory.ini
```

Verify that Ansible parses the inventory:

```bash
ansible-inventory --graph
```

> [!IMPORTANT]
> Only System Administrator-approved machines should be included in the inventory.

---

## 8. Configure Ansible Vault

Create the Vault password file:

```bash
echo 'YOUR_VAULT_PASSWORD' > ~/.vault_pass
```

Set file permissions so only your user can read it:

```bash
chmod 600 ~/.vault_pass
```

> [!WARNING]
> The Vault password file (`~/.vault_pass`) must **never** be committed to Git.

Create the `group_vars/windows` directory:

```bash
mkdir -p group_vars/windows
```

Create the encrypted Windows credentials file:

```bash
ansible-vault create group_vars/windows/vault.yml
```

Inside the editor prompt, paste the admin password:

```yaml
ansible_password: "WINDOWS_ANSIBLEADMIN_PASSWORD"
```

Save and exit the editor.

Verify that the file is encrypted:

```bash
head -n 1 group_vars/windows/vault.yml
```

The output should begin with:

```text
$ANSIBLE_VAULT;
```

---

## 9. Test Windows Connectivity

After the target Windows PCs have been configured using `bootstrap_winrm.ps1`, test connectivity from the controller:

```bash
ansible windows -m ansible.windows.win_ping
```

Expected result:

```json
pc01 | SUCCESS => {
    "ping": "pong"
}
```

Repeat and verify for all approved machines.

---

## 10. Add Approved Software

Navigate to the approved software directory:

```bash
cd approved-software
```

Place approved installer files (`.msi`, etc.) inside this directory.

> [!NOTE]
> Do not commit installer files to Git.

Update `catalog.yml` with the approved software metadata:
- **Software name** (`name`)
- **Version** (`version`)
- **Software ID** (`id`)
- **Installer URL** (`url`)
- **SHA-256 checksum** (`sha256`)
- **Verification path** (`verify_path`)

Example `catalog.yml` entry:

```yaml
software_1:
  name: "Git"
  version: "2.44.0"
  id: "software_1"
  url: "http://<CONTROLLER_IP>:8000/Git-2.44.0-64-bit.msi"
  sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  verify_path: 'C:\Program Files\Git\cmd\git.exe'
```

---

## 11. Start the Installer Server

Navigate to the `approved-software` directory from the repository root:

```bash
cd approved-software
```

Start Python's built-in HTTP server bound to your controller IP:

```bash
python3 -m http.server 8000 --bind <CONTROLLER_IP>
```

Example (bound to `192.168.1.117`):

```bash
python3 -m http.server 8000 --bind 192.168.1.117
```

> [!TIP]
> Keep this terminal running during deployment so Windows machines can download installers.

---

## 12. Test Deployment

First, perform a canary deployment to a single approved machine:

```bash
python3 runner.py deploy <SOFTWARE_ID> --hosts pc01
```

Example deploying `software_1` to `pc01`:

```bash
python3 runner.py deploy software_1 --hosts pc01
```

Verify the installation on the target machine.

If successful, deploy to all approved machines in the inventory:

```bash
python3 runner.py deploy <SOFTWARE_ID> --hosts all
```

Example deploying `software_1` to all hosts:

```bash
python3 runner.py deploy software_1 --hosts all
```

To deploy to a specific subset of machines:

```bash
python3 runner.py deploy <SOFTWARE_ID> --hosts pc01,pc02
```

---

## 13. View Deployment History & Catalog

View previous deployment runs:

```bash
python3 runner.py history
```

View the available approved software catalog:

```bash
python3 runner.py catalog
```
