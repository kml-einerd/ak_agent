"""
Atomic — Registro de operações do forge com metadata e JSON Schema.

Inspirado no @atomic() do astron-rpa (Apache 2.0).
Adaptado para registrar sub-waves e operações do Code Forge como blocos
com introspecção automática de parâmetros.

Uso:
    from atomic import atomic, AtomicRegistry

    @atomic(group="android", title="Portal Client", model="haiku")
    def portal_client(files: list[str], test_command: str = "go test ./..."):
        '''Cria HTTP client Go para DroidRun Portal.'''
        ...

    # Listar todas as operações registradas com JSON Schema
    AtomicRegistry.json()

    # Executar uma operação
    AtomicRegistry.run("android.portal_client", files=["pkg/android/client.go"])
"""

import inspect
import json
import functools
from dataclasses import dataclass, field, asdict
from typing import Any, Optional, Callable


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

@dataclass
class ParamMeta:
    """Metadata de um parâmetro de operação."""
    key: str
    title: str
    type: str  # str, int, float, bool, list, dict
    required: bool = True
    default: Any = None
    description: str = ""


@dataclass
class AtomicMeta:
    """Metadata de uma operação atômica."""
    key: str            # group.func_name
    title: str
    group: str
    description: str
    model: str          # haiku, sonnet, opus
    inputs: list[ParamMeta] = field(default_factory=list)
    outputs: list[ParamMeta] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    acceptance: str = ""
    test_command: str = ""
    src: str = ""       # module.func qualified name


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class AtomicRegistry:
    """Registro global de operações atômicas do forge."""

    _operations: dict[str, AtomicMeta] = {}
    _functions: dict[str, Callable] = {}

    @classmethod
    def register(cls, key: str, meta: AtomicMeta, func: Callable):
        cls._operations[key] = meta
        cls._functions[key] = func

    @classmethod
    def get(cls, key: str) -> Optional[AtomicMeta]:
        return cls._operations.get(key)

    @classmethod
    def list_keys(cls) -> list[str]:
        return list(cls._operations.keys())

    @classmethod
    def run(cls, key: str, **kwargs) -> Any:
        """Executa uma operação atômica pelo key."""
        func = cls._functions.get(key)
        if not func:
            raise KeyError(f"Operação não encontrada: {key}")

        meta = cls._operations[key]

        # Validar parâmetros obrigatórios
        for param in meta.inputs:
            if param.required and param.key not in kwargs and param.default is None:
                raise ValueError(f"Parâmetro obrigatório ausente: {param.key}")

        # Aplicar defaults
        for param in meta.inputs:
            if param.key not in kwargs and param.default is not None:
                kwargs[param.key] = param.default

        return func(**kwargs)

    @classmethod
    def json(cls) -> dict:
        """Gera JSON Schema de todas as operações registradas."""
        result = {}
        for key, meta in cls._operations.items():
            result[key] = {
                "key": meta.key,
                "title": meta.title,
                "group": meta.group,
                "description": meta.description,
                "model": meta.model,
                "src": meta.src,
                "depends_on": meta.depends_on,
                "acceptance": meta.acceptance,
                "test_command": meta.test_command,
                "inputSchema": _params_to_json_schema(meta.inputs),
                "outputSchema": _params_to_json_schema(meta.outputs),
            }
        return result

    @classmethod
    def to_subwaves(cls, group: Optional[str] = None) -> list[dict]:
        """Converte operações registradas em sub-waves para o forge.

        Se group é especificado, filtra apenas operações desse grupo.
        """
        subwaves = []
        for key, meta in cls._operations.items():
            if group and meta.group != group:
                continue
            subwaves.append({
                "id": f"sw-{key.replace('.', '-')}",
                "title": meta.title,
                "model": meta.model,
                "depends_on": meta.depends_on,
                "task_description": meta.description,
                "acceptance": meta.acceptance,
                "test_command": meta.test_command,
                "files_to_edit": [],  # preenchido pelo planner
                "context_files": {},
                "test_files": {},
            })
        return subwaves

    @classmethod
    def clear(cls):
        cls._operations.clear()
        cls._functions.clear()


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------

def atomic(group: str = "", title: str = "", model: str = "haiku",
           depends_on: list[str] = None, acceptance: str = "",
           test_command: str = ""):
    """Decorator que registra uma função como operação atômica do forge.

    Faz introspecção automática dos parâmetros (nome, tipo, default, docstring).

    Exemplo:
        @atomic(group="bodycam", title="Event Logger", model="haiku")
        def event_logger(sink_type: str = "cloud_logging", buffer_size: int = 100):
            '''Cria sistema de logging de eventos com sink plugável.'''
            ...
    """
    def decorator(func):
        # Introspecção de parâmetros
        sig = inspect.signature(func)
        inputs = []
        for name, param in sig.parameters.items():
            ptype = "str"  # default
            if param.annotation != inspect.Parameter.empty:
                ptype = _python_type_to_str(param.annotation)

            required = param.default == inspect.Parameter.empty
            default = None if required else param.default

            inputs.append(ParamMeta(
                key=name,
                title=name.replace("_", " ").title(),
                type=ptype,
                required=required,
                default=default,
                description="",
            ))

        func_name = func.__name__
        key = f"{group}.{func_name}" if group else func_name

        meta = AtomicMeta(
            key=key,
            title=title or func_name.replace("_", " ").title(),
            group=group,
            description=(func.__doc__ or "").strip(),
            model=model,
            inputs=inputs,
            depends_on=depends_on or [],
            acceptance=acceptance,
            test_command=test_command,
            src=f"{func.__module__}.{func.__qualname__}",
        )

        AtomicRegistry.register(key, meta, func)

        @functools.wraps(func)
        def wrapper(**kwargs):
            return AtomicRegistry.run(key, **kwargs)

        wrapper._atomic_meta = meta
        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _python_type_to_str(annotation) -> str:
    """Converte tipo Python para string JSON Schema."""
    origin = getattr(annotation, "__origin__", None)
    if origin is list:
        return "array"
    if origin is dict:
        return "object"
    return TYPE_MAP.get(annotation, "string")


def _params_to_json_schema(params: list[ParamMeta]) -> dict:
    """Converte lista de ParamMeta para JSON Schema."""
    schema = {
        "type": "object",
        "properties": {},
        "required": [],
    }
    for p in params:
        prop = {"type": p.type, "description": p.description or p.title}
        if p.default is not None:
            prop["default"] = p.default
        schema["properties"][p.key] = prop
        if p.required:
            schema["required"].append(p.key)
    return schema
