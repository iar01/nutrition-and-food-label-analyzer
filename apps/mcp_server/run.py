import argparse
import sys

from labellens.config import settings
from labellens.mcp_server.app import mcp


def main() -> None:
    ap = argparse.ArgumentParser(description="LabelLens MCP server")
    ap.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-auth", action="store_true", help="local development only")
    args = ap.parse_args()

    if args.transport == "stdio":
        mcp.run()
        return

    # HTTP: needs the auth wrapper from Lesson 7
    from labellens.mcp_server.http import (
        build_http_app,  # imported here so stdio never needs uvicorn
    )

    token = settings.mcp_auth_token
    if not token and not args.no_auth:
        sys.exit("Set MCP_AUTH_TOKEN in .env, or pass --no-auth for local development.")
    if args.no_auth and args.host not in ("127.0.0.1", "localhost"):
        sys.exit("--no-auth is only allowed on localhost.")

    import uvicorn

    uvicorn.run(
        build_http_app(mcp, None if args.no_auth else token), host=args.host, port=args.port
    )


if __name__ == "__main__":
    main()
