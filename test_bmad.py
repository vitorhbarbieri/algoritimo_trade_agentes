"""
Teste para verificar se squad-bmad está disponível e funcionando.
"""

print("=" * 70)
print("TESTE: Verificação do squad-bmad")
print("=" * 70)

# Teste 1: Tentar importar
print("\n1. Tentando importar bmad...")
try:
    import bmad
    print("   ✓ bmad importado com sucesso")
    
    # Verificar atributos
    print("\n2. Verificando atributos disponíveis...")
    attrs = [x for x in dir(bmad) if not x.startswith('_')]
    print(f"   Atributos encontrados: {len(attrs)}")
    if attrs:
        print(f"   Primeiros atributos: {attrs[:10]}")
    
    # Verificar se tem parallel_map
    if hasattr(bmad, 'parallel_map'):
        print("\n   ✓ parallel_map encontrado!")
        print("   squad-bmad está FUNCIONAL")
    else:
        print("\n   ⚠️ parallel_map não encontrado")
        print("   Verificando outras funções de paralelização...")
        parallel_funcs = [x for x in attrs if 'parallel' in x.lower() or 'map' in x.lower()]
        if parallel_funcs:
            print(f"   Funções relacionadas: {parallel_funcs}")
        else:
            print("   Nenhuma função de paralelização encontrada")
    
    # Verificar versão se disponível
    if hasattr(bmad, '__version__'):
        print(f"\n   Versão: {bmad.__version__}")
    elif hasattr(bmad, '__file__'):
        print(f"\n   Localização: {bmad.__file__}")
    
    print("\n" + "=" * 70)
    print("RESULTADO: squad-bmad está INSTALADO")
    print("=" * 70)
    
except ImportError as e:
    print(f"   ✗ Erro ao importar: {e}")
    print("\n" + "=" * 70)
    print("RESULTADO: squad-bmad NÃO está instalado")
    print("=" * 70)
    print("\nO projeto usará multiprocessing como fallback.")
    print("Isso é normal e funciona perfeitamente!")
    print("\nPara instalar squad-bmad (se disponível):")
    print("  pip install squad-bmad")
    print("\nOu instale diretamente do GitHub se houver:")
    print("  pip install git+https://github.com/[repo]/squad-bmad.git")

