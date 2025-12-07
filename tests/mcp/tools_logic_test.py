"""
Tests for MCP tools logic module.
"""

import pytest

from app.mcp.oauth_tools_logic import parse_mcp_tool_name
from app.mcp.tools_logic import build_mcp_tool_name, transform_mcp_spec_to_classic_tool
from app.tools_logic import is_mcp_tool_name


@pytest.mark.parametrize(
    "spec_name, auth_type, server_index, model, expected",
    [
        ("tool1", "none", 0, "gemini/gemini-pro", "n.0.tool1"),
        ("tool2", "user_federation", 1, "gemini/gemini-pro", "u.1.tool2"),
        ("tool3", "unknown", 2, "gemini/gemini-pro", "unknown.2.tool3"),
        ("tool1", "none", 0, "gpt-4", "n-0-tool1"),
        ("tool2", "user_federation", 1, "gpt-4", "u-1-tool2"),
        ("tool3", "unknown", 2, "gpt-4", "unknown-2-tool3"),
    ],
)
def test_build_mcp_tool_name(spec_name, auth_type, server_index, model, expected):
    result = build_mcp_tool_name(spec_name, auth_type, server_index, model)

    assert result == expected


@pytest.mark.parametrize(
    "tool_name, expected",
    [
        # Gemini format (dot-separated)
        ("n.0.tool1", ("tool1", "none", 0)),
        ("u.1.tool2", ("tool2", "user_federation", 1)),
        ("u.2.my-complex-tool", ("my-complex-tool", "user_federation", 2)),
        # GPT format (hyphen-separated)
        ("n-0-tool1", ("tool1", "none", 0)),
        ("u-1-tool2", ("tool2", "user_federation", 1)),
        ("u-2-my-complex-tool", ("my-complex-tool", "user_federation", 2)),
    ],
)
def test_parse_mcp_tool_name(tool_name, expected):
    result = parse_mcp_tool_name(tool_name)

    assert result == expected


@pytest.mark.parametrize(
    "tool_name",
    [
        "tool1",
        "tool1.n",
        "tool1-n",
        "x.0.tool1",
        "x-0-tool1",
        "n.abc.tool1",
        "n-abc-tool1",
    ],
)
def test_parse_mcp_tool_name_errors(tool_name):
    result = parse_mcp_tool_name(tool_name)
    assert result == ("", "", -1)


@pytest.mark.parametrize(
    "name, expected",
    [
        ("n.0.tool1", True),
        ("u.1.tool2", True),
        ("n-0-tool1", True),
        ("u-1-tool2", True),
        ("tool3", False),
        ("", False),
    ],
)
def test_is_mcp_tool_name(name, expected):
    result = is_mcp_tool_name(name)

    assert result == expected


@pytest.mark.parametrize(
    "mcp_spec, auth_type, server_index, model, expected",
    [
        (
            {
                "name": "test_tool",
                "description": "Test tool",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"param": {"type": "string"}},
                    }
                },
            },
            "none",
            0,
            "gpt-4",
            {
                "type": "function",
                "function": {
                    "name": "n-0-test_tool",
                    "description": "Test tool",
                    "parameters": {
                        "type": "object",
                        "properties": {"param": {"type": "string"}},
                    },
                },
            },
        ),
        (
            {
                "name": "test_tool",
                "description": "Test tool",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "param": {"type": "string", "format": "invalid"}
                        },
                    }
                },
            },
            "none",
            0,
            "gemini/gemini-pro",
            {
                "type": "function",
                "function": {
                    "name": "n.0.test_tool",
                    "description": "Test tool",
                    "parameters": {
                        "type": "object",
                        "properties": {"param": {"type": "string"}},
                    },
                },
            },
        ),
        (
            {
                "name": "test_tool",
                "description": "Test tool",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "param": {"type": "string", "format": "date-time"}
                        },
                    }
                },
            },
            "none",
            0,
            "gemini/gemini-pro",
            {
                "type": "function",
                "function": {
                    "name": "n.0.test_tool",
                    "description": "Test tool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "param": {"type": "string", "format": "date-time"}
                        },
                    },
                },
            },
        ),
        (
            {
                "name": "test_tool",
                "description": "Test tool without type",
                "inputSchema": {"json": {"properties": {"param": {"type": "string"}}}},
            },
            "none",
            0,
            "gpt-4",
            {
                "type": "function",
                "function": {
                    "name": "n-0-test_tool",
                    "description": "Test tool without type",
                    "parameters": {
                        "type": "object",
                        "properties": {"param": {"type": "string"}},
                    },
                },
            },
        ),
        (
            {
                "name": "test_tool",
                "description": "Test tool without properties",
                "inputSchema": {"json": {"type": "object"}},
            },
            "none",
            0,
            "gpt-4",
            {
                "type": "function",
                "function": {
                    "name": "n-0-test_tool",
                    "description": "Test tool without properties",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ),
    ],
)
def test_transform_mcp_spec_to_classic_tool(
    mcp_spec, auth_type, server_index, model, expected
):
    result = transform_mcp_spec_to_classic_tool(
        mcp_spec=mcp_spec,
        auth_type=auth_type,
        server_index=server_index,
        model=model,
    )

    assert result == expected
