# Registering papers and acquiring PDFs

This guide covers adding papers to a Zotero library with `zotero-cli` and obtaining their PDFs, including saves through a paired browser Connector.
It explains how to choose a path, save through the browser without duplicate writes, limit retries, and verify and report the outcome.
The [browser command reference](browser-reference.md), generated from the CLI parser, lists every `zotero-cli browser` subcommand and flag.

## Choosing a path

Choose a path from the user's workflow, the access available and any user instructions; no path is preferred in general.
The paths differ in how they find metadata and files:

| Path | Commands | Behavior |
| --- | --- | --- |
| Identifier lookup | `add doi`, `add url`, `add isbn` | Looks up metadata; DOI and URL lookups find PDFs over plain HTTP and open-access sources, without the browser's login session |
| Browser Connector | `browser save`, `browser batch` | Runs the Connector's toolbar save in the user's browser, with its translators, cookies, proxy and attachment handling |
| Local file or existing item | `add file`, `attach` | Imports a file you have or attaches one to an existing item; an attached link is not a stored PDF |

Before creating an item, search the intended library for its DOI, ISBN and title.
`add` reuses an existing item by default, so repeating it does not repair a missing PDF.
For an existing item, inspect its attachments rather than registering it again.
A browser save behaves like a toolbar click, so a reload or another tab can create a second item.

## Limiting retries

Routine acquisition gets bounded effort per paper:

1. Make one normal attempt on the chosen path.
1. Retry once only when an observed condition has changed, such as a completed login, a cleared challenge, a corrected destination, or a finished load.
1. Try at most one distinct, documented alternative path or source.
1. If it still fails, stop that paper and continue with independent work.

Changing URL variants, browser settings or request parameters without new evidence is not a new strategy.
When a shared prerequisite such as the bridge, authentication or the destination fails, stop the affected batch and resolve it once.
If an operation may already have written data, check its job with `browser result` and the library before any new save.
Stop when the user says to stop investigating a paper or route.
An explicitly requested diagnosis may go further, with a concrete hypothesis and recorded outcomes.

## Saving through the browser Connector

`zotero-cli browser` sends jobs through a local broker to a Connector that runs the save in the user's own browser.
The CLI never sees the browser's cookies and does not download the PDF itself.
The Connector opens tabs and closes them conservatively, and the broker carries jobs and keeps their results.
You own duplicate checks, verification, retry limits, and deciding when to involve the user.

### Checking the bridge

Confirm these prerequisites before dispatching any browser work:

- **Support**: `zotero-cli browser --help` must work, and the browser needs a Connector build with Browser CLI.
  Ordinary released Connectors do not implement it.
- **Broker**: One `zotero-cli browser serve` process must be running.
  Reuse it rather than starting a competing one, and do not restart it while a save is unresolved.
- **Pairing**: The Connector is paired in its preferences under Advanced, Browser CLI, with the broker's port and token file contents.
  Never print the token.
- **Connection**: `zotero-cli --json browser status` must report `data.connected: true`.
  Broker and browser must reach the same loopback port.
  From WSL with a Windows browser, check this first, and run the broker and CLI on Windows if it fails.
- **Options**: A non-default `--port` or `--token-file` must be passed to every related command.

`zotero-cli config` does not check the bridge.
A missing command or connection is a setup blocker, not evidence that a paper is unavailable.
Use the browser profile that has the required access, because a fresh profile has none of the user's logins.
`--url` opens a tab in the running browser but does not launch a browser.

### Saving one paper

A typical single save checks the bridge, then saves in a background tab:

```bash
zotero-cli --json browser status
zotero-cli --json browser targets
zotero-cli --json browser save --url https://doi.org/10.1038/s41586-021-03819-2 --target L4 --background --close-on-success
zotero-cli --json browser inspect --tab-id 42
zotero-cli --json browser focus --tab-id 42
zotero-cli --json browser save --tab-id 42 --target L4
zotero-cli --json browser result JOB_ID --timeout 180
```

Use the IDs the commands return; `L4` and `42` are examples.
The flags and results behave as follows:

- **Target guard**: `--target` requires that target to be selected in Zotero already; it does not select it, and omitting it saves to the current selection.
  `L` and `C` IDs come from `browser targets` and are Connector desktop IDs, not web API library IDs or item keys.
- **Library queries**: The CLI's active library is independent of the Connector's selection.
  Use `library list` and `library switch` so duplicate checks and verification query the intended library.
- **Tab cleanup**: `--close-on-success` closes only the background tab that this request created, after a confirmed save.
  Failures, uncertain outcomes, tabs the user touched, and tabs saved with `--tab-id` stay open; `tab.closed` and `tab.closeReason` say which.
- **Retained tabs**: After a failure, inspect the retained tab, `focus` it only when the user must act, and resume with `--tab-id`.
  Do not open another copy of the URL.
- **PDF requirement**: A save fails unless a stored PDF is confirmed for each returned item; `--allow-no-pdf` permits an intended metadata-only save.
  A failed save can still have created metadata, and its receipt stays under `data`.
- **Timeouts**: A CLI timeout does not cancel the job.
  Recover its outcome with `browser result JOB_ID` and never submit a second save for it.
  The broker keeps results only while it runs.
