---
name: shadowbot-cli
description: Use the locally installed ShadowBot/Yingdao RPA shell CLI to inspect and operate apps/projects, Studio, Console tasks, account state, settings, runtime mode, and UI. Use for ShadowBot/Yingdao project discovery, app IDs, task execution/logs, Studio state, settings, or UI control.
---

# ShadowBot CLI

Use the installed ShadowBot agent-oriented CLI for ShadowBot-specific app lifecycle and runtime operations instead of guessing internal APIs or manually automating the ShadowBot UI.

This CLI is a **supplementary tool, not the default way to inspect or develop a project**. For source files, configuration tracing, code search, temporary scripts, and ordinary command execution, use Windows DevSpace first. Do not use CLI flow/block inspection as a substitute for reading the actual project when the source can answer the question directly.

## Executable

Prefer the stable launcher path:

`C:\Program Files\ShadowBot\shadowbot.shell-cli.exe`

Do not pin commands to versioned directories such as `shadowbot-6.x.x`; ShadowBot updates can change those folders.

## Core workflow

1. Check availability first:
   `"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" system health`
2. Inspect runtime state when mode/UI/task state matters:
   `":\Program Files\ShadowBot\shadowbot.shell-cli.exe" system state`
3. Inspect the current account when authentication matters:
   `"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" auth current`
4. The CLI is self-documenting for LLM agents. Before any unfamiliar or parameterized action, run:
   `":\Program Files\ShadowBot\shadowbot.shell-cli.exe" <command> -h`
   Do not guess flags, IDs, accepted values, or workflow ordering.

## Find ShadowBot apps/projects

For user-developed apps:

`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" console app --app-type developed --search "<keyword>"`

For subscribed apps, use `--app-type subscribed`.

Use the returned `appId` as the canonical app identifier. To inspect one app and its runtime input parameters:

`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" console app detail --app-id <UUID> --app-type developed`

When the user asks which ShadowBot project contains a feature, webhook, task, or automation, search app names first with `console app`. If source-level inspection is then required, use the discovered app identity to locate the corresponding local ShadowBot project rather than guessing from directory order.

## Run and inspect tasks

Before running, discover the app and inspect its detail when inputs may be required.

Starting an app or task is a real business execution, not a read-only inspection technique. Do not start a workflow merely to discover runtime variables, configuration values, Sheet names, credentials, account lists, or other data that can be obtained by static source analysis or a direct minimal API request. Execute only when the user has explicitly requested it or the task has reached an agreed run/test stage.

Help:
`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" console task run -h`

Typical default-parameter run:
`":\Program Files\ShadowBot\shadowbot.shell-cli.exe" console task run --app-id <UUID> --app-type developed`

The default task run is synchronous and streams logs. Use `--async` only when the user explicitly wants immediate return or the workflow specifically requires it.

Useful task commands:
- `console task status`
- `console task history`
- `console task logs`
- `console task stop`

Run `-h` on the exact subcommand before supplying parameters.

## Studio operations

Useful commands:
- `studio current get`
- `studio current save`
- `studio current sync`
- `studio current update-info`
- `studio create`
- `studio open`

`studio create` creates a PC automation app and sync-closes it. `studio open` creates a PC automation app and keeps Studio open. Do not assume either command opens an existing app; inspect help and current CLI capabilities instead.

## Runtime modes

The CLI supports `console` and `assistant` mode switching:

`":\Program Files\ShadowBot\shadowbot.shell-cli.exe" mode switch --to console`
`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" mode switch --to assistant`

Console-only operations can return `not_supported` in Assistant mode. Check `system state` before switching. Do not use `--force` to switch to Console while a task is running unless the user explicitly wants that interruption/risk.

## Settings and UI

Configuration workflow:
1. `config list`
2. `config describe --key <key>`
3. `config get --key <key>`
4. `config set --key <key> --value <value>`

Some settings require a ShadowBot restart. Verify after changes.

UI actions are exposed through:
`ui --exec <action>`

Run `ui -h` before use. Supported actions include Studio/Console minimize/maximize and switching to schedule/assistant/console.

## Safety and modification rules

- Read/query operations are safe defaults.
- Prefer Windows DevSpace for source inspection, file operations, project-local Python / PowerShell commands, and temporary diagnostic or migration scripts. Escalate to this CLI only when a ShadowBot-specific capability is actually needed.
- Treat `console app recycle`, permanent delete, publish, collaborator changes, `config set`, task stop, forced mode switches, and similar state-changing operations as explicit user-intent actions.
- Treat all app/task execution commands as real execution with possible business side effects even when the goal is only to inspect variables. Do not execute workflows for discovery.
- Never invent an app UUID or silently pick the first search result when multiple apps match. Use names and returned metadata to disambiguate.
- Prefer CLI outputs as the source of truth for current ShadowBot app IDs, task state, account state, and supported command parameters.
- If a command fails because the local REST API is unavailable, verify `system health`, ShadowBot process/runtime state, and authentication before attempting alternate methods.
