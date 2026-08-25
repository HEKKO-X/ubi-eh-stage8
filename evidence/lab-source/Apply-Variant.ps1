param([Parameter(Mandatory=$true)][string]$VariantJson)

$ErrorActionPreference = 'Stop'
Import-Module ActiveDirectory
$variant = Get-Content $VariantJson -Raw | ConvertFrom-Json
$candidatePassword = ConvertTo-SecureString $variant.candidate_password -AsPlainText -Force
$servicePassword = ConvertTo-SecureString $variant.service_password -AsPlainText -Force

New-ADOrganizationalUnit -Name 'NetForge' -Path $variant.domain_dn -ProtectedFromAccidentalDeletion $false -ErrorAction SilentlyContinue
$ou = "OU=NetForge,$($variant.domain_dn)"
New-ADUser -Name $variant.candidate_user -SamAccountName $variant.candidate_user -AccountPassword $candidatePassword -Enabled $true -Path $ou -ErrorAction SilentlyContinue
New-ADUser -Name $variant.service_user -SamAccountName $variant.service_user -AccountPassword $servicePassword -Enabled $true -Path $ou -ServicePrincipalNames "HTTP/archive.$($variant.domain_netbios.ToLower()).local" -ErrorAction SilentlyContinue
New-ADGroup -Name 'Archive Operators' -SamAccountName 'Archive Operators' -GroupScope Global -Path $ou -ErrorAction SilentlyContinue

$serviceDn = (Get-ADUser $variant.service_user).DistinguishedName
& dsacls.exe $serviceDn /G "$($variant.domain_netbios)\$($variant.candidate_user):WP;servicePrincipalName"
if ($LASTEXITCODE -ne 0) { throw 'Failed to apply path-one ACL' }

$shareRoot = 'C:\NetForge-Archive'
New-Item -ItemType Directory -Path $shareRoot -Force | Out-Null
$variant.path_1_flag | Set-Content "$shareRoot\path-one.txt"
$variant.path_2_flag | Set-Content "$shareRoot\path-two.txt"
New-SmbShare -Name 'NetForgeArchive$' -Path $shareRoot -FullAccess 'Domain Admins' -ReadAccess 'Archive Operators',$variant.service_user -ErrorAction SilentlyContinue | Out-Null

$archiveSid = (Get-ADGroup 'Archive Operators').SID
$serviceSid = (Get-ADUser $variant.service_user).SID
$pathOneAcl = Get-Acl "$shareRoot\path-one.txt"
$pathOneAcl.SetAccessRuleProtection($true, $false)
$pathOneAcl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($serviceSid,'Read','Allow')))
$pathOneAcl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule('BUILTIN\Administrators','FullControl','Allow')))
Set-Acl "$shareRoot\path-one.txt" $pathOneAcl
$pathTwoAcl = Get-Acl "$shareRoot\path-two.txt"
$pathTwoAcl.SetAccessRuleProtection($true, $false)
$pathTwoAcl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($archiveSid,'Read','Allow')))
$pathTwoAcl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule('BUILTIN\Administrators','FullControl','Allow')))
Set-Acl "$shareRoot\path-two.txt" $pathTwoAcl

$candidateSid = (Get-ADUser $variant.candidate_user).SID
$groupDn = (Get-ADGroup 'Archive Operators').DistinguishedName
$groupAcl = Get-Acl "AD:\$groupDn"
$genericAll = New-Object System.DirectoryServices.ActiveDirectoryAccessRule($candidateSid,'GenericAll','Allow')
$groupAcl.AddAccessRule($genericAll)
Set-Acl "AD:\$groupDn" $groupAcl

[ordered]@{
  applied_at = (Get-Date).ToUniversalTime().ToString('o')
  candidate = $variant.candidate_user
  service = $variant.service_user
  service_dn = $serviceDn
  group_dn = $groupDn
  ou = $ou
} | ConvertTo-Json | Set-Content C:\NetForge-Variant-Application.json
