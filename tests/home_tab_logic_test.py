import pytest
from slack_sdk.models.blocks import ActionsBlock, HeaderBlock, SectionBlock
from slack_sdk.models.blocks.basic_components import MarkdownTextObject, PlainTextObject
from slack_sdk.models.blocks.block_elements import ButtonElement
from slack_sdk.models.views import View

from app.home_tab_logic import (
    build_home_tab_blocks,
    build_home_tab_view,
    build_no_auth_servers_section,
    build_oauth_servers_section,
    extract_cancel_server_index,
    extract_disable_server_index,
    extract_enable_server_index,
    extract_server_index_from_action_id,
    format_timestamp,
)
from app.mcp.oauth_control_service import OAUTH_URL_PROCESSING


@pytest.mark.parametrize(
    "expires_at_timestamp, user_tz, expected",
    [
        (1640995200, "UTC", "00:00:00"),  # 2022-01-01 00:00:00 UTC
        (1640995200, "America/New_York", "19:00:00"),  # 2021-12-31 19:00:00 EST
        (1640995200, "Asia/Tokyo", "09:00:00"),  # 2022-01-01 09:00:00 JST
        (1640995200, "invalid_timezone", "00:00:00"),  # fallback to UTC
        (-1, "UTC", "23:59:59"),  # 1969-12-31 23:59:59 UTC
        ("invalid", "UTC", ""),  # invalid timestamp type
    ],
)
def test_format_timestamp(expires_at_timestamp, user_tz, expected):
    result = format_timestamp(expires_at_timestamp, user_tz)

    assert result == expected


@pytest.mark.parametrize(
    "mcp_servers, expected_blocks",
    [
        (
            [],
            [
                HeaderBlock(
                    text=PlainTextObject(text="🌐 MCP Servers without Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="No servers configured.")),
            ],
        ),
        (
            [{"name": "TestServer", "url": "http://localhost:8000/mcp/"}],
            [
                HeaderBlock(
                    text=PlainTextObject(text="🌐 MCP Servers without Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="*TestServer*")),
            ],
        ),
        (
            [
                {"name": "Server1", "url": "http://localhost:8001/mcp/"},
                {"name": "Server2", "url": "http://localhost:8002/mcp/"},
            ],
            [
                HeaderBlock(
                    text=PlainTextObject(text="🌐 MCP Servers without Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="*Server1*")),
                SectionBlock(text=MarkdownTextObject(text="*Server2*")),
            ],
        ),
    ],
)
def test_build_no_auth_servers_section(mcp_servers, expected_blocks):
    result = build_no_auth_servers_section(mcp_servers)

    assert result == expected_blocks


@pytest.mark.parametrize(
    "server_data, user_tz, expected",
    [
        ([], "UTC", []),  # Empty server data
        (
            [
                {
                    "index": 0,
                    "server": {"name": "GitHubServer"},
                    "auth_url": None,
                    "oauth_verification_code": None,
                    "session_data": None,
                    "has_valid_session": False,
                    "has_cached_tools": False,
                }
            ],
            "UTC",
            [
                HeaderBlock(
                    text=PlainTextObject(text="🔒 MCP Servers with Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="GitHubServer")),
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="Enable"),
                            action_id="enable_mcp_oauth_0",
                            style="primary",
                        )
                    ]
                ),
            ],
        ),  # Header + Server block + Enable button
        (
            [
                {
                    "index": 0,
                    "server": {"name": "GitHubServer"},
                    "auth_url": OAUTH_URL_PROCESSING,
                    "oauth_verification_code": None,
                    "session_data": None,
                    "has_valid_session": False,
                    "has_cached_tools": False,
                }
            ],
            "UTC",
            [
                HeaderBlock(
                    text=PlainTextObject(text="🔒 MCP Servers with Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="GitHubServer")),
                SectionBlock(text=MarkdownTextObject(text="⏳ Please wait...")),
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="Cancel"),
                            action_id="cancel_mcp_oauth_0",
                        )
                    ]
                ),
            ],
        ),  # Header + Server block + Processing message
        (
            [
                {
                    "index": 0,
                    "server": {"name": "GitHubServer"},
                    "auth_url": "https://auth.example.com",
                    "oauth_verification_code": "e9f0a1b2",
                    "session_data": None,
                    "has_valid_session": False,
                    "has_cached_tools": False,
                }
            ],
            "UTC",
            [
                HeaderBlock(
                    text=PlainTextObject(text="🔒 MCP Servers with Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="GitHubServer")),
                SectionBlock(
                    text=MarkdownTextObject(
                        text="🔗 <https://auth.example.com|Click to authorize> / Code: `e9f0a1b2`"
                    )
                ),
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="Cancel"),
                            action_id="cancel_mcp_oauth_0",
                        )
                    ]
                ),
            ],
        ),  # Header + Server block + Auth URL with oauth_verification_code + Cancel button
        (
            [
                {
                    "index": 0,
                    "server": {"name": "GitHubServer"},
                    "auth_url": None,
                    "oauth_verification_code": None,
                    "session_data": {"expires_at": 1640995200},
                    "has_valid_session": True,
                    "has_cached_tools": True,
                }
            ],
            "UTC",
            [
                HeaderBlock(
                    text=PlainTextObject(text="🔒 MCP Servers with Authentication")
                ),
                SectionBlock(
                    text=MarkdownTextObject(text="*GitHubServer* (expires at 00:00:00)")
                ),
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="Disable"),
                            action_id="disable_mcp_oauth_0",
                        )
                    ]
                ),
            ],
        ),  # Header + Server block with expires_at + Disable button
        (
            [
                {
                    "index": 0,
                    "server": {"name": "GitHubServer"},
                    "auth_url": None,
                    "oauth_verification_code": None,
                    "session_data": {"expires_at": None},
                    "has_valid_session": True,
                    "has_cached_tools": True,
                }
            ],
            "UTC",
            [
                HeaderBlock(
                    text=PlainTextObject(text="🔒 MCP Servers with Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="*GitHubServer*")),
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="Disable"),
                            action_id="disable_mcp_oauth_0",
                        )
                    ]
                ),
            ],
        ),  # Header + Server block without expires_at + Disable button
        (
            [
                {
                    "index": 0,
                    "server": {"name": "GitHubServer"},
                    "auth_url": None,
                    "oauth_verification_code": None,
                    "session_data": None,
                    "has_valid_session": True,
                    "has_cached_tools": False,
                }
            ],
            "UTC",
            [
                HeaderBlock(
                    text=PlainTextObject(text="🔒 MCP Servers with Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="GitHubServer")),
                SectionBlock(text=MarkdownTextObject(text="⏳ Fetching tools...")),
            ],
        ),  # Header + Server block + Fetching tools message
    ],
)
def test_build_oauth_servers_section(server_data, user_tz, expected):
    result = build_oauth_servers_section(server_data, user_tz)

    assert result == expected


