# Windows PC Setup

This guide walks through configuring target Windows client machines so they can be managed securely by the central Ansible controller.

---

## 1. Get the Approved Bootstrap Script

Obtain the approved [`bootstrap_winrm.ps1`](file:///home/rahul/ansible/cli-prototype/bootstrap_winrm.ps1) script from the project repository.

You can transfer this script to the Windows machine via USB, network share, or download it directly from the approved internal location.

---

## 2. Open PowerShell as Administrator

On the target Windows PC:

1. Click the **Start** menu.
2. Type **PowerShell**.
3. Right-click **Windows PowerShell** (or Terminal) and select **Run as administrator**.

> [!IMPORTANT]
> Administrative privileges are required to create local accounts, configure PowerShell Remoting, and modify Windows Firewall rules.

---

## 3. Run the Bootstrap Script

Navigate to the directory containing `bootstrap_winrm.ps1` and execute it:

```powershell
.\bootstrap_winrm.ps1 -Controller <CONTROLLER_IP>
```

Example (for controller IP `192.168.1.117`):

```powershell
.\bootstrap_winrm.ps1 -Controller 192.168.1.117
```

If PowerShell execution policy blocks running scripts on the machine, run this command to bypass it for the session:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap_winrm.ps1 -Controller <CONTROLLER_IP>
```

---

## 4. Provide the AnsibleAdmin Password

When prompted by the script:

```text
Ansible password:
```

Enter the secure password for the `AnsibleAdmin` account.

> [!NOTE]
> This password must match the `ansible_password` stored in `group_vars/windows/vault.yml` on the Ansible controller.

---

## 5. Automated Configuration (WinRM & Firewall)

The script automatically performs the following security and setup tasks:

- **Local User Creation**: Creates or updates the `AnsibleAdmin` user account with password set to never expire.
- **Administrator Privileges**: Adds `AnsibleAdmin` to the local `Administrators` group.
- **Enable WinRM**: Runs `Enable-PSRemoting` to start and configure the WinRM service.
- **Firewall Restriction**: Enables the `WINRM-HTTP-In-TCP` firewall rule and restricts incoming WinRM access strictly to the controller's IP address (`-RemoteAddress $Controller`).

Once completed, the script prints:

```text
Ready: WinRM running, restricted to <CONTROLLER_IP>
```

---

## 6. Verify Connectivity from the Ansible Controller

Return to the Ubuntu Ansible controller to verify WinRM connectivity.

From the repository root on the controller, test ping to all configured Windows hosts:

```bash
ansible windows -m ansible.windows.win_ping
```

Or test a specific machine (for example, `pc01`):

```bash
ansible pc01 -m ansible.windows.win_ping
```

Expected result:

```json
pc01 | SUCCESS => {
    "ping": "pong"
}
```

The Windows PC is now ready to receive software deployments from the controller.
