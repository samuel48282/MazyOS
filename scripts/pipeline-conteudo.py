#!/usr/bin/env python3
"""
Pipeline Automático de Produção O Bom Pastor
Gera: ideias → roteiro → título → descrição → hashtags → prompts
Salva em: marketing/conteudo/<tema>/
"""

import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import anthropic

load_dotenv()

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
MARKETING_DIR = PROJECT_ROOT / "marketing" / "conteudo"
MEMORIA_DIR = PROJECT_ROOT / "_memoria"

# Validar estrutura do projeto
def validar_estrutura():
    """Valida que a estrutura esperada existe"""
    dirs_esperados = [
        MEMORIA_DIR,
        PROJECT_ROOT / "marketing",
        MARKETING_DIR,
    ]

    for diretorio in dirs_esperados:
        if not diretorio.exists():
            print(f"\n❌ ERRO: Diretório esperado não encontrado: {diretorio}")
            print(f"   A estrutura do projeto pode estar incorreta.")
            print(f"   Verifique se você está rodando do diretório correto.")
            exit(1)

    MARKETING_DIR.mkdir(parents=True, exist_ok=True)

# Carregar contexto do negócio
def carregar_contexto():
    """Lê os arquivos de memória e retorna o contexto do negócio"""
    try:
        with open(MEMORIA_DIR / "empresa.md", "r", encoding="utf-8") as f:
            empresa = f.read()
        with open(MEMORIA_DIR / "preferencias.md", "r", encoding="utf-8") as f:
            preferencias = f.read()
        with open(MEMORIA_DIR / "estrategia.md", "r", encoding="utf-8") as f:
            estrategia = f.read()

        # Validar que conteúdo não está vazio
        if not empresa or not preferencias or not estrategia:
            raise ValueError("Um ou mais arquivos de contexto estão vazios")

        return empresa, preferencias, estrategia
    except FileNotFoundError as e:
        print(f"\n❌ ERRO: Arquivos de contexto não encontrados em {MEMORIA_DIR}")
        print(f"   Procure pelos seguintes arquivos:")
        print(f"   - {MEMORIA_DIR / 'empresa.md'}")
        print(f"   - {MEMORIA_DIR / 'preferencias.md'}")
        print(f"   - {MEMORIA_DIR / 'estrategia.md'}")
        exit(1)
    except ValueError as e:
        print(f"\n❌ ERRO: {e}")
        print(f"   Verifique que os arquivos não estão vazios")
        exit(1)

EMPRESA, PREFERENCIAS, ESTRATEGIA = carregar_contexto()

# ============================================================================
# CLIENTE ANTHROPIC
# ============================================================================

def criar_cliente():
    """Cria cliente Anthropic com API key"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "❌ ANTHROPIC_API_KEY não configurada.\n"
            "Faça: export ANTHROPIC_API_KEY=sua-chave-aqui\n"
            "Ou adicione ao .env do projeto"
        )
    return anthropic.Anthropic(api_key=api_key)

# ============================================================================
# FUNÇÕES DE GERAÇÃO
# ============================================================================

def gerar_ideias(tema: str, quantidade: int = 5) -> list[str]:
    """Gera ideias virais baseado no tema"""
    try:
        client = criar_cliente()

        prompt = f"""
Você é especialista em conteúdo viral para YouTube Shorts e Facebook.

CONTEXTO DO NEGÓCIO:
{EMPRESA}

PREFERÊNCIAS DE TOM:
{PREFERENCIAS}

ESTRATÉGIA ATUAL:
{ESTRATEGIA}

Gere {quantidade} ideias de vídeos VIRAIS para o tema: "{tema}"

Cada ideia deve:
1. Ser específica e acionável
2. Ter potencial alto de engajamento
3. Adequada para Shorts (60-90s)
4. Seguir o tom e estilo da marca

