# Terminal Agent Design

## Goal

Build a general command-line agent that starts with `JW` or `jw`, connects to an OpenAI-compatible large model, and can operate approved tools through a terminal conversation.

## Scope

The first version is a lightweight REPL and tool runner. It keeps the existing `scripts/cinema.py` CLI intact and adds a natural-language layer around reusable tools. It supports OpenAI-compatible providers first, while keeping a provider boundary for future Ollama support.

## Startup

Users can start the agent with either command:

```bash
JW
jw
```

The installer creates both executables in `~/.local/bin`. A development fallback remains available:

```bash
python3 scripts/agent.py
```

## Architecture

- `scripts/agent.py`: terminal REPL entry point.
- `scripts/agent_core.py`: conversation loop, slash command dispatch, model/tool orchestration.
- `scripts/agent_config.py`: config loading, environment overrides, safe config summary, Quark cookie updates.
- `scripts/llm.py`: provider abstraction and OpenAI-compatible chat completions client.
- `scripts/tools/registry.py`: tool registry, schemas, risk levels, and confirmation policy.
- `scripts/tools/cinema_tools.py`: wrappers around existing cinema commands.
- `scripts/tools/quark_tools.py`: Quark status and cookie login helper.
- `scripts/tools/shell_tools.py`: confirmed shell execution with dangerous command blocking.
- `scripts/install_agent_command.py`: installs `JW` and `jw` launchers.

## Permissions

Tools have risk levels:

- `read`: no confirmation required.
- `write`: confirmation required because the tool changes local or remote state.
- `shell`: confirmation required and only valid for explicit shell requests.
- `secret`: never echoes sensitive values.

Shell execution is not automatic. The agent proposes a command, shows it, and waits for confirmation.

## Model Configuration

`config.json` may contain:

```json
{
  "agent": {
    "provider": "openai_compatible",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4.1-mini",
    "api_key_env": "OPENAI_API_KEY",
    "allow_shell": "confirm",
    "history_limit": 20
  }
}
```

Environment variables override config:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

The API key is read from the environment and not written to `config.json`.

## Quark Login

The current project uses cookie-based Quark authentication. `/login quark` prompts for a Cookie through hidden terminal input, stores it in `config.json`, and reports only a masked status.

## Local Mode

If the model is not configured, slash commands still work. Natural-language requests explain that model configuration is required.

## Testing

Use standard-library `unittest` tests so the project does not need a test dependency. Tests cover config loading, tool registry policy, shell safety, Quark cookie storage, and launcher installation.
