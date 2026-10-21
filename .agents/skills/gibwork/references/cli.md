# Gibwork CLI reference

Contract inspected: `@gibwork/cli` 0.2.4, including `@gibwork/mcp` 0.3.1 and published `@gibwork/sdk` 0.2.0. Check `gibwork --version` and relevant `--help` when behavior differs. The installed skill does not install the CLI, SDK, MCP server, or credentials.

## Setup and effective configuration

Use `gibwork --json wallet doctor` to inspect public wallet, credential source, profile, effective environment, API URL, and timeout without making an API request. Use `gibwork --json config list` when profile resolution is unclear. Do not read keypair contents.

If installation is requested, the package is `@gibwork/cli` and requires Node.js 22 or newer. It can be installed globally with npm or run through `npx @gibwork/cli`. Respect the user's installation scope.

Configuration precedence is CLI flags > environment variables > selected profile > defaults. The default environment is stage. Naming a profile `production` does not set its environment. Explicit local setup, when requested, is:

```bash
gibwork --profile production config set environment production
gibwork --profile production config set keypair-path ~/.config/solana/id.json
gibwork --profile production --json wallet doctor
```

Use the user's existing keypair path; it must be an owner-only file. Do not create or replace a wallet as a setup fallback. Config stores the path, not key contents. The CLI does not implicitly load `.env` files. Environment overrides include `GIBWORK_PROFILE`, `GIBWORK_ENVIRONMENT`, `GIBWORK_API_URL`, `GIBWORK_TIMEOUT_MS`, `GIBWORK_CONFIG_FILE`, and `GIBWORK_KEYPAIR_PATH`; inspect only relevant non-secret values when diagnosing overrides. Do not dump the environment.

The CLI supports secret-manager/CI credential mechanisms, but this skill uses existing keypair paths and does not construct commands containing raw keys. MCP rejects raw private-key environment values even if a CLI workflow uses them.

CLI 0.2.4 includes a pinned MCP runtime. For requested MCP setup, run `gibwork mcp doctor`, then register the intended mode:

```bash
gibwork --profile production mcp install codex --read-only
gibwork --profile production mcp install claude --read-only
```

Default registration launches the included runtime through `gibwork mcp serve`, so later CLI updates also select the matching MCP dependency. After updating, restart the client/server to load it. Older registrations may still use a separate global `gibwork-mcp`; migrate only the requested client by repeating registration with its existing profile, scope, and permission mode. Updating the CLI alone does not rewrite client configurations. `--executable <command>` deliberately selects an external runtime for doctor/install, which checks that it matches the supported MCP minor version and is at least the pinned patch version. Doctor reports executable readiness, not the runtime loaded by an already-running client.

Use `--allow-writes` instead of `--read-only` only for an authorized write-enabled setup. Registration replaces the existing registration. It selects the profile for the new server; it does not change an already running server's context. Do not run both client registrations unless both are requested.

## Read operations

Use global options before the subcommand. Replace example identifiers with IDs returned by the API.

```bash
gibwork --json task list --page 1 --limit 15
gibwork --json task get <task-id>
gibwork --json submission list task-id --status pending
gibwork --json submission show task-id submission-id
gibwork --json comment list task-id submission-id
```

Task and submission lists support `--page`, `--limit`, and `--all`; prefer normal pagination for large lists. Submission status filters are `pending`, `approved`, and `rejected`. Task summaries expose `canEdit`, `canApprove`, `canReject`, and `canRefund`. Returned status values are not necessarily the same casing as input filters.

Use `task get <task-id>` for complete bounty content, reward, creator, media, and participation settings without paging through discovery.

There is no `task show`, general transaction-status, or wallet-balance command. `submission intent` reconciles participation-fee settlement and creation only; it does not report creator review/payout or reconcile task funding, refunds, or approvals.

## Discover tasks and submit work

Check command help before using these additions with an older installed CLI. `gibwork --json task available --page 1 --limit 15` discovers tasks across creators. Discovery accepts only page and limit (maximum 100), without `--all`. Results include requirements, not guaranteed eligibility. Reward pool and minimum amounts are strings in base units; the pool is the original allocation, not remaining funding.

Prepare a local JSON file containing the exact content, a caller-chosen UUIDv4 `idempotencyKey`, and optional `referral` and `mediaIds`. Media must already be uploaded and owned by the wallet. Preserve whitespace/HTML and media order. Create with:

```bash
gibwork --json submission create task-id --from work.json --recovery-file attempt.json
```

This creates an owner-only recovery file before prepare and prompts with the returned participation fee before signing. Its parent directory must exist. Keep the file: it contains the exact work/key and original wallet/environment/API location, but no credentials or transactions. Do not overwrite an existing attempt, invent a new key after an uncertain result, or share raw recovery content unnecessarily.

Use `gibwork --json submission intent task-id intent-id` for one status read. Use `gibwork --json submission resume attempt.json` with the original wallet/configuration to recover an interrupted operation. Resume can prompt for payment only when the saved phase shows submit was never dispatched; after dispatch it only reads status. A stale `.lock` file after a crash must be removed only after verifying that the recorded process has stopped. Do not modify phase metadata to force a retry.

