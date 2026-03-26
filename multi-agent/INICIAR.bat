@echo off
title Studio PI - Agentes
color 0A
cls

echo.
echo  ========================================
echo    STUDIO PI - Sistema de Multi-Agentes
echo  ========================================
echo.

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado!
    echo.
    echo  Instale o Python em: https://www.python.org/downloads/
    echo  Marque a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b
)

echo  [1/3] Instalando dependencias...
pip install claude-agent-sdk fastapi uvicorn --quiet

echo  [2/3] Iniciando servidor...
start /B python -m uvicorn servidor:app --host 127.0.0.1 --port 7860 --log-level error

echo  [3/3] Aguardando inicializacao...
timeout /t 4 /nobreak >nul

echo.
echo  ========================================
echo    Abrindo no navegador...
echo  ========================================
echo.
echo  Se nao abrir automaticamente, acesse:
echo  http://localhost:7860
echo.
echo  Pressione CTRL+C neste terminal para encerrar.
echo.

start http://localhost:7860
python -m uvicorn servidor:app --host 127.0.0.1 --port 7860 --log-level warning
