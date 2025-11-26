#!/bin/bash

echo "Iniciando Dashboard do Agente de Trading..."
echo ""
echo "Instalando dependências (se necessário)..."
pip install streamlit plotly -q
echo ""
echo "Iniciando servidor Streamlit..."
echo ""
echo "Acesse: http://localhost:8501"
echo ""
streamlit run dashboard.py

