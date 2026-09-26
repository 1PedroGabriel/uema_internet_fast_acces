[CmdletBinding()]
param(
    [switch]$Setup,
    [switch]$Monitor,
    [switch]$Install,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Net.Http

$script:CredentialDirectory = Join-Path $env:APPDATA 'UemaWifiAutoLogin'
$script:UsernamePath = Join-Path $script:CredentialDirectory 'username.txt'
$script:PasswordPath = Join-Path $script:CredentialDirectory 'password.dpapi'
$script:TaskName = 'UEMA Wi-Fi Auto Login'
$script:PortalHost = '172.25.50.10'
$script:PortalPath = '/auth/index.html/u'
$script:ProbeUrl = 'http://www.msftconnecttest.com/connecttest.txt'

function Write-Status {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

function Save-Credentials {
    New-Item -ItemType Directory -Path $script:CredentialDirectory -Force | Out-Null

    $username = Read-Host 'Login do SIGUEMA'
    if ([string]::IsNullOrWhiteSpace($username)) {
        throw 'O login não pode ficar vazio.'
    }

    $password = Read-Host 'Senha do SIGUEMA' -AsSecureString
    if ($password.Length -eq 0) {
        throw 'A senha não pode ficar vazia.'
    }

    [System.IO.File]::WriteAllText($script:UsernamePath, $username, [System.Text.Encoding]::UTF8)
    $encryptedPassword = ConvertFrom-SecureString -SecureString $password
    [System.IO.File]::WriteAllText($script:PasswordPath, $encryptedPassword, [System.Text.Encoding]::ASCII)

    Write-Status 'Credenciais salvas para este usuário do Windows.'
}

function Get-UemaSsid {
    $output = (& netsh.exe wlan show interfaces 2>$null | Out-String)
    $ssidMatches = [regex]::Matches($output, '(?im)^\s*SSID\s*:\s*(.*?)\s*$')

    foreach ($match in $ssidMatches) {
        if ($match.Groups[1].Value.Trim() -eq 'UEMA') {
            return 'UEMA'
        }
    }

    return $null
}

function New-UemaHttpClient {
    $handler = [System.Net.Http.HttpClientHandler]::new()
    $handler.AllowAutoRedirect = $false
    $handler.UseCookies = $true
    $client = [System.Net.Http.HttpClient]::new($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(12)
    $client.DefaultRequestHeaders.UserAgent.ParseAdd('UemaWifiAutoLogin/1.0')
    return $client
}

function Get-PortalResponse {
    param(
        [System.Net.Http.HttpClient]$Client,
        [uri]$Uri
    )

    $currentUri = $Uri
    for ($redirect = 0; $redirect -le 5; $redirect++) {
        $request = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::Get, $currentUri)
        try {
            $response = $Client.SendAsync($request).GetAwaiter().GetResult()
            try {
                $statusCode = [int]$response.StatusCode
                $location = $response.Headers.Location
                if ($statusCode -ge 300 -and $statusCode -lt 400 -and $null -ne $location) {
                    $currentUri = [uri]::new($currentUri, $location)
                    continue
                }

                $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
                return [pscustomobject]@{
                    Uri = $currentUri
                    StatusCode = $statusCode
                    Body = $body
                }
            }
            finally {
                $response.Dispose()
            }
        }
        finally {
            $request.Dispose()
        }
    }

    throw 'O portal redirecionou muitas vezes.'
}

function Test-UemaInternet {
    param([System.Net.Http.HttpClient]$Client)

    try {
        $result = Get-PortalResponse -Client $Client -Uri ([uri]$script:ProbeUrl)
        return ($result.StatusCode -eq 200 -and $result.Body.Trim() -eq 'Microsoft Connect Test')
    }
    catch {
        return $false
    }
}

function Invoke-UemaLogin {
    if (-not (Test-Path -LiteralPath $script:UsernamePath) -or -not (Test-Path -LiteralPath $script:PasswordPath)) {
        throw 'Credenciais ausentes. Execute o script com -Setup primeiro.'
    }

    $username = [System.IO.File]::ReadAllText($script:UsernamePath).Trim()
    $encryptedPassword = [System.IO.File]::ReadAllText($script:PasswordPath).Trim()
    $securePassword = ConvertTo-SecureString -String $encryptedPassword
    $passwordPointer = [IntPtr]::Zero
    $client = New-UemaHttpClient

    try {
        $page = Get-PortalResponse -Client $client -Uri ([uri]$script:ProbeUrl)
        if ($page.StatusCode -eq 200 -and $page.Body.Trim() -eq 'Microsoft Connect Test') {
            return $true
        }

        $formMatch = [regex]::Match($page.Body, '(?is)<form\b[^>]*\baction\s*=\s*["'']([^"'']+)["'']')
        if (-not $formMatch.Success) {
            Write-Status 'Sem internet, mas o formulário do portal não foi encontrado.'
            return $false
        }

        $action = [System.Net.WebUtility]::HtmlDecode($formMatch.Groups[1].Value)
        $target = [uri]::new($page.Uri, $action)
        if ($target.Scheme -ne 'http' -or $target.Host -ne $script:PortalHost -or $target.AbsolutePath -ne $script:PortalPath) {
            Write-Status 'O destino do formulário não corresponde ao portal UEMA esperado; login cancelado.'
            return $false
        }

        $passwordPointer = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
        $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
        $formValues = [System.Collections.Generic.Dictionary[string, string]]::new()
        $formValues.Add('user', $username)
        $formValues.Add('password', $plainPassword)
        $content = [System.Net.Http.FormUrlEncodedContent]::new($formValues)
        $request = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::Post, $target)
        $request.Content = $content
        $request.Headers.Referrer = $page.Uri

        try {
            $response = $client.SendAsync($request).GetAwaiter().GetResult()
            $response.Dispose()
        }
        finally {
            $request.Dispose()
            $content.Dispose()
            $formValues.Clear()
            $plainPassword = $null
        }

        Start-Sleep -Seconds 2
        return (Test-UemaInternet -Client $client)
    }
    finally {
        if ($passwordPointer -ne [IntPtr]::Zero) {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
        }
        $client.Dispose()
    }
}

function Start-Monitor {
    if (-not (Test-Path -LiteralPath $script:UsernamePath) -or -not (Test-Path -LiteralPath $script:PasswordPath)) {
        throw 'Credenciais ausentes. Execute o script com -Setup primeiro.'
    }

    $lastAttempt = [DateTime]::MinValue
    $lastState = ''
    Write-Status 'Monitor iniciado. Verificando a rede UEMA a cada 20 segundos.'

    while ($true) {
        if ((Get-UemaSsid) -ne 'UEMA') {
            $lastAttempt = [DateTime]::MinValue
            if ($lastState -ne 'fora') {
                Write-Status 'Aguardando conexão ao Wi-Fi UEMA.'
                $lastState = 'fora'
            }
            Start-Sleep -Seconds 20
            continue
        }

        $client = New-UemaHttpClient
        try {
            if (Test-UemaInternet -Client $client) {
                if ($lastState -ne 'online') {
                    Write-Status 'Wi-Fi UEMA conectado e internet disponível.'
                    $lastState = 'online'
                }
                $lastAttempt = [DateTime]::MinValue
            }
            elseif (((Get-Date) - $lastAttempt).TotalMinutes -ge 5) {
                Write-Status 'Wi-Fi UEMA detectado sem internet; tentando autenticar.'
                $lastAttempt = Get-Date
                $authenticated = Invoke-UemaLogin
                if ($authenticated) {
                    Write-Status 'Autenticação concluída; internet disponível.'
                    $lastState = 'online'
                }
                else {
                    Write-Status 'Não foi possível confirmar a autenticação. Nova tentativa em 5 minutos.'
                    $lastState = 'falha'
                }
            }
        }
        catch {
            Write-Status 'Falha ao verificar ou autenticar. Nova tentativa em 5 minutos.'
            $lastAttempt = Get-Date
            $lastState = 'falha'
        }
        finally {
            $client.Dispose()
        }

        Start-Sleep -Seconds 20
    }
}

if ($Setup) {
    Save-Credentials
    exit 0
}

if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $script:TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Status 'Inicialização automática removida.'
    exit 0
}

