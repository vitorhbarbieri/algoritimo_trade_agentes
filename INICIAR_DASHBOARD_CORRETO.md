# ✅ Como Iniciar o Dashboard Corretamente

## ⚠️ Erro Comum

**Erro:** `Error: No such option: -m`

**Causa:** Comando incorreto ou diretório errado

## ✅ Solução

### 1. Navegar para o Diretório Correto

```powershell
cd C:\Projetos\algoritimo_trade_agentes
```

### 2. Comando Correto

**Opção A: Usando streamlit diretamente**
```powershell
streamlit run dashboard_central.py
```

**Opção B: Usando python -m**
```powershell
python -m streamlit run dashboard_central.py
```

**Opção C: Usando o script batch**
```powershell
.\start_dashboard_central.bat
```

## 🔍 Verificar Antes de Iniciar

### 1. Verificar Diretório
```powershell
Get-Location
# Deve mostrar: C:\Projetos\algoritimo_trade_agentes
```

### 2. Verificar se Arquivo Existe
```powershell
Test-Path dashboard_central.py
# Deve retornar: True
```

### 3. Verificar se Streamlit Está Instalado
```powershell
python -c "import streamlit; print('OK')"
# Deve mostrar: OK
```

### 4. Verificar se API Está Rodando
```powershell
python test_api_simple.py
# Deve mostrar: ✅ API está respondendo!
```

## 📋 Passo a Passo Completo

```powershell
# 1. Navegar para o diretório correto
cd C:\Projetos\algoritimo_trade_agentes

# 2. Verificar se está no lugar certo
Get-ChildItem dashboard_central.py

# 3. Iniciar dashboard
streamlit run dashboard_central.py

# Ou usar o script
.\start_dashboard_central.bat
```

## 🚀 Comandos Rápidos

### Terminal 1 - API
```powershell
cd C:\Projetos\algoritimo_trade_agentes
python run_api.py
```

### Terminal 2 - Dashboard
```powershell
cd C:\Projetos\algoritimo_trade_agentes
streamlit run dashboard_central.py
```

## ⚠️ Se Ainda Der Erro

1. **Verifique o PATH do Python:**
   ```powershell
   python --version
   where.exe python
   ```

2. **Instale Streamlit novamente:**
   ```powershell
   pip install streamlit --upgrade
   ```

3. **Use o caminho completo:**
   ```powershell
   C:\Python314\python.exe -m streamlit run dashboard_central.py
   ```

## ✅ Comando Final Correto

```powershell
cd C:\Projetos\algoritimo_trade_agentes
streamlit run dashboard_central.py --server.port 8501
```

O dashboard abrirá em: **http://localhost:8501**

