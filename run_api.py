"""
Wrapper para executar api_server.py com PYTHONPATH correto.
"""

import sys
import os
from pathlib import Path

# Adicionar diretório atual e src ao PYTHONPATH
project_root = Path(__file__).parent
src_path = project_root / 'src'

# Adicionar ao path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Configurar variável de ambiente
os.environ['PYTHONPATH'] = f"{project_root}{os.pathsep}{src_path}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"

# Agora importar e executar api_server
if __name__ == '__main__':
    # Importar api_server como módulo
    import api_server
    
    # Executar o servidor
    api_server.app.run(host='0.0.0.0', port=5000, debug=True)

