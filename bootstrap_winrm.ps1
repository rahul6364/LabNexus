param([string]$Controller = "192.168.1.117")

$pw = Read-Host "Ansible password" -AsSecureString

if (Get-LocalUser AnsibleAdmin -ErrorAction SilentlyContinue) {
    Set-LocalUser AnsibleAdmin -Password $pw
} else {
    New-LocalUser AnsibleAdmin -Password $pw -PasswordNeverExpires | Out-Null
}

Add-LocalGroupMember -Group Administrators -Member AnsibleAdmin -ErrorAction SilentlyContinue

Enable-PSRemoting -Force -SkipNetworkProfileCheck | Out-Null

Enable-NetFirewallRule -Name "WINRM-HTTP-In-TCP"

Set-NetFirewallRule -Name "WINRM-HTTP-In-TCP" -RemoteAddress $Controller

Write-Host "Ready: WinRM running, restricted to $Controller"