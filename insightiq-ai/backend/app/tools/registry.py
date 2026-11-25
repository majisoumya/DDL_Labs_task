"""Controlled AI Tool Registry for Validated Analytics Invocation and OpenAI Schema Generation."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Type, Union
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.tools.schemas import ToolExecutionResult

logger = get_logger("insightiq.tools.registry")


def _sanitize_for_json(obj: Any) -> Any:
    """Recursively converts Decimals and non-primitive types into JSON-serializable primitives."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(item) for item in obj]
    elif hasattr(obj, "model_dump"):
        return _sanitize_for_json(obj.model_dump())
    return obj


@dataclass
class ToolDefinition:
    """Specification of an approved analytics tool."""
    name: str
    description: str
    input_schema: Type[BaseModel]
    func: Callable[..., Any]
    requires_db: bool = True


class ToolRegistry:
    """Central registry and executor for controlled AI analytics tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: Type[BaseModel],
        requires_db: bool = True,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a function as an approved tool."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.register_tool(
                ToolDefinition(
                    name=name,
                    description=description,
                    input_schema=input_schema,
                    func=func,
                    requires_db=requires_db,
                )
            )
            return func
        return decorator

    def register_tool(self, tool: ToolDefinition) -> None:
        """Registers a ToolDefinition into the internal dictionary."""
        if tool.name in self._tools:
            logger.warning("Overwriting existing tool registration: %s", tool.name)
        self._tools[tool.name] = tool
        logger.info("Registered approved tool: %s", tool.name)

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Retrieves a registered tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        """Returns all registered tool definitions."""
        return list(self._tools.values())

    def to_openai_tools(self) -> List[Dict[str, Any]]:
        """Converts registered tools into OpenAI function calling schema specifications."""
        openai_tools: List[Dict[str, Any]] = []
        for tool in self._tools.values():
            schema = tool.input_schema.model_json_schema()
            # Clean title from schema if present
            schema.pop("title", None)

            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description.strip(),
                    "parameters": schema,
                },
            })
        return openai_tools

    def execute_tool(
        self,
        name: str,
        raw_arguments: Union[Dict[str, Any], str],
        db: Optional[Session] = None,
    ) -> ToolExecutionResult:
        """Executes a tool with strict Pydantic argument validation and timing.

        Ensures that:
        - Unknown tools fail cleanly.
        - Invalid arguments are caught with detailed validation errors.
        - SQL is never executed directly from raw arguments.
        - Output is JSON-sanitized (Decimals converted safely).
        """
        start_time = time.perf_counter()
        tool = self.get_tool(name)

        # 1. Unknown Tool Check
        if not tool:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"Tool '{name}' is not an approved analytics tool. Available tools: {list(self._tools.keys())}"
            logger.warning("Execution rejected: %s", error_msg)
            return ToolExecutionResult(
                tool_name=name,
                arguments=raw_arguments if isinstance(raw_arguments, dict) else {"raw": raw_arguments},
                success=False,
                error=error_msg,
                execution_time_ms=round(duration_ms, 2),
            )

        # 2. Argument Parsing (Handle string JSON if supplied)
        args_dict: Dict[str, Any]
        if isinstance(raw_arguments, str):
            try:
                args_dict = json.loads(raw_arguments) if raw_arguments.strip() else {}
            except json.JSONDecodeError as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                error_msg = f"Failed to parse tool arguments as valid JSON: {exc}"
                logger.warning("Tool argument JSON parse error for '%s': %s", name, exc)
                return ToolExecutionResult(
                    tool_name=name,
                    arguments={"raw": raw_arguments},
                    success=False,
                    error=error_msg,
                    execution_time_ms=round(duration_ms, 2),
                )
        else:
            args_dict = raw_arguments or {}

        # 3. Argument Validation using Pydantic
        try:
            validated_args = tool.input_schema.model_validate(args_dict)
        except ValidationError as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            error_details = []
            for err in exc.errors():
                loc = ".".join(str(l) for l in err.get("loc", []))
                error_details.append(f"{loc}: {err.get('msg')}")
            error_msg = f"Validation failed for tool '{name}': " + "; ".join(error_details)
            logger.warning("Tool argument validation failure: %s", error_msg)
            return ToolExecutionResult(
                tool_name=name,
                arguments=args_dict,
                success=False,
                error=error_msg,
                execution_time_ms=round(duration_ms, 2),
            )

        # 4. Enforce Database Requirement
        if tool.requires_db and db is None:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"Tool '{name}' requires an active database session."
            logger.error(error_msg)
            return ToolExecutionResult(
                tool_name=name,
                arguments=validated_args.model_dump(),
                success=False,
                error=error_msg,
                execution_time_ms=round(duration_ms, 2),
            )

        # 5. Execute Tool Function
        try:
            logger.info("Executing tool '%s' with args: %s", name, validated_args.model_dump())
            if tool.requires_db:
                raw_result = tool.func(validated_args, db=db)
            else:
                raw_result = tool.func(validated_args)

            sanitized_data = _sanitize_for_json(raw_result)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            return ToolExecutionResult(
                tool_name=name,
                arguments=validated_args.model_dump(),
                success=True,
                data=sanitized_data,
                execution_time_ms=round(duration_ms, 2),
                metadata={"source_service": tool.func.__module__},
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"Runtime error in tool '{name}': {exc}"
            logger.error("Error executing tool '%s': %s", name, exc, exc_info=True)
            return ToolExecutionResult(
                tool_name=name,
                arguments=validated_args.model_dump(),
                success=False,
                error=error_msg,
                execution_time_ms=round(duration_ms, 2),
            )


# Default global tool registry instance
default_tool_registry = ToolRegistry()
