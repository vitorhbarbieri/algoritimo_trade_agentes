# 🚀 Como Iniciar o Servidor e Testar

## ⚠️ Problema Identificado e Resolvido

O erro que você viu (`ImportError: attempted relative import`) foi **corrigido**! 

Agora use `run_api.py` em vez de `api_server.py` diretamente.

## 📋 Passo a Passo

### 1. Iniciar o Servidor API

**Opção A: Script Batch (Windows)**
```bash
start_api.bat
```

**Opção B: Manualmente**
```bash
python run_api.py
```

Você verá:
```
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.15.22:5000
```

**⚠️ IMPORTANTE:** Deixe essa janela aberta! O servidor precisa estar rodando.

### 2. Testar a API (em OUTRO terminal)

**Teste Simples:**
```bash
python test_api_simple.py
```

**Teste Completo:**
```bash
python test_api.py
```

**Ou teste manualmente:**
```bash
# No navegador, acesse:
http://localhost:5000/health

# Ou no PowerShell:
Invoke-WebRequest http://localhost:5000/health
```

### 3. Iniciar Dashboard (Opcional)

Em outro terminal:
```bash
streamlit run dashboard.py
```

Acesse: http://localhost:8501

## 🔧 Solução do Problema

O problema era que `api_server.py` tentava importar módulos com imports relativos (`from .pricing import ...`), mas quando executado diretamente, Python não reconhecia o pacote `src`.

**Solução:** Criamos `run_api.py` que configura o PYTHONPATH corretamente antes de importar.

## ✅ Verificação Rápida

1. ✅ Servidor rodando? → Veja mensagem "Running on http://127.0.0.1:5000"
2. ✅ Teste simples? → `python test_api_simple.py`
3. ✅ Teste completo? → `python test_api.py`

## 🎯 Endpoints para Testar

### No Navegador:
- http://localhost:5000/ → Informações da API
- http://localhost:5000/health → Status
- http://localhost:5000/strategies/list → Listar estratégias

### Via Python:
```python
import requests

# Health check
r = requests.get('http://localhost:5000/health')
print(r.json())

# Executar backtest
r = requests.post('http://localhost:5000/backtest/run', json={
    'tickers': ['AAPL'],
    'use_real_data': True
})
print(r.json())
```

## 🐛 Se Ainda Não Funcionar

1. **Verifique se o servidor está rodando:**
   - Você deve ver "Running on http://127.0.0.1:5000"
   - Se não ver, execute `python run_api.py` novamente

2. **Verifique a porta:**
   - Outro programa pode estar usando a porta 5000
   - Altere em `run_api.py`: `port=5001`

3. **Verifique dependências:**
   ```bash
   pip install flask flask-cors requests
   ```

4. **Veja os logs:**
   - O servidor mostra erros no terminal onde está rodando

## 📝 Próximos Passos

1. ✅ Inicie o servidor: `python run_api.py`
2. ✅ Teste: `python test_api_simple.py`
3. ✅ Execute backtest via API
4. ✅ Veja resultados no dashboard

