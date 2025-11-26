#!/bin/bash

echo "======================================================================"
echo "Iniciando Dashboard Central - Trading Agents"
echo "======================================================================"
echo ""

# Verificar se Streamlit está instalado
python3 -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Instalando Streamlit e dependências..."
    pip install streamlit plotly requests -q
fi

echo ""
echo "Verificando se a API está rodando..."
python3 -c "import requests; r = requests.get('http://localhost:5000/health', timeout=2); print('API OK')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "AVISO: API não está respondendo!"
    echo "Certifique-se de que o servidor está rodando:"
    echo "  python run_api.py"
    echo ""
    read -p "Pressione Enter para continuar mesmo assim..."
fi

echo ""
echo "======================================================================"
echo "Dashboard iniciando em http://localhost:8501"
echo "======================================================================"
echo ""

streamlit run dashboard_central.py --server.port 8501

