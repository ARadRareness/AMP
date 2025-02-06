from fastmcp_http import FastMCPHttpClient
from mcp.types import TextContent


def ask_for_permission(description: str) -> bool:
    # Request permission
    client = FastMCPHttpClient()
    permission = client.call_tool(
        "ask_for_permission",
        {
            "description": description,
        },
    )

    if not isinstance(permission[0], TextContent):
        # logger.error(f"Permission response is not a TextContent: {permission[0]}")
        return False

    text_content: TextContent = permission[0]
    print(text_content.text)

    return text_content.text == "true"
