@echo off
chcp 65001 >nul
title Casamento Paulo e Gabie

echo.
echo  ============================================
echo    Casamento Paulo ^& Gabie — Servidor Web
echo  ============================================
echo.

:: Verifica se o Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python não encontrado. Instale em https://python.org
    pause
    exit /b 1
)

:: Instala as dependências
echo  [1/2] Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo  [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo  [2/2] Iniciando servidor...
echo.
echo  ============================================
echo    Acesse no navegador:
echo    http://localhost:8000
echo    http://localhost:8000/presentes
echo  ============================================
echo.
echo  Pressione CTRL+C para encerrar o servidor.
echo.

uvicorn app.main:app --reload

pause
