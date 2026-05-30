$ErrorActionPreference = "Stop"

$processNames = @("Lernbrief-Hub", "python", "pythonw")
$stopped = @()

foreach ($name in $processNames) {
    $procs = Get-Process -Name $name -ErrorAction SilentlyContinue
    foreach ($p in $procs) {
        try {
            # Stop only likely app hosts; for python/pythonw, check command line when available.
            if ($name -in @("python", "pythonw")) {
                $cmd = ""
                try {
                    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)").CommandLine
                } catch {
                    $cmd = ""
                }
                if ($cmd -notmatch "lernbrief|Lernbrief-Hub|app.py") {
                    continue
                }
            }

            Stop-Process -Id $p.Id -Force
            $stopped += "$($p.ProcessName) (PID $($p.Id))"
        } catch {
            Write-Host "Konnte Prozess nicht beenden: $($p.ProcessName) (PID $($p.Id))" -ForegroundColor Yellow
        }
    }
}

if ($stopped.Count -eq 0) {
    Write-Host "Kein laufender Lernbrief-Hub-Prozess gefunden." -ForegroundColor Cyan
} else {
    Write-Host "Beendet:" -ForegroundColor Green
    $stopped | ForEach-Object { Write-Host "- $_" }
}
