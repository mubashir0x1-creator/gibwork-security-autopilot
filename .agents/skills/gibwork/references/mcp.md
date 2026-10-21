# Gibwork MCP reference

Contract inspected: `@gibwork/mcp` 0.3.1 with published SDK 0.2.0. Tool names below are the server's names; clients may wrap them in a server namespace. Match the exposed tool, not a hardcoded host prefix. Consult the connected schema for version differences.

## Runtime and reads

`gibwork_wallet_status` takes no arguments and returns `walletAddress`, `profile`, `environment`, `writesEnabled`, and `timeoutMs`. It loads local configuration, not an API connectivity or balance check. Missing credentials can make this call fail; it is not a tool for receiving private keys.

| Tool | Inputs |
| --- | --- |
| `gibwork_task_list` | Optional `page`, `limit`, `pageAll` |
| `gibwork_task_available` | Optional `page`, `limit`; no `pageAll` |
| `gibwork_task_get` | `taskId` |
| `gibwork_submission_intent_get` | `taskId`, `intentId`; original wallet required |
| `gibwork_submission_list` | `taskId`; optional pagination and `status` |
| `gibwork_submission_get` | `taskId`, `submissionId` |
| `gibwork_comment_list` | `taskId`, `submissionId` |

Pagination is one-based, defaults to page 1 and limit 15, with maximum limit 100. Status filters are `pending`, `approved`, and `rejected`; preserve returned status values. Inspect submission content, contributor, media, and comments before assessing the work. Task summaries contain action permissions such as `canApprove`.

Use `gibwork_task_get` when you already have a bounty ID and need its complete content, reward, creator, media, or participation settings. Do not page through discovery to approximate a by-ID lookup.

Use actual `writesEnabled` and exposed tools to establish permissions. With read-only registration, explain the restriction. Re-registration is a configuration change, not automatic recovery from a denied write.

## Discover work and submit

`gibwork_task_available` discovers tasks across creators using the configured wallet. Page/limit default to 1/15, limit is at most 100, and the offset must remain a safe integer. Eligibility is checked during preparation. Preserve returned requirements and restrictions. Asset and minimum amounts are string base units; the reward pool is the original allocation, not remaining funding.

`gibwork_submission_create_prepare` accepts `taskId`, raw `content` (1–50,000 Unicode characters), a caller-chosen UUIDv4 `idempotencyKey`, optional nullable `referral` (up to 200 characters), and optional nullable `mediaIds` (up to ten distinct UUIDv4 values for existing wallet-owned uploads). Preserve whitespace/HTML and media ordering. There is no media upload tool.

Preparation persists the original work/key locally before requesting the intent. Only a payable `pending` intent returns a `confirmationId`; other states return without one. Show `fee.amount`, `fee.totalDebit`, symbol/mint, destination, wallet/environment, intent expiry, and `confirmationExpiresAt` before obtaining approval. Do not hard-code the participation fee. Submit once with `gibwork_submission_create_submit` and only `{ "confirmationId": "..." }`.

The confirmation is single-use, bound to the wallet/profile/environment/API location and saved attempt, and expires at the earlier of five minutes or intent expiry. The API `expiresAt` and block-height validity are separate. Submit rechecks the original intent and refuses changed payment attempts or quotes. Renewed preparation invalidates older confirmations; approval must cover the returned quote.

| Intent status | Meaning and next step |
| --- | --- |
| `pending` | Incomplete; payment can resume only with reliable local evidence that dispatch never occurred. |
| `submitted` | Settlement unresolved; read the original intent later. |
| `fulfilled` | Submission created; creator review and payout are separate. |
| `failed` / `expired` | Resolve the original attempt before explicitly choosing a new key. |
| `requires_review` | Fee paid; operator attention required. Retain the IDs/hash and do not pay again. |

Only `created: true` / `fulfilled` confirms creation. An allocated `taskSubmissionId`, hash, or successful tool exchange does not. Use `gibwork_submission_intent_get` for one creation/fee-settlement read using the original wallet; it does not report creator review/payout and does not reconcile bounty funding, approval, or refund operations. No automatic polling or payment retry is provided.

For an interrupted pre-dispatch attempt, repeat prepare with the exact original payload/key and original configuration. The server checks durable history and only returns another payable confirmation when safe. Once dispatch is recorded, it only reconciles, even if the API still says `pending`. A lost/expired confirmation does not prove no payment was dispatched. Do not switch to CLI resume/create to retry it.

Recovery is stored in an owner-only `mcp-submissions` directory beside the effective Gibwork configuration file, or the operator's `--state-dir`. Keep the same directory across restarts/processes. It contains private work and progress, but no credentials or transactions. Do not delete records, change directories, or edit phases to force retries. For attempts made outside this state directory, use intent reads; local history cannot prove they were never dispatched. After a crash, a `.lock` may remain: verify its recorded PID has stopped before removing only that lock. A persistence error after dispatch can carry known outcome/IDs; preserve them and reconcile.

## Creation

`gibwork_task_create_prepare` requires:

