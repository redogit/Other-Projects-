using namespace System.Security.Cryptography
using namespace System.Security.Cryptography.X509Certificates
param(
    [Parameter(Mandatory)][string]$Carrier,
    [Parameter(Mandatory)][string]$PolicyProbe,
    [Parameter(Mandatory)][string]$Receipt
)
$ErrorActionPreference = 'Stop'
# Test trust provisioning is permitted only on a disposable hosted CI runner.
# The application itself still uses the normal Windows trust store and policy.
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_ENVIRONMENT -ne 'github-hosted') {
    throw 'Certificate fixture provisioning requires a disposable GitHub-hosted runner'
}
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
try {
    $principal = [System.Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Fixture provisioning requires the hosted runner administrator account'
    }
} finally { $identity.Dispose() }
$fixtureDir = Join-Path $env:RUNNER_TEMP ("rmapl-tls-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $fixtureDir | Out-Null
# CurrentUser Root can open an interactive trust dialog. This disposable
# administrator runner uses the standard machine store; no dialog is automated.
$store = [X509Store]::new('Root', [StoreLocation]::LocalMachine)
$added = [System.Collections.Generic.List[X509Certificate2]]::new()
$anchor = [DateTimeOffset]::UtcNow

function New-Fixture([string]$Name, [bool]$Trusted, [bool]$Expired) {
    Write-Host "Creating controlled fixture: $Name"
    $key = [RSA]::Create(2048)
    $cert = $null
    try {
        $request = [CertificateRequest]::new('CN=localhost', $key,
            [HashAlgorithmName]::SHA256, [RSASignaturePadding]::Pkcs1)
        $san = [SubjectAlternativeNameBuilder]::new()
        $san.AddDnsName('localhost')
        $request.CertificateExtensions.Add($san.Build())
        $usage = [System.Security.Cryptography.OidCollection]::new()
        [void]$usage.Add([System.Security.Cryptography.Oid]::new('1.3.6.1.5.5.7.3.1'))
        $request.CertificateExtensions.Add([X509EnhancedKeyUsageExtension]::new($usage, $true))
        # Self-signed endpoint fixtures have no remote AIA/CDP dependencies.
        # Exclude-root revocation remains enabled in the unmodified client.
        $start = $anchor.AddDays(-2)
        $end = $anchor.AddDays(2)
        if ($Expired) { $start = $anchor.AddDays(-4); $end = $anchor.AddDays(-2) }
        $cert = $request.CreateSelfSigned($start, $end)
        [IO.File]::WriteAllText((Join-Path $fixtureDir "$Name.pem"), $cert.ExportCertificatePem())
        [IO.File]::WriteAllText((Join-Path $fixtureDir "$Name.key"), $key.ExportPkcs8PrivateKeyPem())
        [IO.File]::WriteAllBytes((Join-Path $fixtureDir "$Name.cer"), $cert.RawData)
        if ($Trusted) {
            $public = [X509Certificate2]::new($cert.RawData)
            # Track before Add so even a partial failure reaches cleanup.
            $added.Add($public)
            Write-Host "Provisioning fixture in disposable machine store: $Name"
            $store.Add($public)
            Write-Host "Fixture provisioned: $Name"
        }
    } finally {
        if ($cert) { $cert.Dispose() }
        $key.Dispose()
    }
}

try {
    $store.Open([OpenFlags]::ReadWrite)
    New-Fixture 'valid' $true $false
    New-Fixture 'untrusted' $false $false
    New-Fixture 'expired' $true $true
    Write-Host 'Executing explicit policy and loopback checks'
    python (Join-Path $PSScriptRoot 'check_win32_tls_negative.py') --carrier $Carrier --policy-probe $PolicyProbe --fixtures $fixtureDir --receipt $Receipt
    if ($LASTEXITCODE -ne 0) { throw "Controlled TLS checks failed: $LASTEXITCODE" }
} finally {
    try {
        $cleanupErrors = [System.Collections.Generic.List[string]]::new()
        foreach ($cert in $added) {
            try {
                Write-Host "Removing fixture: $($cert.Thumbprint)"
                $store.Remove($cert)
                if ($store.Certificates.Find([X509FindType]::FindByThumbprint, $cert.Thumbprint, $false).Count -ne 0) {
                    throw "Fixture cleanup failed: $($cert.Thumbprint)"
                }
            } catch {
                $cleanupErrors.Add($_.ToString())
            } finally {
                $cert.Dispose()
            }
        }
        if ($cleanupErrors.Count) { throw ($cleanupErrors -join '; ') }
        Write-Host 'All fixture certificates removed'
    } finally {
        $store.Close()
        Remove-Item -Recurse -Force $fixtureDir
    }
}
