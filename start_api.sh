#!/bin/bash

echo "======================================================================"
echo "Iniciando API Server do Sistema de Trading"
echo "======================================================================"
echo ""
echo "Instalando dependências (se necessário)..."
pip install flask flask-cors -q
echo ""
echo "Iniciando servidor Flask..."
echo ""
echo "API disponível em: http://localhost:5000"
echo "Dashboard disponível em: http://localhost:8501"
echo ""
echo "Para testar:"
echo "  curl http://localhost:5000/health"
echo ""
echo "======================================================================"
python run_api.py

