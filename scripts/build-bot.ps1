Set-PSDebug -Trace 1
$DebugPreference = "Continue"
$Full = 1
$ExtraOpts = ""
If ($Full) {
    python -m pip install --upgrade pip setuptools wheel
    pip install -r requirements/bot.txt
    rm -recurse build
    rm -recurse dist
    $ExtraOpts = "--clean"
}
PyInstaller.exe $ExtraOpts -y ./inst/bot.spec
