# Ubuntu MCP Server

Secure Ubuntu command execution, file access, and system information for Codex and other MCP clients over stdio. Requires Linux, Python 3.10+, and [uv](https://docs.astral.sh/uv/getting-started/installation/).

## Connect to Codex

From the repository:

```bash
cd /absolute/path/to/codex-mcp-for-ubuntu
uv venv .venv --managed-python -p 3.12
uv sync
uv run ubuntu-mcp-server --help
codex mcp add ubuntu -- uv --directory "$PWD" run --frozen ubuntu-mcp-server
codex mcp list
```

Start a new Codex session and use `/mcp` to verify the connection. For a standalone command:

```bash
uv tool install .
codex mcp add ubuntu -- ubuntu-mcp-server
```

If Codex cannot find `uv`, use its absolute path from `command -v uv`. You can also add this to `~/.codex/config.toml`:

```toml
[mcp_servers.ubuntu]
command = "/home/you/.local/bin/uv"
args = ["--directory", "/absolute/path/to/codex-mcp-for-ubuntu", "run", "--frozen", "ubuntu-mcp-server"]
startup_timeout_sec = 30
tool_timeout_sec = 60
```

See the [Codex MCP documentation](https://developers.openai.com/codex/mcp/) for client configuration.

## Sudo

Sudo is disabled by default. Enable it only for explicitly approved absolute executable paths:

```bash
codex mcp remove ubuntu
codex mcp add ubuntu -- uv --directory "$PWD" run --frozen ubuntu-mcp-server \
  --allow-sudo --sudo-command /usr/bin/whoami
```

The server uses non-interactive `sudo -n` and never accepts a password. The OS account must have a matching narrow `NOPASSWD` sudoers rule. Do not approve shells, interpreters, editors, or package managers unless you intend to grant broad root access.

## Available tools

- `execute_command` — run one executable under the selected policy
- `list_directory`, `read_file`, `write_file` — inspect and modify permitted paths
- `get_system_info` — report OS, user, and resource information
- `install_package` — legacy name; checks installed packages only
- `search_packages` — search apt packages

Commands run without shell expansion, pipes, or redirection. The default `secure` policy is restrictive; `dev` is broader but still requires explicit sudo opt-in. These are application policies, not an OS sandbox.

## Development

```bash
uv venv .venv --managed-python -p 3.12
uv sync
uv run python -m unittest discover -s tests -v
uv build
```

`pyproject.toml` is the source of package metadata and dependencies; `uv.lock` pins the environment. `requirements.txt` is deprecated and retained only for compatibility. The legacy `setup.py` and `install.py` helpers are not recommended for new installations.

Implementation lives in `ubuntu_mcp_server/`; `main.py` remains a compatibility entry point.
