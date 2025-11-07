"""
Tests for the MCP configuration logic module.
"""

import pytest

from app.mcp.config_logic import (
    get_no_auth_servers_from_config,
    get_oauth_server_from_config,
    get_oauth_server_index_from_config,
    get_oauth_servers_from_config,
    normalize_mcp_config,
)


@pytest.mark.parametrize(
    "config_data, expected",
    [
        # Valid config without auth_session_duration_minutes - should add default
        (
            {
                "servers": [
                    {
                        "name": "Test Server",
                        "url": "https://test.example.com",
                        "auth_type": "none",
                    }
                ]
            },
            {
                "servers": [
                    {
                        "name": "Test Server",
                        "url": "https://test.example.com",
                        "auth_type": "none",
                    }
                ],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
                "agentcore_region": "us-west-2",
                "oauth_callback_url": "",
            },
        ),
        # Valid config with auth_session_duration_minutes
        (
            {
                "servers": [
                    {
                        "name": "Test Server",
                        "url": "https://test.example.com",
                        "auth_type": "none",
                    }
                ],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
            },
            {
                "servers": [
                    {
                        "name": "Test Server",
                        "url": "https://test.example.com",
                        "auth_type": "none",
                    }
                ],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
                "agentcore_region": "us-west-2",
                "oauth_callback_url": "",
            },
        ),
        # Empty dict - should return empty with default
        (
            {},
            {
                "servers": [],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
                "agentcore_region": "us-west-2",
                "oauth_callback_url": "",
            },
        ),
        # Invalid dict without servers key - should return empty with default
        (
            {"other_key": "value"},
            {
                "servers": [],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
                "agentcore_region": "us-west-2",
                "oauth_callback_url": "",
            },
        ),
        # None input - should return empty with default
        (
            None,
            {
                "servers": [],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
                "agentcore_region": "us-west-2",
                "oauth_callback_url": "",
            },
        ),
    ],
)
def test_normalize_mcp_config(config_data, expected):
    result = normalize_mcp_config(config_data)
    assert result == expected


@pytest.mark.parametrize(
    "config, expected",
    [
        # Multiple servers with mixed auth types
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "none",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "oauth",
                    },
                    {
                        "name": "Server 3",
                        "url": "https://server3.example.com",
                        "auth_type": "none",
                    },
                ]
            },
            [
                {"name": "Server 1", "url": "https://server1.example.com"},
                {"name": "Server 3", "url": "https://server3.example.com"},
            ],
        ),
        # Empty servers list
        ({"servers": []}, []),
        # No servers key
        ({}, []),
    ],
)
def test_get_no_auth_servers(config, expected):
    result = get_no_auth_servers_from_config(config)
    assert result == expected


@pytest.mark.parametrize(
    "config, expected",
    [
        # Multiple servers with mixed auth types
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "none",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "oauth",
                    },
                    {
                        "name": "Server 3",
                        "url": "https://server3.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            [
                {
                    "name": "Server 2",
                    "url": "https://server2.example.com",
                    "auth_type": "oauth",
                },
                {
                    "name": "Server 3",
                    "url": "https://server3.example.com",
                    "auth_type": "user_federation",
                },
            ],
        ),
        # Server without auth_type (falsy value)
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "",
                    },
                ]
            },
            [],
        ),
        # Empty servers list
        ({"servers": []}, []),
        # No servers key
        ({}, []),
    ],
)
def test_get_oauth_servers_from_config(config, expected):
    result = get_oauth_servers_from_config(config)
    assert result == expected


@pytest.mark.parametrize(
    "config, server_index, expected",
    [
        # Valid index
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "oauth",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            1,
            {
                "name": "Server 2",
                "url": "https://server2.example.com",
                "auth_type": "user_federation",
            },
        ),
        # Index 0
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "oauth",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            0,
            {
                "name": "Server 1",
                "url": "https://server1.example.com",
                "auth_type": "oauth",
            },
        ),
        # Negative index
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "oauth",
                    },
                ]
            },
            -1,
            {},
        ),
        # Index out of range
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "oauth",
                    },
                ]
            },
            2,
            {},
        ),
        # Empty config
        ({}, 0, {}),
        # No servers in config
        ({"servers": []}, 0, {}),
    ],
)
def test_get_oauth_server_from_config(config, server_index, expected):
    result = get_oauth_server_from_config(config, server_index)
    assert result == expected


@pytest.mark.parametrize(
    "config, server_name, expected",
    [
        # Server found at index 0
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "oauth",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            "Server 1",
            0,
        ),
        # Server found at index 1
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "oauth",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            "Server 2",
            1,
        ),
        # Server not found
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "oauth",
                    },
                ]
            },
            "Server 2",
            None,
        ),
        # Empty servers list
        ({"servers": []}, "Server 1", None),
        # No servers key
        ({}, "Server 1", None),
        # Server with none auth_type (should not be in oauth servers)
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "none",
                    },
                ]
            },
            "Server 1",
            None,
        ),
    ],
)
def test_get_oauth_server_index_from_config(config, server_name, expected):
    result = get_oauth_server_index_from_config(config, server_name)
    assert result == expected
