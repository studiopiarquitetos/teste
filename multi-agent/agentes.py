"""
Sistema de Multi-Agentes - Studio PI
=====================================
Orquestrador com sala virtual de agentes especializados.

Uso:
    python agentes.py "sua tarefa aqui"
    python agentes.py  (modo interativo)
"""

import anyio
import sys
import os
from claude_agent_sdk import (
    query, ClaudeAgentOptions, AgentDefinition,
    ResultMessage, SystemMessage, AssistantMessage,
    TextBlock, ToolUseBlock, ToolResultBlock,
)

# ─────────────────────────────────────────────
# DEFINIÇÃO DOS AGENTES ESPECIALIZADOS
# ─────────────────────────────────────────────

AGENTES = {
    "arquiteto-legal": AgentDefinition(
        description="Especialista em projetos legais, aprovações, documentação técnica e normas de arquitetura.",
        prompt="""Você é um arquiteto especialista em projetos legais de arquitetura.
Seu foco é:
- Documentação técnica (memoriais, ARTs, RRTs)
- Conformidade com normas (NBR, ABNT, Plano Diretor)
- Processos de aprovação em prefeituras
- Projetos executivos e complementares
Responda sempre com precisão técnica e indique referências normativas quando pertinente.""",
        tools=["Read", "Glob", "Grep", "Write"],
    ),

    "comercial": AgentDefinition(
        description="Especialista em vendas, propostas comerciais, contratos e relacionamento com clientes.",
        prompt="""Você é um especialista em comercial para escritório de arquitetura.
Seu foco é:
- Elaboração de propostas e orçamentos
- Contratos e escopo de serviços
- Captação e fidelização de clientes
- Apresentações e materiais comerciais
- Precificação de projetos arquitetônicos
Seja persuasivo, claro e profissional.""",
        tools=["Read", "Write"],
    ),

    "financeiro": AgentDefinition(
        description="Especialista em controle financeiro, fluxo de caixa e gestão de custos do escritório.",
        prompt="""Você é um especialista em gestão financeira para escritório de arquitetura.
Seu foco é:
- Fluxo de caixa e planejamento financeiro
- Controle de horas e rentabilidade de projetos
- Análise de custos e despesas
- Indicadores de desempenho (KPIs)
- Faturamento e recebíveis
Apresente dados de forma clara com análises objetivas.""",
        tools=["Read", "Write"],
    ),

    "marketing": AgentDefinition(
        description="Especialista em marketing digital, redes sociais, branding e posicionamento do escritório.",
        prompt="""Você é um especialista em marketing para escritório de arquitetura.
Seu foco é:
- Estratégia de conteúdo (Instagram, LinkedIn, Behance)
- Copywriting e storytelling de projetos
- Branding e identidade visual
- SEO e presença digital
- Campanhas e geração de leads
Crie conteúdos criativos e alinhados ao mercado de arquitetura.""",
        tools=["Read", "Write"],
    ),

    "criativos": AgentDefinition(
        description="Especialista em desenvolvimento criativo de projetos, conceitos e soluções de design.",
        prompt="""Você é um arquiteto criativo especialista em conceito e design.
Seu foco é:
- Desenvolvimento de conceito arquitetônico
- Partido arquitetônico e linguagem formal
- Soluções espaciais e funcionais
- Referências e precedentes de projeto
- Apresentações e pranchas de design
Pense de forma criativa e inovadora, sempre fundamentando as escolhas.""",
        tools=["Read", "Write"],
    ),

    "gestao-interna": AgentDefinition(
        description="Especialista em processos internos, gestão de equipe, POPs e organização do escritório.",
        prompt="""Você é um especialista em gestão interna de escritório de arquitetura.
Seu foco é:
- Criação e revisão de POPs (Procedimentos Operacionais Padrão)
- Gestão de equipe e processos
- Organização de arquivos e documentos
- Fluxos de trabalho e comunicação interna
- Onboarding e treinamento
Seja sistemático, claro e orientado a processos.""",
        tools=["Read", "Glob", "Grep", "Write"],
    ),

    "documentacoes": AgentDefinition(
        description="Especialista em documentação técnica, relatórios, memoriais e registros de projeto.",
        prompt="""Você é um especialista em documentação para projetos de arquitetura.
Seu foco é:
- Memoriais descritivos e justificativos
- Relatórios técnicos de vistorias
- Diários de obra e atas de reunião
- Documentação fotográfica e registros
- Checklists e controle de qualidade
Seja preciso, detalhado e organize as informações de forma lógica.""",
        tools=["Read", "Glob", "Grep", "Write"],
    ),
}