if ($Install) {
    if (-not (Test-Path -LiteralPath $script:UsernamePath) -or -not (Test-Path -LiteralPath $script:PasswordPath)) {
        throw 'Execute primeiro o script com -Setup para cadastrar as credenciais.'
    }
    if ([string]::IsNullOrWhiteSpace($PSCommandPath)) {
        throw 'Salve este script em um arquivo antes de instalar a inicialização automática.'
    }

    $powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Monitor"
    $action = New-ScheduledTaskAction -Execute $powershell -Argument $arguments
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $script:TaskName -Action $action -Trigger $trigger -Principal $principal -Description 'Verifica o Wi-Fi UEMA e autentica no portal cativo.' -Force | Out-Null
    Start-ScheduledTask -TaskName $script:TaskName
    Write-Status 'Monitor instalado para iniciar ao entrar no Windows.'
    exit 0
}

if ($Monitor) {
    Start-Monitor
    exit 0
}

Write-Host @'
Uso:
  .\UemaWifiAutoLogin.ps1 -Setup      Cadastra login e senha (senha protegida pelo Windows).
  .\UemaWifiAutoLogin.ps1 -Install    Inicia o monitor ao entrar no Windows.
  .\UemaWifiAutoLogin.ps1 -Monitor    Executa o monitor nesta janela.
  .\UemaWifiAutoLogin.ps1 -Uninstall  Remove a inicialização automática.
'@