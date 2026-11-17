# zotero-cli browser command reference

Generated from the CLI's own argument parser by
`scripts/gen_skill_reference.py` -- do not edit by hand.

`reference.md` in this skill directory covers the global options and every
other command.


## `browser`

### `browser serve`

 - `--port` -- default `23120`
 - `--token-file` -- default `~/.config/zotero-mcp/browser-bridge.token`

### `browser status`

 - `--port` -- default `23120`
 - `--token-file` -- default `~/.config/zotero-mcp/browser-bridge.token`

### `browser tabs`

 - `--port` -- default `23120`
 - `--token-file` -- default `~/.config/zotero-mcp/browser-bridge.token`
 - `--timeout` -- default `120`

### `browser targets`

 - `--port` -- default `23120`
 - `--token-file` -- default `~/.config/zotero-mcp/browser-bridge.token`
 - `--timeout` -- default `120`

### `browser open`

 - `--port` -- default `23120`
 - `--token-file` -- default `~/.config/zotero-mcp/browser-bridge.token`
 - `--timeout` -- default `120`
 - `--background` -- Open the URL in an inactive tab without focusing its window
 - `<url>` -- HTTP(S) publication URL to open in the paired browser

### `browser inspect`

 - `--port` -- default `23120`
 - `--token-file` -- default `~/.config/zotero-mcp/browser-bridge.token`
 - `--timeout` -- default `120`
 - `--tab-id` -- **required**

### `browser focus`

 - `--port` -- default `23120`
 - `--token-file` -- default `~/.config/zotero-mcp/browser-bridge.token`
 - `--timeout` -- default `120`
 - `--tab-id` -- **required**

### `browser save`

 - `--port` -- default `23120`
 - `--token-file` -- default `~/.config/zotero-mcp/browser-bridge.token`
 - `--timeout` -- default `120`
 - `--ready-timeout` -- default `30` -- Page/translator readiness budget in seconds (0.5–120; default 30), separate from batch interval and job timeout
 - `--destination` -- Move the new save session to this Connector L/C target, like the popup
 - `--background` -- Open the URL in an inactive tab without focusing its window
 - `--close-on-success` -- Close this request's background URL tab after confirmed save; preserve failures and user-touched tabs
 - `--tab-id` / `--url` -- mutually exclusive
 - `--target` -- Require this currently selected Connector target (L/C ID)
 - `--allow-no-pdf` -- Allow a metadata-only save

### `browser batch`

 - `--port` -- default `23120`
 - `--token-file` -- default `~/.config/zotero-mcp/browser-bridge.token`
 - `--timeout` -- default `120`
 - `<urls>` -- Distinct new-publication URLs, after caller duplicate checks
 - `--target` -- Require this initial selection; without destination, guard every save
 - `--interval` -- default `2.0` -- Seconds between papers (0.5–60; default 2)
 - `--ready-timeout` -- default `30` -- Page/translator readiness budget in seconds (0.5–120; default 30), separate from batch interval and job timeout
 - `--destination` -- Move the new save session to this Connector L/C target, like the popup

### `browser result`

 - `--port` -- default `23120`
 - `--token-file` -- default `~/.config/zotero-mcp/browser-bridge.token`
 - `--timeout` -- default `120`
 - `<job_id>`
