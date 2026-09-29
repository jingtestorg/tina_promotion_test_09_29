"""MCP tool indirection layer.

This module is the owned abstraction over sap_cloud_sdk.agentgateway MCP tool loading.
Import from here (never from sap_cloud_sdk.agentgateway directly) so that tests can
monkey-patch `get_mcp_tools` without touching the SDK.

In production: returns tools from the Agent Gateway.
In tests (IBD_TESTING=1): conftest.py replaces this with mock tools from mcp-mock.json.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from langchain_core.tools import BaseTool, StructuredTool

logger = logging.getLogger(__name__)

_IBD_TESTING = os.environ.get("IBD_TESTING") == "1"


async def get_mcp_tools() -> list[BaseTool]:
    """Load MCP tools.

    - In production: fetches tools from the SAP Agent Gateway.
    - In test (IBD_TESTING=1): loads mock tools from mcp-mock.json if it exists,
      otherwise returns an empty list.
    """
    if _IBD_TESTING:
        return _load_mock_tools()

    try:
        # In production, delegate to the agw module's get_mcp_tools which handles
        # the full Agent Gateway tool loading, conversion, and retry logic.
        from mcp_providers.agw import get_mcp_tools as agw_get_mcp_tools  # type: ignore[import]
        tools = await agw_get_mcp_tools()
        logger.info("Loaded %d MCP tools from Agent Gateway.", len(tools))
        return tools  # type: ignore[return-value]
    except Exception as exc:
        logger.warning("Failed to load MCP tools from Agent Gateway: %s", exc)
        return []


def _load_mock_tools() -> list[BaseTool]:
    """Build StructuredTool instances from mcp-mock.json for offline testing."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    if not mock_path.exists():
        logger.debug("mcp-mock.json not found at %s; returning no mock tools.", mock_path)
        return []

    try:
        config = json.loads(mock_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read mcp-mock.json: %s", exc)
        return []

    tools: list[BaseTool] = []
    for tool_cfg in config.get("tools", []):
        name = tool_cfg.get("name", "unknown_tool")
        description = tool_cfg.get("description", "")
        mock_response = tool_cfg.get("mock_response", {})

        def _make_fn(response: object):
            def _fn(**kwargs):  # noqa: ANN001,ANN202
                return json.dumps(response) if not isinstance(response, str) else response
            return _fn

        tools.append(
            StructuredTool.from_function(
                func=_make_fn(mock_response),
                name=name,
                description=description,
            )
        )

    logger.debug("Loaded %d mock MCP tools from mcp-mock.json.", len(tools))
    return tools
