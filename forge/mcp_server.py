#!/usr/bin/env python3
"""
MCP Server do Code Forge — Expõe operações do forge como MCP Tools.

Inspirado no streamable_mcp.py do astron-rpa (Apache 2.0).
Adaptado para expor o Code Forge como MCP server que o Akita/Claude pode chamar.

Uso:
    # Rodar standalone
    python3 mcp_server.py

    # Ou como MCP server no Claude Code (settings.json)
    {
      "mcpServers": {
        "code-forge": {
          "command": "python3",
          "args": ["/home/agdis/pm-os-gcp/code-forge/mcp_server.py"]
        }
      }
    }

Tools expostos:
    - forge_plan: Decompõe um plano em sub-waves
    - forge_run: Executa geração massiva de código
    - forge_status: Verifica status de um run
    - forge_collect: Coleta resultados de um run
"""

import json
import os
import sys
import subprocess
from pathlib import Path

# MCP SDK (pip install mcp)
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

FORGE_DIR = Path(__file__).parent
FORGE_PY = FORGE_DIR / "forge.py"


def _run_forge(args: list[str], timeout: int = 600) -> str:
    """Roda forge.py como subprocess e retorna output."""
    cmd = [sys.executable, str(FORGE_PY)] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(FORGE_DIR.parent),  # pm-os-gcp root
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        return output
    except subprocess.TimeoutExpired:
        return f"[timeout after {timeout}s]"
    except Exception as e:
        return f"[error]: {str(e)}"


def create_server() -> "Server":
    """Cria MCP Server com tools do forge."""
    app = Server("code-forge")

    @app.list_tools()
    async def list_tools() -> list["types.Tool"]:
        return [
            types.Tool(
                name="forge_plan",
                description="Decompõe um plano de implementação em sub-waves independentes para geração massiva paralela. Retorna preview das sub-waves, custo estimado e tempo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_path": {
                            "type": "string",
                            "description": "Caminho absoluto para o arquivo .md do plano",
                        },
                        "model": {
                            "type": "string",
                            "description": "Modelo padrão para geração (haiku, sonnet, opus)",
                            "default": "haiku",
                        },
                        "machines": {
                            "type": "integer",
                            "description": "Número máximo de máquinas paralelas",
                            "default": 20,
                        },
                    },
                    "required": ["plan_path"],
                },
            ),
            types.Tool(
                name="forge_run",
                description="Executa geração massiva de código: decompõe plano, distribui para workers PM-OS, monitora, coleta resultados. Retorna run_id e link do monitor.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_path": {
                            "type": "string",
                            "description": "Caminho absoluto para o arquivo .md do plano",
                        },
                        "model": {
                            "type": "string",
                            "description": "Modelo padrão para geração",
                            "default": "haiku",
                        },
                        "machines": {
                            "type": "integer",
                            "description": "Máquinas paralelas",
                            "default": 20,
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "Se true, mostra preview sem executar",
                            "default": False,
                        },
                    },
                    "required": ["plan_path"],
                },
            ),
            types.Tool(
                name="forge_status",
                description="Verifica status de um forge run em andamento. Mostra progresso, sub-waves completadas, custo parcial.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "run_id": {
                            "type": "string",
                            "description": "ID do forge run (ex: forge-20260324-053417)",
                        },
                    },
                    "required": ["run_id"],
                },
            ),
            types.Tool(
                name="forge_collect",
                description="Coleta resultados de um forge run completado e merge no projeto local.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "run_id": {
                            "type": "string",
                            "description": "ID do forge run",
                        },
                    },
                    "required": ["run_id"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list["types.TextContent"]:
        if name == "forge_plan":
            args = ["run", arguments["plan_path"], "--dry"]
            if arguments.get("model"):
                args += ["--model", arguments["model"]]
            if arguments.get("machines"):
                args += ["--machines", str(arguments["machines"])]
            output = _run_forge(args, timeout=120)

        elif name == "forge_run":
            args = ["run", arguments["plan_path"]]
            if arguments.get("dry_run"):
                args.append("--dry")
            if arguments.get("model"):
                args += ["--model", arguments["model"]]
            if arguments.get("machines"):
                args += ["--machines", str(arguments["machines"])]
            output = _run_forge(args, timeout=1800)

        elif name == "forge_status":
            run_id = arguments["run_id"]
            # Read status from temp file
            tasks_file = f"/tmp/forge-tasks-{run_id}.json"
            if os.path.exists(tasks_file):
                with open(tasks_file) as f:
                    tasks = json.load(f)
                done = sum(1 for t in tasks.values()
                          if t.get("status") in ("done", "passed"))
                failed = sum(1 for t in tasks.values()
                            if t.get("status") == "failed")
                total = len(tasks)
                cost = sum(t.get("cost_usd", 0) for t in tasks.values())
                output = (f"Run: {run_id}\n"
                         f"Progress: {done}/{total} done, {failed} failed\n"
                         f"Cost: ${cost:.2f}\n"
                         f"Monitor: python3 /tmp/forge-monitor-{run_id}.py")
            else:
                output = f"Run {run_id} não encontrado"

        elif name == "forge_collect":
            output = _run_forge(["collect", arguments["run_id"]], timeout=300)

        else:
            output = f"Tool desconhecido: {name}"

        return [types.TextContent(type="text", text=output)]

    return app


async def main():
    """Roda MCP server via stdio."""
    if not HAS_MCP:
        print("MCP SDK não instalado. Rode: pip install mcp", file=sys.stderr)
        sys.exit(1)

    app = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