@pytest.mark.parametrize(
    "mcp_servers, expected_blocks",
    [
        (
            [],
            [
                HeaderBlock(
                    text=PlainTextObject(text="🌐 MCP Servers without Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="No servers configured.")),
            ],
        ),
        (
            [{"name": "TestServer", "url": "http://localhost:8000/mcp/"}],
            [
                HeaderBlock(
                    text=PlainTextObject(text="🌐 MCP Servers without Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="*TestServer*")),
            ],
        ),
        (
            [
                {"name": "Server1", "url": "http://localhost:8001/mcp/"},
                {"name": "Server2", "url": "http://localhost:8002/mcp/"},
            ],
            [
                HeaderBlock(
                    text=PlainTextObject(text="🌐 MCP Servers without Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="*Server1*")),
                SectionBlock(text=MarkdownTextObject(text="*Server2*")),
            ],
        ),
    ],
)
def test_build_home_tab_blocks(mcp_servers, expected_blocks):
    config_servers = []
    for server in mcp_servers:
        config_servers.append(
            {"name": server["name"], "url": server["url"], "auth_type": "none"}
        )

    result = build_home_tab_blocks(
        mcp_config={"servers": config_servers},
        user_oauth_urls={},
        user_oauth_verification_codes={},
        user_oauth_sessions={},
        user_oauth_tools={},
        user_tz="UTC",
    )
    assert result == expected_blocks


@pytest.mark.parametrize(
    "mcp_config, user_oauth_urls, user_oauth_verification_codes, user_oauth_sessions, user_oauth_tools, expected",
    [
        (
            {
                "servers": [
                    {
                        "name": "GitHubServer",
                        "url": "http://test",
                        "auth_type": "user_federation",
                        "agentcore_provider": "github",
                    }
                ]
            },
            {},
            {},
            {},
            {},
            [
                HeaderBlock(
                    text=PlainTextObject(text="🌐 MCP Servers without Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="No servers configured.")),
                HeaderBlock(
                    text=PlainTextObject(text="🔒 MCP Servers with Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="GitHubServer")),
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="Enable"),
                            action_id="enable_mcp_oauth_0",
                            style="primary",
                        )
                    ]
                ),
            ],
        ),  # OAuth server without auth
        (
            {
                "servers": [
                    {
                        "name": "GitHubServer",
                        "url": "http://test",
                        "auth_type": "user_federation",
                        "agentcore_provider": "github",
                    }
                ]
            },
            {"GitHubServer": "https://auth.example.com"},
            {"GitHubServer": "e9f0a1b2"},
            {},
            {},
            [
                HeaderBlock(
                    text=PlainTextObject(text="🌐 MCP Servers without Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="No servers configured.")),
                HeaderBlock(
                    text=PlainTextObject(text="🔒 MCP Servers with Authentication")
                ),
                SectionBlock(text=MarkdownTextObject(text="GitHubServer")),
                SectionBlock(
                    text=MarkdownTextObject(
                        text="🔗 <https://auth.example.com|Click to authorize> / Code: `e9f0a1b2`"
                    )
                ),
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="Cancel"),
                            action_id="cancel_mcp_oauth_0",
                        )
                    ]
                ),
            ],
        ),  # OAuth server with pending auth URL and oauth_verification_code
    ],
)
def test_build_home_tab_blocks_with_oauth(
    mcp_config,
    user_oauth_urls,
    user_oauth_verification_codes,
    user_oauth_sessions,
    user_oauth_tools,
    expected,
):
    result = build_home_tab_blocks(
        mcp_config=mcp_config,
        user_oauth_urls=user_oauth_urls,
        user_oauth_verification_codes=user_oauth_verification_codes,
        user_oauth_sessions=user_oauth_sessions,
        user_oauth_tools=user_oauth_tools,
        user_tz="UTC",
    )

    assert result == expected


@pytest.mark.parametrize(
    "mcp_config, user_oauth_urls, user_oauth_verification_codes, user_oauth_sessions, user_oauth_tools, expected",
    [
        (
            {"servers": []},
            {},
            {},
            {},
            {},
            View(
                type="home",
                blocks=build_home_tab_blocks({"servers": []}, {}, {}, {}, {}, "UTC"),
            ),
        ),
        (
            {
                "servers": [
                    {"name": "TestServer", "url": "http://test", "auth_type": "none"}
                ]
            },
            {},
            {},
            {},
            {},
            View(
                type="home",
                blocks=build_home_tab_blocks(
                    {
                        "servers": [
                            {
                                "name": "TestServer",
                                "url": "http://test",
                                "auth_type": "none",
                            }
                        ]
                    },
                    {},
                    {},
                    {},
                    {},
                    "UTC",
                ),
            ),
        ),
    ],
)
def test_build_home_tab_view(
    mcp_config,
    user_oauth_urls,
    user_oauth_verification_codes,
    user_oauth_sessions,
    user_oauth_tools,
    expected,
):
    result = build_home_tab_view(
        mcp_config=mcp_config,
        user_oauth_urls=user_oauth_urls,
        user_oauth_verification_codes=user_oauth_verification_codes,
        user_oauth_sessions=user_oauth_sessions,
        user_oauth_tools=user_oauth_tools,
        user_tz="UTC",
    )

    assert result == expected


# Action extraction function tests
@pytest.mark.parametrize(
    "action_id, action_prefix, expected",
    [
        ("enable_mcp_oauth_0", "enable_mcp_oauth_", 0),
        ("disable_mcp_oauth_2", "disable_mcp_oauth_", 2),
        ("enable_mcp_oauth_123", "enable_mcp_oauth_", 123),
    ],
)
def test_extract_server_index_from_action_id(action_id, action_prefix, expected):
    result = extract_server_index_from_action_id(action_id, action_prefix)
    assert result == expected


@pytest.mark.parametrize(
    "action_id, expected",
    [
        ("enable_mcp_oauth_0", 0),
        ("enable_mcp_oauth_3", 3),
    ],
)
def test_extract_enable_server_index(action_id, expected):
    result = extract_enable_server_index(action_id)
    assert result == expected


@pytest.mark.parametrize(
    "action_id, expected",
    [
        ("disable_mcp_oauth_1", 1),
        ("disable_mcp_oauth_5", 5),
    ],
)
def test_extract_disable_server_index(action_id, expected):
    result = extract_disable_server_index(action_id)
    assert result == expected


@pytest.mark.parametrize(
    "action_id, expected",
    [
        ("cancel_mcp_oauth_0", 0),
        ("cancel_mcp_oauth_2", 2),
        ("cancel_mcp_oauth_10", 10),
    ],
)
def test_extract_cancel_server_index(action_id, expected):
    result = extract_cancel_server_index(action_id)
    assert result == expected


def test_build_home_tab_blocks_with_error_message():
    mcp_config = {}
    user_oauth_urls = {}
    user_oauth_verification_codes = {}
    user_oauth_sessions = {}
    user_oauth_tools = {}
    user_tz = "UTC"
    error_message = "Test error message"

    result = build_home_tab_blocks(
        mcp_config,
        user_oauth_urls,
        user_oauth_verification_codes,
        user_oauth_sessions,
        user_oauth_tools,
        user_tz,
        error_message,
    )

    expected = [
        SectionBlock(
            text=MarkdownTextObject(text=":warning: *Error:* Test error message")
        )
    ]

    assert result == expected


def test_build_home_tab_view_with_error_message():
    mcp_config = {}
    user_oauth_urls = {}
    user_oauth_verification_codes = {}
    user_oauth_sessions = {}
    user_oauth_tools = {}
    user_tz = "UTC"
    error_message = "Test error message"

    result = build_home_tab_view(
        mcp_config,
        user_oauth_urls,
        user_oauth_verification_codes,
        user_oauth_sessions,
        user_oauth_tools,
        user_tz,
        error_message,
    )

    expected = View(
        type="home",
        blocks=[
            SectionBlock(
                text=MarkdownTextObject(text=":warning: *Error:* Test error message")
            )
        ],
    )

    assert result == expected