- `title`: nonempty, maximum 120 characters.
- `content`: nonempty, maximum 10,000 characters; safe HTML supported.
- `tags`: an array of up to three unique discovery tags.
- `payment`: `{ "mintAddress": "...", "amount": "25.00" }`.
- `minSubmissionAmount`: a decimal string such as `"5.00"`.

Amount strings require exactly two decimals. The MCP schema requires a Solana mint address and passes it to the SDK/API; syntactic validity is not proof a token is supported. Establish the intended mint from the user or trusted current configuration/documentation, and let preparation validate it. Do not guess based only on a ticker or silently copy a mint from another environment. The CLI's fixed mint is not an MCP default.

Optional fields include `primarySkillSlug`, `deadline`, `allowOnlyVerifiedSubmissions`, and Discord guild/role restrictions. Read the exposed schema when those features are requested. Do not invent legacy `paymentAmount`, `paymentMint`, or `wait` inputs.

Preparation returns `confirmationId`, `intentId`, `taskId`, wallet/profile/environment, `createdAt`, `expiresAt`, `lastValidBlockHeight`, and `paymentQuote`. Show the quote's token, `fundingAmount`, `platformFee`, and `totalDebit` before seeking the required approval. Submit once using `gibwork_task_create_submit` with only `{ "confirmationId": "..." }`.

## Approval and refund

| Prepare tool | Inputs | Quote and final tool |
| --- | --- | --- |
| `gibwork_submission_approve_prepare` | `taskId`, `submissionId`, `amount`; optional `rating` 1–5 | `approvalQuote`; `gibwork_submission_approve_submit` |
| `gibwork_task_refund_prepare` | `taskId` | `refundQuote`; `gibwork_task_refund_submit` |

Approval amount is gross and must have exactly two decimals. Show `grossApprovalAmount`, `platformFee`, `referralFee`, `netPayoutAmount`, token, and `closeTask` from the returned quote. For refunds, show `grossRefundAmount`, `platformFee`, `netRefundAmount`, and token. Do not hardcode fee percentages or describe a gross amount as the contributor's net receipt.

Both submit tools accept only the corresponding `confirmationId`. Prepared IDs are process-local, single-use, and normally expire after five minutes; use the returned expiration. They are tied to operation kind, wallet, profile, and environment. Restarting the server loses them. IDs are consumed before signing, so an error does not make an ID reusable. Block-height validity may expire separately.

If an operation is definitely unsubmitted and its quote expired, re-prepare the still-requested action and obtain approval for the new quote. If an ID is unknown or already used and submission history is uncertain, reconcile first; do not treat every `PENDING_INTENT_ERROR` as safe to retry.

## Other writes

| Tool | Inputs and effect |
| --- | --- |
| `gibwork_task_update` | `taskId` plus at least one of `content`, `allowOnlyVerifiedSubmissions`, or `deadline`. Changes metadata immediately. |
| `gibwork_submission_reject` | `taskId`, `submissionId`, optional `reason`. Changes review state; requires explicit approval under the tool/host contract. |
| `gibwork_comment_create` | `taskId`, `submissionId`, `content`. Posts immediately; safe HTML supported. |

There are no prepare tools for these writes. Do not turn review feedback into a rejection or public comment without the user's request.

## Results and errors

Successful MCP responses expose the returned object as structured content and JSON text; they do not use the CLI's `ok/data` envelope. Failed calls may set `isError: true` and contain `{ "error": { "code": "...", "message": "..." } }`. A successful transport exchange is not necessarily a successful operation.

- `USAGE_ERROR`: reconcile inputs with the exposed schema.
- `CONFIG_ERROR` / `CREDENTIAL_ERROR`: diagnose public settings using the CLI reference when appropriate. MCP accepts an owner-only keypair file, not raw private-key environment values.
- `WRITES_DISABLED`: explain the permission restriction.
- `PROTOCOL_ERROR`: retain recovery identifiers and reconcile; do not treat malformed responses as proof of no payment.
- `RECOVERY_ERROR`: preserve local records and returned IDs; address the storage/lock issue before resuming.
- `PENDING_INTENT_ERROR`: distinguish expiry before submission from unknown/consumed IDs.
- `API_ERROR`, `NETWORK_ERROR`, `TIMEOUT_ERROR`, `CANCELLED`: inspect the action and available context before any retry; do not assume financial submission was undone.
- `AMBIGUOUS_SUBMIT`: report unknown outcome, preserve returned identifiers, and inspect supported reads. Do not re-submit or prepare a replacement intent.

There is no dedicated transaction-status, pending-intent-list, or wallet-balance tool in this contract. Task details and submission reads may help reconciliation but may not settle transaction outcome. Do not invent a recovery tool or claim success from stale task state.

Preserve returned IDs, hashes, statuses, and raw API `retryAfter` (seconds or HTTP date). Respect that delay before an explicit next request. Quote amounts are already decimal strings; raw task reward totals may be base units and require the returned token decimals for display. Do not interpret a prepared `taskId` or transaction hash alone as a confirmed operation.
