"""
Módulo para definir e gerenciar as ferramentas (tools) que os agentes podem usar
para aumentar suas capacidades e autonomia.

Uma ferramenta (tool) é uma função que um agente pode invocar para realizar
uma ação específica, como buscar informações, gerar recursos, ou interagir
com sistemas externos.
"""
from typing import Dict, Any, Callable, List, Optional, Union
import inspect
import functools
import json
import logging
import os
from pathlib import Path
from utils.logger import AILogger

# Get the app_logs directory path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
app_logs_dir = backend_dir / "app_logs"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tools")
logger.setLevel(logging.INFO)
ai_logger = AILogger(log_dir=str(app_logs_dir))


class Tool:
    """
    Representa uma ferramenta que um agente pode usar para interagir com o ambiente.
    """

    def __init__(
        self,
        name: str,
        func: Callable,
        description: str,
        required_params: List[str] = None,
        optional_params: Dict[str, Any] = None
    ):
        """
        Inicializa uma nova ferramenta.

        Args:
            name: Nome único da ferramenta
            func: Função que implementa a ferramenta
            description: Descrição do que a ferramenta faz
            required_params: Lista de nomes de parâmetros obrigatórios
            optional_params: Dicionário de parâmetros opcionais com valores padrão
        """
        self.name = name
        self.func = func
        self.description = description
        self.required_params = required_params or []
        self.optional_params = optional_params or {}

        # Extrair assinatura da função para validação
        self.signature = inspect.signature(func)

        # Validar que os parâmetros obrigatórios existem na assinatura
        for param in self.required_params:
            if param not in self.signature.parameters:
                raise ValueError(
                    f"Parâmetro obrigatório '{param}' não existe na função {func.__name__}")

    def __call__(self, **kwargs) -> Any:
        """
        Executa a ferramenta com os argumentos fornecidos.
        """
        # Verificar se todos os parâmetros obrigatórios foram fornecidos
        for param in self.required_params:
            if param not in kwargs:
                raise ValueError(
                    f"Parâmetro obrigatório '{param}' não fornecido para a ferramenta {self.name}")

        # Adicionar valores padrão para parâmetros opcionais não fornecidos
        for param, default_value in self.optional_params.items():
            if param not in kwargs:
                kwargs[param] = default_value

        # Filtrar apenas os parâmetros que existem na assinatura da função
        valid_kwargs = {k: v for k, v in kwargs.items(
        ) if k in self.signature.parameters}

        # Executar a função
        try:
            result = self.func(**valid_kwargs)
            return result
        except Exception as e:
            logger.error(
                f"Erro ao executar a ferramenta {self.name}: {str(e)}")
            return {"error": str(e)}

    def to_dict(self) -> Dict[str, Any]:
        """
        Retorna uma representação em dicionário da ferramenta para inclusão em prompts.
        """
        return {
            "name": self.name,
            "description": self.description,
            "required_params": self.required_params,
            "optional_params": self.optional_params
        }


class ToolRegistry:
    """
    Registro central de ferramentas disponíveis para os agentes.
    """

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, required_params: List[str] = None, optional_params: Dict[str, Any] = None):
        """
        Decorator para registrar uma ferramenta.
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Log antes da execução
                ai_logger.log_agent_call(
                    agent_name="MCP",
                    method_name=name,
                    input_data={"args": args, "kwargs": kwargs}
                )

                try:
                    # Executar a função
                    result = func(*args, **kwargs)

                    # Log do resultado
                    ai_logger.log_agent_call(
                        agent_name="MCP",
                        method_name=name,
                        input_data={"args": args, "kwargs": kwargs},
                        output_data=result
                    )

                    return result
                except Exception as e:
                    # Log do erro
                    ai_logger.log_agent_call(
                        agent_name="MCP",
                        method_name=name,
                        input_data={"args": args, "kwargs": kwargs},
                        error=str(e)
                    )
                    raise

            # Preservar metadata da função original
            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__

            # Registrar a ferramenta com seus metadados
            self.tools[name] = {
                "func": wrapper,
                "description": description,
                "required_params": required_params or [],
                "optional_params": optional_params or {},
                "signature": inspect.signature(func)
            }

            return wrapper
        return decorator

    def get_tool(self, name: str) -> Dict[str, Any]:
        """Retorna uma ferramenta registrada pelo nome."""
        return self.tools.get(name)

    def execute(self, name: str, *args, **kwargs) -> Any:
        """Executa uma ferramenta registrada."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")

        return tool["func"](*args, **kwargs)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Lista todas as ferramentas registradas com suas descrições."""
        return [
            {
                "name": name,
                "description": tool["description"],
                "required_params": tool["required_params"],
                "optional_params": tool["optional_params"]
            }
            for name, tool in self.tools.items()
        ]


# Instância global do registro de ferramentas
tool_registry = ToolRegistry()