# ─────────────────────────────────────────────
# PROMPT DO ORQUESTRADOR
# ─────────────────────────────────────────────

SYSTEM_PROMPT_ORQUESTRADOR = """Você é o Orquestrador do Studio PI, um escritório de arquitetura.

Você coordena uma equipe de agentes especializados:
- arquiteto-legal: projetos legais, normas e aprovações
- comercial: propostas, contratos e clientes
- financeiro: controle financeiro e fluxo de caixa
- marketing: conteúdo, redes sociais e branding
- criativos: conceito e design de projetos
- gestao-interna: POPs, processos e organização
- documentacoes: documentação técnica e relatórios

Quando receber uma tarefa:
1. Analise o que é necessário
2. Delegue para o(s) agente(s) mais adequado(s) usando a ferramenta Agent
3. Integre as respostas de forma coerente
4. Entregue um resultado final claro e completo

Responda sempre em português brasileiro."""

# ─────────────────────────────────────────────
# EXECUÇÃO
# ─────────────────────────────────────────────

ICONES_AGENTES = {
    "arquiteto-legal": "📐",
    "comercial":       "🤝",
    "financeiro":      "💰",
    "marketing":       "📣",
    "criativos":       "🎨",
    "gestao-interna":  "📋",
    "documentacoes":   "📄",
}

async def executar(tarefa: str):
    print(f"\n🏗️  Studio PI - Sistema Multi-Agentes")
    print(f"📋 Tarefa: {tarefa}")
    print("─" * 50)

    session_id = None
    agente_atual = "🧠 Orquestrador"

    async for message in query(
        prompt=tarefa,
        options=ClaudeAgentOptions(
            cwd=os.path.dirname(os.path.abspath(__file__)) + "/..",
            allowed_tools=["Read", "Glob", "Grep", "Write", "Agent"],
            system_prompt=SYSTEM_PROMPT_ORQUESTRADOR,
            agents=AGENTES,
            max_turns=30,
        ),
    ):
        if isinstance(message, SystemMessage):
            if message.subtype == "init":
                session_id = message.data.get("session_id")
                print(f"\n🧠 Orquestrador iniciado\n")

        elif isinstance(message, AssistantMessage):
            for block in message.content:
                # Orquestrador pensando / falando
                if isinstance(block, TextBlock) and block.text.strip():
                    print(f"\n💬 {agente_atual}:")
                    print(f"   {block.text.strip()[:300]}{'...' if len(block.text) > 300 else ''}")

                # Orquestrador chamando um agente
                elif isinstance(block, ToolUseBlock):
                    if block.name == "Agent":
                        nome = block.input.get("agent_type", "agente")
                        icone = ICONES_AGENTES.get(nome, "🤖")
                        agente_atual = f"{icone} {nome}"
                        print(f"\n{'─'*50}")
                        print(f"  ➜ Chamando {agente_atual}...")
                        tarefa_agente = block.input.get("prompt", "")
                        if tarefa_agente:
                            print(f"  📩 Missão: {tarefa_agente[:200]}")
                        print(f"{'─'*50}")
                    else:
                        print(f"\n🔧 {agente_atual} usando ferramenta: {block.name}")

        elif isinstance(message, ResultMessage):
            print(f"\n\n{'═'*50}")
            print(f"✅ RESULTADO FINAL\n")
            print(message.result)
            print(f"{'═'*50}")
            if session_id:
                print(f"📎 Session ID: {session_id}")


async def modo_interativo():
    print("\n🏗️  Studio PI - Sistema Multi-Agentes")
    print("Agentes disponíveis:", ", ".join(AGENTES.keys()))
    print("Digite 'sair' para encerrar.\n")

    while True:
        try:
            tarefa = input("📝 Tarefa: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Encerrando.")
            break

        if tarefa.lower() in ("sair", "exit", "quit"):
            print("👋 Encerrando.")
            break

        if not tarefa:
            continue

        await executar(tarefa)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        tarefa = " ".join(sys.argv[1:])
        anyio.run(executar, tarefa)
    else:
        anyio.run(modo_interativo)
