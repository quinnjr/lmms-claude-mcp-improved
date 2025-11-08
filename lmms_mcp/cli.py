"""
Command-line interface for LMMS-Claude-MCP.
"""

import sys
import argparse
import logging
import asyncio

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the CLI."""
    import sys

    # Handle case where command might be passed as first arg (e.g., from uvx)
    # Filter out 'lmms-mcp' if it appears as an argument, and handle empty args
    filtered_args = [arg for arg in sys.argv[1:] if arg != 'lmms-mcp' and arg not in ['server', 'remote']]

    # If no valid command found, check if we have any args at all
    has_command = any(arg in ['server', 'remote'] for arg in sys.argv[1:])

    # If no command specified and we're being called as MCP server (no args or just 'lmms-mcp'),
    # default to server mode with stdio
    if not has_command and (len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == 'lmms-mcp')):
        # Run as MCP server with stdio transport (for Claude Desktop)
        from .server import MCPServer
        server = MCPServer()
        asyncio.run(server.start(use_stdio=True))
        return

    parser = argparse.ArgumentParser(description="LMMS-Claude-MCP: LMMS integration with Claude AI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run", required=False)

    # Server command
    server_parser = subparsers.add_parser("server", help="Run the MCP server")
    server_parser.add_argument("--host", default="127.0.0.1", help="Server host")
    server_parser.add_argument("--port", type=int, default=8000, help="Server port")
    server_parser.add_argument("--lmms-host", default="127.0.0.1", help="LMMS host")
    server_parser.add_argument("--lmms-port", type=int, default=9000, help="LMMS port")

    # Remote command
    remote_parser = subparsers.add_parser("remote", help="Run the LMMS remote script")
    remote_parser.add_argument("--listening-host", default="127.0.0.1", help="Listening host")
    remote_parser.add_argument("--listening-port", type=int, default=9000, help="Listening port")
    remote_parser.add_argument("--client-host", default="127.0.0.1", help="Client host")
    remote_parser.add_argument("--client-port", type=int, default=9001, help="Client port")

    # Parse arguments
    args = parser.parse_args()

    # Default to server if no command is provided
    if not args.command:
        # Re-parse with server as the command to get server-specific arguments
        server_args = server_parser.parse_args([])
        # Create a new namespace that includes both command and server args
        class CombinedArgs:
            def __init__(self):
                self.command = "server"
                for attr in dir(server_args):
                    if not attr.startswith('_'):
                        setattr(self, attr, getattr(server_args, attr))
        args = CombinedArgs()

    try:
        if args.command == "server":
            from .server import MCPServer
            # Get server arguments (they should always exist now)
            host = getattr(args, 'host', '127.0.0.1')
            port = getattr(args, 'port', 8000)
            lmms_host = getattr(args, 'lmms_host', '127.0.0.1')
            lmms_port = getattr(args, 'lmms_port', 9000)
            server = MCPServer(host, port, lmms_host, lmms_port)
            # Use stdio transport for MCP (required by Claude Desktop)
            asyncio.run(server.start(use_stdio=True))
        elif args.command == "remote":
            from .lmms_remote import LMMSRemoteScript, main as remote_main
            remote = LMMSRemoteScript(args.listening_host, args.listening_port,
                                      args.client_host, args.client_port)
            remote_main()
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()