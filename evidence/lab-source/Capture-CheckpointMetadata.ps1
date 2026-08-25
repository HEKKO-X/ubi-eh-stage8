param([string]$Output = 'C:\NetForge-Evidence')

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path $Output -Force | Out-Null
Get-ADUser -SearchBase "OU=NetForge,$((Get-ADDomain).DistinguishedName)" -Filter * -Properties ServicePrincipalName,MemberOf |
  Select-Object SamAccountName,DistinguishedName,ServicePrincipalName,MemberOf |
  ConvertTo-Json -Depth 5 | Set-Content "$Output\variant-users.json"
Get-ADGroup -SearchBase "OU=NetForge,$((Get-ADDomain).DistinguishedName)" -Filter * -Properties Members |
  Select-Object SamAccountName,DistinguishedName,Members |
  ConvertTo-Json -Depth 5 | Set-Content "$Output\variant-groups.json"
Get-SmbShare -Name 'NetForgeArchive$' | ConvertTo-Json -Depth 4 | Set-Content "$Output\share.json"
Get-FileHash C:\NetForge-Variant-Application.json -Algorithm SHA256 | ConvertTo-Json | Set-Content "$Output\application-hash.json"