Retorne como lista numerada, uma ideia por linha.
Exemplo:
1. "5 sinais de que você tá no caminho certo"
2. "Como aliviar dores naturalmente em 3 minutos"
"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parsear resposta em lista
        ideias = [linha.strip() for linha in response.content[0].text.split('\n') if linha.strip()]
        return ideias
    except Exception as e:
        print(f"\n❌ ERRO ao gerar ideias: {str(e)}")
        print(f"   Verifique:")
        print(f"   - ANTHROPIC_API_KEY está correta em .env")
        print(f"   - Você tem saldo/quota na sua conta Anthropic")
        print(f"   - Sua conexão com internet está ativa")
        exit(1)


def criar_roteiro(ideia: str) -> str:
    """Cria roteiro curto para o Shorts"""
    try:
        client = criar_cliente()

        prompt = f"""
Você é escritor de roteiros para Shorts (60-90 segundos).

ESTILO E TOM:
{PREFERENCIAS}

IDEIA DO VÍDEO: "{ideia}"

Crie um roteiro estruturado para um Short de 60-90 segundos.

Estrutura:
[GANCHO - 0 a 5s] - Frase que prende
[PROBLEMA - 5 a 30s] - Identifica o problema
[SOLUÇÃO - 30 a 50s] - Oferece a solução
[CTA - 50 a 60s] - Call to action

Retorne o roteiro formatado e pronto para ler/filmar.
"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
    except Exception as e:
        print(f"\n❌ ERRO ao criar roteiro: {str(e)}")
        print(f"   Verifique sua conexão e API key")
        exit(1)


def criar_titulo(ideia: str, roteiro: str) -> str:
    """Cria título com alta retenção"""
    try:
        client = criar_cliente()

        prompt = f"""
Você é especialista em títulos virais para YouTube.

IDEIA: "{ideia}"
ROTEIRO: {roteiro[:200]}...

Gere 3 títulos com alta retenção. Cada um em uma linha.

Critérios:
- Curiosidade (gap que faz querer clicar)
- Emocional (não robótico)
- Compatível com o tom da marca
- 50-60 caracteres máximo

Exemplo:
"Se você sente isso, é hora de mudar"
"Ninguém fala sobre isso"
"Sua vida vai nunca mais ser a mesma"

Retorne apenas os 3 títulos, um por linha.
"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
    except Exception as e:
        print(f"\n❌ ERRO ao criar título: {str(e)}")
        print(f"   Verifique sua conexão e API key")
        exit(1)


def criar_descricao(ideia: str, roteiro: str) -> str:
    """Cria descrição do vídeo"""
    try:
        client = criar_cliente()

        prompt = f"""
Crie uma descrição para YouTube/Facebook (150-200 caracteres).

IDEIA: "{ideia}"
ROTEIRO RESUMIDO: {roteiro[:150]}...

A descrição deve:
1. Começar com o gancho emocional
2. Explicar brevemente o que é o vídeo
3. Terminar com CTA (inscrever, comentar, compartilhar)
4. Manter o tom humanizado

Exemplo:
"Você tá cansado de tentar? Nesse vídeo mostro 5 sinais de que você tá no caminho certo. Assista até o final. Comente qual ressoou com você. 💚"

Retorne apenas a descrição, sem formatação adicional.
"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
    except Exception as e:
        print(f"\n❌ ERRO ao criar descrição: {str(e)}")
        print(f"   Verifique sua conexão e API key")
        exit(1)


def criar_hashtags(ideia: str, tema: str) -> str:
    """Cria hashtags estratégicas"""
    try:
        client = criar_cliente()

        prompt = f"""
Crie hashtags estratégicas para o vídeo.

TEMA: {tema}
IDEIA: "{ideia}"

Gere 15 hashtags no padrão:
- 3 hashtags GRANDES (100M+ buscas) - ex: #YouTube #Fe #Motivacao
- 7 hashtags MÉDIAS (10M-100M) - ex: #BemEstar #SaudeNatural
- 5 hashtags PEQUENAS/NICHO (1M-10M) - ex: #RefugioDaAlma #DicasDeVida