- **Serialized jobs**: The broker runs one job at a time, so `inspect` and `focus` wait behind a running save.
  Ask the user to visit that tab directly meanwhile.

The `--background` and `--close-on-success` options need a Connector build that supports them; older builds ignore them.

### Waiting for pages and human verification

Each save first waits for the page and its translator, up to `--ready-timeout` seconds (default 30, range 0.5 to 120).
A PDF save waits for an actual translator or PDF and proceeds as soon as one is ready.
`--timeout` (default 120) is the CLI's wait for the whole job, so set it above the readiness budget with time left for the download.
For example, `--ready-timeout 60 --timeout 180` suits slow publishers; both apply only to that invocation.

Two pre-save states create no item:

- **`state: loading` with `waitingFor: translator`**: Detection expired, which may mean a slow or unsupported page.
  It is not evidence of a CAPTCHA or of a need for user action.
- **`state: needs_user_action`**: The page title looks like a challenge page, such as a CAPTCHA.
  This is a title heuristic, not a diagnosis of access rights or the challenge provider.

If a CAPTCHA is visibly in progress or reported as active, defer that tab and do not save it or include it in a batch.
A helper starting work, an enabled save button, a detected translator, or `inspect` reporting `ready` does not show that the challenge cleared.
Confirm clearance from the page itself or from the user, then inspect and resume the same tab; a fixed delay is not confirmation.
The tool does not solve CAPTCHAs, and CAPTCHA extensions are optional parts of the browser environment.

### Saving a batch

For several new publications, check each against the intended library first, then save the remaining URLs in one batch:

```bash
zotero-cli --json browser batch URL1 URL2 URL3 --target L4 --interval 5 --ready-timeout 60 --timeout 180
```

A batch needs `--target` or `--destination` and distinct URLs.
It does not query the library or repair existing items.
It saves one paper at a time in background tabs with close-on-success, and never focuses a tab.
`--interval` sets the gap after each result before the next submission (default 2 seconds, range 0.5 to 60).
Separate `save` calls have no gap, so pace them yourself.

The report under `data` replaces the single-job `data.result` with these lists:

- **`completed`**: Confirmed saves.
- **`deferred`**: Tabs left loading or needing user action, to handle together after the pass, using `focus` only when the user must act.
- **`failed`**: Errors, including partial saves that need inspection before any retry.
- **`unattempted`**: URLs not submitted because the pass stopped.

A timeout, a lost connection, a failed destination or target check, or a failure with no confirmed desktop save sets `stopped` and ends the pass.
Any incomplete batch returns `ok: false` with exit code 1 and keeps every outcome.
A prompt inside an already running save can still stop a batch, because deferral happens only before a save starts.
Do not start another batch on the same broker while one is unresolved, and do not close successful tabs the user touched.

### Moving saves to a destination

`--destination` on `save` or `batch` moves the finished save session to an `L` or `C` target, as the Connector popup does.
The item is first created in the currently selected library, which must allow file saving, and then moved with its attachments.
The move is not atomic, and it changes Zotero's visible selection.
With batch `--destination`, `--target` guards only the first paper; without it, `--target` guards every paper.

A confirmed move returns `destinationApplied: true` and a `target` equal to the destination; anything else is reported as a failure.
A failed or uncertain move keeps the receipt and tab and stops a batch, so inspect Zotero before retrying.
A reused page session cannot be moved to a different destination, and its popup may still show the original one.
Do not retry or move from that popup, and do not edit the popup while a save is moving.
Destinations and non-default `--ready-timeout` values need an updated Connector, which the CLI checks before saving.

## Verifying and reporting results

A save receipt shows only that the Connector stored something, so verify the item before reporting it.
Report outcomes once, after the work, without turning Zotero notes into a log.

### Verifying a saved paper

Check a saved paper in this order:

1. Read the job's `data.result`, not only the top-level `ok`.
   `sessionID`, `connectorItemID` and `connectorAttachmentID` identify the save session, not Zotero items.
1. Find the saved item in the intended library and compare its DOI and title with the requested paper.
   A translator can identify the wrong work.
1. List its child attachments and check that the main-text file is the right paper, readable and apparently complete.
   Reading by the parent key can select supplementary material instead.

Verification does not require reading the whole paper; check the version only when requested or when it matters to the intended use.
A candidate URL, a linked attachment, a closed tab or a stored-PDF receipt alone does not prove that the complete paper was obtained.

### Reporting outcomes

Use Zotero notes for literature content, interpretation and relevant evidence limits, such as "abstract only reviewed".
Do not create or append notes to log registration, acquisition attempts, tool failures or verification history.
Keep details needed for continuation in the task's established work records, following user instructions.
If no such record is established, include those details in the response rather than creating a new store.

Give one consolidated report covering these points:

- **Successes**: A brief summary, distinguishing metadata-only, acquired and verified results where that affects the user's next step.
- **Unresolved papers**: Each identified by title, DOI or item link, with its blocker and the action or condition needed to continue.
- **Shared blockers**: Grouped once instead of repeated for each paper.
- **Operational detail**: Routes, failure stages and item, job or tab IDs only when needed for user action, recovery or a requested diagnosis.
- **Restored files**: Backups or restored files reported as preservation, not as new downloads.

Link sources by their canonical publication URLs, without tokens, cookies or signed URL parameters.