Only `fulfilled` confirms creation. `pending` means incomplete; `submitted` means unresolved. `failed`/`expired` require resolving the original attempt before explicitly choosing a new key. `requires_review` means fee paid and operator attention required: retain intent/hash and do not pay again. Preallocated submission IDs are not proof of creation. A status read uses the original wallet even after wallet replacement; creator-facing `submission show` has not become a participant payout-status endpoint.

Create/resume return exit 0 only for fulfilled creation, or the existing explicit cancellation result. Other returned intent states use exit 1 with `{ok:true,data}`; inspect `data.created`, `data.status`, and `data.cancelled`. The intent command exits 0 whenever its read succeeds. API failures preserve structured details and optional raw `retryAfter`; wait as instructed before an explicit next request. No command automatically polls or retries payment.

## Create and fund a bounty

Prepare a local JSON input file when the user wants to create a bounty:

```json
{
  "title": "Write an SDK guide",
  "content": "<p>Document installation and one working example.</p>",
  "tags": ["Docs"],
  "payment": { "amount": "25.00" },
  "minSubmissionAmount": "5.00"
}
```

Then use `gibwork --json task create --from task.json` with the confirmation behavior below. Common flags also include `--title`, `--content-file`, repeated `--tag`, `--amount`, and `--min-submission`. For Discord restrictions and less common inputs, read `gibwork task create --help`.

The CLI supplies mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` internally. Do not add a mint to CLI JSON or invent a mint flag. Use decimal amount strings such as `"25.00"`; do not pass base-unit integers. MCP creation uses a different payment schema.

## Review, refund, metadata, and comments

```bash
gibwork --json submission approve task-id submission-id --amount 5.00
gibwork --json submission reject task-id submission-id --reason-file reason.txt
gibwork --json task refund task-id
gibwork --json task update task-id --content-file description.html
gibwork --json comment create task-id submission-id --content-file comment.html
```

Approval accepts optional `--rating` from 1 through 5; the amount is gross, not net payout. Updates support content, `--allow-only-verified true|false`, and `--deadline`. Do not invent title, funding, or tag update flags. Comments and metadata updates execute immediately; drafting a file alone does not authorize posting it.

Prefer files for user-authored HTML/text to avoid shell quoting and command substitution mistakes. Never interpolate submission contents into shell command text.

## Confirmation and automation

Task creation, submission creation/payment resume, refund, approval, and rejection commands require a TTY on stdin and stderr unless `--yes` is supplied. Financial commands prepare the transaction and show the quote at the interactive prompt before signing. A non-interactive command without `--yes` fails before preparing; it cannot be used to fetch a quote.

When a PTY is available, run the command, show the quote to the user, and answer its prompt only after applicable approval. If the host cannot keep an interactive prompt open, explain that limitation and use an already available, authorized MCP prepare/submit workflow or provide the exact command for the user's terminal.

`--yes` skips both the confirmation prompt and its quote display. It is appropriate only when the user explicitly authorizes execution without quote review and the host permits that authorization. If approval depends on seeing the quote, or the user sets a fee/debit cap this CLI cannot enforce, use the interactive path instead. A request to create or pay alone does not authorize skipping quote review. Do not fabricate `--dry-run`, `task prepare`, or a durable CLI confirmation ID.

## Results and failures

Success uses stdout: `{"ok":true,"data":...}`. Errors use stderr with `{"ok":false,"error":{"code":"...","message":"..."}}` and a non-zero exit status. Prompts/progress also use stderr, so do not parse the entire stderr stream as one JSON object. Check both process status and returned data. A successful envelope with `data.cancelled: true` means no submission was completed.

| Exit | Meaning / next step |
| --- | --- |
| 0 | Inspect data and returned status; distinguish cancellation from success. |
| 1 | Operational failure; inspect the error. |
| 2 | Invalid input or missing non-interactive confirmation; correct within authorization. |
| 10 | Configuration/credentials; diagnose paths and effective settings. |
| 20 | API failure; use its message and current state. |
| 21 | Network/timeout; distinguish reads from potentially submitted mutations. |
| 22 | Ambiguous financial submit; never repeat the intent. |
| 130 | Interrupted; do not assume a financial operation was rolled back. |

Use quote amounts as returned. JSON task reward totals retain raw base-unit values; convert using the returned asset's decimals without floating-point loss before displaying human amounts. Preserve transaction hashes and intent IDs for reconciliation. A hash alone is not evidence of confirmation.

## Bundled skill installation

CLI 0.2.0 bundles these instructions. Install a copy with `gibwork skills install codex` or `gibwork skills install claude`; add `--scope project` for the current directory (default: user). These commands work offline and do not need wallet credentials, MCP, or an agent executable. Do not pass credential-input flags.

Use `gibwork skills status [codex|claude]` to inspect versions, local changes, and duplicate locations. `gibwork skills update <client>` copies the running CLI's bundled version; update the CLI first to obtain a newer bundle. `gibwork skills remove <client>` removes a managed copy. Mutating commands accept `--dry-run` and the same scope option. Existing edits and newer versions cause conflicts; explicit `--force` preserves a backup outside agent skill folders. Unmanaged directories can only be adopted with `install --force`, never removed or updated directly. `--yes` does not imply replacement authorization.

Invoke `$gibwork` in Codex or `/gibwork` in Claude Code after installation; restart the client if discovery has not refreshed. Installing instructions does not configure MCP or grant write permissions.