Formato: #Hashtag (sem espaços)

Retorne como lista, uma por linha.
"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
    except Exception as e:
        print(f"\n❌ ERRO ao criar hashtags: {str(e)}")
        print(f"   Verifique sua conexão e API key")
        exit(1)


def criar_prompt_imagem(ideia: str) -> str:
    """Cria prompt para DALL-E/Midjourney de capa/thumbnail"""
    try:
        client = criar_cliente()

        prompt = f"""
Crie um prompt descritivo para gerar a CAPA/THUMBNAIL do vídeo.

IDEIA: "{ideia}"

O prompt deve:
1. Descrever uma imagem impactante (capa/thumbnail)
2. Incluir as cores da marca (verde, preto, branco)
3. Ser visual e chamativo
4. Ter uma pessoa ou elemento emocional
5. Ser específico para uso em DALL-E, Midjourney ou Replicate

Formato:
"A vibrant thumbnail showing... with green and white colors, high contrast, emotional, professional design style"

Retorne apenas o prompt, sem explicações.
"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
    except Exception as e:
        print(f"\n❌ ERRO ao criar prompt de imagem: {str(e)}")
        print(f"   Verifique sua conexão e API key")
        exit(1)


def criar_prompt_video(roteiro: str, ideia: str) -> str:
    """Cria prompt para gerar vídeo (Synthesia, Pika, etc)"""
    try:
        client = criar_cliente()

        prompt = f"""
Crie um prompt técnico para gerar vídeo (Synthesia, Pika, Runway).

IDEIA: "{ideia}"
ROTEIRO: {roteiro[:300]}...

O prompt deve descrever:
1. Visual principal (cenários, cores - verde/branco/preto)
2. Movimento/transições (dinâmico, rápido)
3. Textos/legendas que aparecem
4. Ritmo (energético, emocional)
5. Duração (60-90 segundos)

Formato técnico, pronto para colar em ferramenta de IA.

Exemplo:
"Create a 60-second video with: opening scene of nature in green tones, dynamic transitions, white text overlay with main message, emotional music background, fast-paced cuts every 5 seconds, final CTA screen in green with white text"

Retorne apenas o prompt.
"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
    except Exception as e:
        print(f"\n❌ ERRO ao criar prompt de vídeo: {str(e)}")
        print(f"   Verifique sua conexão e API key")
        exit(1)

# ============================================================================
# ARMAZENAMENTO
# ============================================================================

