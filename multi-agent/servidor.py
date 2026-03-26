"""
Servidor Web - Studio PI Multi-Agentes
"""
import asyncio
import json
import os
import sys
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

# Garante que o módulo de agentes é encontrado
sys.path.insert(0, os.path.dirname(__file__))

from claude_agent_sdk import (
    query, ClaudeAgentOptions, AgentDefinition,
    ResultMessage, SystemMessage, AssistantMessage,
    TextBlock, ToolUseBlock,
)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Agentes ────────────────────────────────────────────────────────────────────

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
- Indicadores de desempenho (KPIs)
Apresente dados de forma clara com análises objetivas.""",
        tools=["Read", "Write"],
    ),
    "marketing": AgentDefinition(
        description="Especialista em marketing digital, redes sociais, branding e posicionamento do escritório.",
        prompt="""Você é um especialista em marketing para escritório de arquitetura.
Seu foco é:
- Estratégia de conteúdo (Instagram, LinkedIn, Behance)
- Copywriting e storytelling de projetos
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
- Referências e precedentes de projeto
Pense de forma criativa e inovadora.""",
        tools=["Read", "Write"],
    ),
    "gestao-interna": AgentDefinition(
        description="Especialista em processos internos, gestão de equipe, POPs e organização do escritório.",
        prompt="""Você é um especialista em gestão interna de escritório de arquitetura.
Seu foco é:
- Criação e revisão de POPs
- Gestão de equipe e processos
- Fluxos de trabalho e comunicação interna
Seja sistemático, claro e orientado a processos.""",
        tools=["Read", "Glob", "Grep", "Write"],
    ),
    "documentacoes": AgentDefinition(
        description="Especialista em documentação técnica, relatórios, memoriais e registros de projeto.",
        prompt="""Você é um especialista em documentação para projetos de arquitetura.
Seu foco é:
- Memoriais descritivos e justificativos
- Relatórios técnicos de vistorias
- Checklists e controle de qualidade
Seja preciso, detalhado e organize as informações de forma lógica.""",
        tools=["Read", "Glob", "Grep", "Write"],
    ),
}

SYSTEM_PROMPT = """Você é o Orquestrador do Studio PI, um escritório de arquitetura.
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
2. Delegue para o(s) agente(s) mais adequado(s)
3. Integre as respostas de forma coerente
4. Entregue um resultado final claro e completo

Responda sempre em português brasileiro."""

# ── SSE Stream ─────────────────────────────────────────────────────────────────

class Tarefa(BaseModel):
    texto: str

def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

async def stream_agentes(tarefa: str) -> AsyncGenerator[str, None]:
    yield sse("inicio", {"mensagem": "🧠 Orquestrador recebeu a tarefa..."})
    await asyncio.sleep(0.1)

    try:
        async for message in query(
            prompt=tarefa,
            options=ClaudeAgentOptions(
                cwd=os.path.dirname(os.path.abspath(__file__)) + "/..",
                allowed_tools=["Read", "Glob", "Grep", "Write", "Agent"],
                system_prompt=SYSTEM_PROMPT,
                agents=AGENTES,
                max_turns=30,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        yield sse("pensamento", {"texto": block.text.strip()})
                        await asyncio.sleep(0.05)

                    elif isinstance(block, ToolUseBlock) and block.name == "Agent":
                        nome = block.input.get("agent_type", "agente")
                        missao = block.input.get("prompt", "")[:200]
                        yield sse("agente_chamado", {"nome": nome, "missao": missao})
                        await asyncio.sleep(0.05)

            elif isinstance(message, ResultMessage):
                yield sse("resultado", {"texto": message.result})

    except Exception as e:
        yield sse("erro", {"mensagem": str(e)})

    yield sse("fim", {})

# ── Rotas ──────────────────────────────────────────────────────────────────────

@app.post("/tarefa")
async def executar_tarefa(tarefa: Tarefa):
    return StreamingResponse(
        stream_agentes(tarefa.texto),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@app.get("/", response_class=HTMLResponse)
async def interface():
    with open(os.path.join(os.path.dirname(__file__), "interface.html"), encoding="utf-8") as f:
        return f.read()
