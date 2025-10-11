# Mini-FTP (Custom UDP Transport)

Implements a reliable Go-Back-N transport protocol over UDP and a mini-FTP
application (LIST / GET / PUT) with GUI and metrics.
(Most of these files have placeholder stuff/skeleton.)

## Run
```bash
python -m app.ftp_server
python -m app.ftp_client

git clone https://github.com/Charisma-Ricarte/Override-StudioCN
cd CSCI4406-TP
# Linux / Mac
python3 -m venv venv

# Windows (PowerShell)
python -m venv venv

# Linux / Mac
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (cmd)
venv\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements.txt

The server will listen on UDP port 9000
python -m app.ftp_server
python -m gui.main


Select a file using the Select File button

Use PUT to upload to the server

Use GET to download from the server

python tests/run_tests.py
