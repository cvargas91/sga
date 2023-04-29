# load file content
$content = Get-Content config/.env -ErrorAction Stop

# load vars to environment
foreach ($line in $content) {
    if ($line.StartsWith("#")) { continue };

    if ($line.Trim()) {
        $kvp = $line -split "=",2
        [Environment]::SetEnvironmentVariable($kvp[0], $kvp[1], "Process") | Out-Null
    }
}
