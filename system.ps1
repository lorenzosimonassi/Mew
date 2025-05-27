if ( -Not (Test-Path "venv")) {
    py -m venv venv
}
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

. .\venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
pip install invoke
pip install -e .