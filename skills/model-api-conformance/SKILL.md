---
name: model-api-conformance
description: Build and run contract tests for a model API adapter. Use when introducing a model route, changing an SDK, or verifying what the calling application can rely on.
---

# Model API conformance

## Why this skill

A provider can accept a request while returning a result the caller interprets incorrectly. Compatibility belongs to a particular route, configuration and caller contract. The useful output is a regression test at that boundary and a decision about enabling the route.

## When to use

Use for a hosted endpoint, a local inference server, or a model gateway. Start at the caller that consumes the result. For a question about task quality after a compatible route change, use [agent-change-eval](../agent-change-eval/SKILL.md).

## Process

1. Trace a real call from request construction through the adapter to the consumer. Record the route, API/SDK version or revision if available, request options and fallback behavior. List the primitives the caller actually uses. For each, state an observable invariant and whether it is required, optional with an explicit fallback, or unused.
2. Build fixtures at the **normal adapter entry point** using the project's test runner when available. Feed raw responses or stream events through its transport seam. For a local adapter that accepts a response object directly, call that function from a small native test. Assert the normalized result and what the downstream consumer observes. Reuse a harmless tool recorder if the caller dispatches actions. Exact generated prose is rarely a protocol invariant.
3. Select cases that exercise the contract:
   - For one-shot structured results, validate the caller's schema and distinguish a valid answer from refusal, truncation, malformed output and transport failure. If a feature is unsupported, check that routing rejects it or uses the declared fallback.
   - For streaming, vary chunk boundaries and test interruption. A syntactically valid prefix can arrive before the call ends. Verify that a consumer requiring a complete call only acts after the route's completion signal. Check how cancellation and partial text are surfaced.
   - For tool calls, preserve argument types, correlation between calls and results, and ordering where promised. If concurrent calls are supported, interleave their fragments. When replay is supported, assert the documented duplicate-delivery behavior at the owner of that guarantee; an adapter test alone cannot establish external exactly-once effects.
   - For multimodal or usage-aware routes, check the parts and units the caller depends on. Missing usage stays distinguishable from measured zero. Check cache accounting only if the consumer uses it.
4. Run the fixtures against the installed adapter. If the question concerns a live endpoint, run a bounded probe when authorized and available. Capture model/route identity and sanitized observations. Separate recorded-provider traffic, synthetic fixtures, and live observations: a fixture can expose an adapter bug but cannot establish that a deployed endpoint supports the feature.
5. Deliver the runnable tests, reproduction command, and a compact matrix: **route/config | primitive | required behavior | observed behavior | evidence | disposition**. Report unrun checks and how to run them. On a mismatch, locate the first divergence between the raw response, normalized result and consumer effect.

## Common rationalizations

“The SDK returned success.” A successful transport can still deliver a truncated response that the application treats as complete.

## Red flags

A mock replaces the adapter being tested. One text completion is extrapolated to tool or schema support. A fallback silently drops a required input or loosens validation.

## Dispositions

Mark each required primitive **pass**, **mismatch**, **unsupported**, or **unverified**. Recommend **enable for the verified capabilities**, **fix and retest**, or **withhold this route for the affected caller**. State whether the decision covers adapter behavior, deployed-provider behavior, or both.
