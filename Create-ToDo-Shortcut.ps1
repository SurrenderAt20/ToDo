$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcherPath = Join-Path $projectRoot "Start-ToDo.bat"
$pythonwPath = Join-Path $projectRoot ".venv\Scripts\pythonw.exe"
$pythonExePath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$imageDir = Join-Path $projectRoot "image"
$pngIconPath = Join-Path $imageDir "todoimg.png"
$icoIconPath = Join-Path $imageDir "todoimg.ico"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "ToDo.lnk"

if (-not (Test-Path $launcherPath)) {
    throw "Launcher not found: $launcherPath"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $launcherPath
$shortcut.WorkingDirectory = $projectRoot

# Convert PNG → ICO only if the .ico doesn't already exist.
if (-not (Test-Path $icoIconPath)) {
    if ((Test-Path $pngIconPath) -and (Test-Path $pythonExePath)) {
        $convertScript = @"
from PIL import Image

img = Image.open(r'$pngIconPath').convert('RGBA')
img.save(r'$icoIconPath', format='ICO', sizes=[(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)])
"@
        & $pythonExePath -c $convertScript
    }
}

if (Test-Path $icoIconPath) {
    $shortcut.IconLocation = "$icoIconPath,0"
}
elseif (Test-Path $pythonwPath) {
    # Fallback to Python icon if no custom icon exists.
    $shortcut.IconLocation = "$pythonwPath,0"
}

$shortcut.Save()
Write-Host "Created shortcut: $shortcutPath"
