@echo off
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [1/3] Membuat virtual environment...
    py -m venv venv
    if errorlevel 1 goto :error

    echo [2/3] Memperbarui pip...
    "venv\Scripts\python.exe" -m pip install --upgrade pip

    echo [3/3] Memasang dependensi...
    "venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

echo.
echo Menjalankan Somnipathy Lab di http://127.0.0.1:5000
echo Tekan CTRL+C untuk menghentikan server.
echo.
"venv\Scripts\python.exe" app.py
goto :eof

:error
echo.
echo Gagal menyiapkan lingkungan.
echo Pastikan Python 3.11/3.12 sudah terpasang dan perintah "py" tersedia.
pause