def salvar_conteudo(tema: str, ideia: str, roteiro: str, titulo: str,
                    descricao: str, hashtags: str, prompt_img: str,
                    prompt_vid: str):
    """Salva todo o conteúdo em arquivos organizados"""

    # Criar pasta do tema
    pasta_tema = MARKETING_DIR / tema.lower().replace(" ", "-").replace("/", "-")
    pasta_tema.mkdir(parents=True, exist_ok=True)

    # Timestamp para identificar
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Arquivo JSON com todos os dados
    dados = {
        "timestamp": timestamp,
        "tema": tema,
        "ideia": ideia,
        "roteiro": roteiro,
        "titulo": titulo,
        "descricao": descricao,
        "hashtags": hashtags,
        "prompt_imagem": prompt_img,
        "prompt_video": prompt_vid,
    }

    arquivo_json = pasta_tema / f"{timestamp}-conteudo.json"
    with open(arquivo_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    # Arquivo markdown legível
    arquivo_md = pasta_tema / f"{timestamp}-conteudo.md"
    md_content = f"""# {ideia}

## Informações
- **Tema:** {tema}
- **Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

## Roteiro
{roteiro}

## Títulos (escolha um)
{titulo}

## Descrição
{descricao}

## Hashtags
{hashtags}

## Prompt para Imagem/Capa
```
{prompt_img}
```

## Prompt para Vídeo
```
{prompt_vid}
```

---
**Status:** Pronto para revisar e publicar
"""

    with open(arquivo_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    return pasta_tema, arquivo_json, arquivo_md

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Pipeline principal"""
    validar_estrutura()

    print("\n" + "="*60)
    print("🚀 PIPELINE DE CONTEÚDO O BOM PASTOR")
    print("="*60 + "\n")

    # Pergunta o tema
    print("Escolha o tema:")
    print("1. Saúde Natural")
    print("2. Fé e Motivação")
    print("3. Bem-estar")
    print("4. Outro (descrever)")

    opcao = input("\nOpção (1-4): ").strip()

    temas_padrao = {
        "1": "Saúde Natural",
        "2": "Fé e Motivação",
        "3": "Bem-estar",
    }

    tema = temas_padrao.get(opcao, input("Descreva o tema: ")).strip()

    if not tema:
        print("❌ Tema não fornecido.")
        return

    print(f"\n📝 Tema selecionado: {tema}")

    try:
        # Step 1: Ideias
        print("\n⏳ Gerando ideias virais...")
        ideias = gerar_ideias(tema, quantidade=5)
        print("✅ Ideias geradas:")
        for i, ideia in enumerate(ideias, 1):
            print(f"  {i}. {ideia}")

        # Selecionar ideia
        try:
            escolha = int(input("\nEscolha uma ideia (1-5): ").strip()) - 1
            ideia_escolhida = ideias[escolha]
        except (ValueError, IndexError):
            ideia_escolhida = ideias[0]
            print(f"Usando ideia 1: {ideia_escolhida}")

        print(f"\n🎯 Ideia selecionada: {ideia_escolhida}")

        # Step 2: Roteiro
        print("\n⏳ Criando roteiro...")
        roteiro = criar_roteiro(ideia_escolhida)
        print("✅ Roteiro criado")

        # Step 3: Título
        print("\n⏳ Criando títulos...")
        titulo = criar_titulo(ideia_escolhida, roteiro)
        print("✅ Títulos criados")

        # Step 4: Descrição
        print("\n⏳ Criando descrição...")
        descricao = criar_descricao(ideia_escolhida, roteiro)
        print("✅ Descrição criada")

        # Step 5: Hashtags
        print("\n⏳ Criando hashtags...")
        hashtags = criar_hashtags(ideia_escolhida, tema)
        print("✅ Hashtags criadas")

        # Step 6: Prompt imagem
        print("\n⏳ Criando prompt de imagem...")
        prompt_img = criar_prompt_imagem(ideia_escolhida)
        print("✅ Prompt de imagem criado")

        # Step 7: Prompt vídeo
        print("\n⏳ Criando prompt de vídeo...")
        prompt_vid = criar_prompt_video(roteiro, ideia_escolhida)
        print("✅ Prompt de vídeo criado")

        # Step 8: Salvar
        print("\n⏳ Salvando conteúdo...")
        pasta, arquivo_json, arquivo_md = salvar_conteudo(
            tema, ideia_escolhida, roteiro, titulo, descricao, hashtags,
            prompt_img, prompt_vid
        )
        print(f"✅ Conteúdo salvo em: {pasta}")
        print(f"   - JSON: {arquivo_json.name}")
        print(f"   - Markdown: {arquivo_md.name}")

        # Resumo
        print("\n" + "="*60)
        print("✨ CONTEÚDO COMPLETO PRONTO")
        print("="*60)
        print(f"\n📂 Pasta: marketing/conteudo/{tema.lower().replace(' ', '-')}/")
        print(f"\n🎬 Próximos passos:")
        print("1. Revisar os arquivos criados")
        print("2. Usar os prompts para gerar imagem e vídeo")
        print("3. Publicar nos canais")
        print("\n")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("Verifique se ANTHROPIC_API_KEY está configurada.")
        return 1

if __name__ == "__main__":
    exit(main() or 0)
