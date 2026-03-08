# Markdown TUI Documentation and UX Polish Design

**Date:** 2026-03-08

**Goal:** Add user-facing documentation and polish the document translation / navigation experience so users understand app behavior, translation progress, and caching.

## Scope

- Add a root-level `README.md` for end users
- Document install, run, key bindings, translation behavior, and cache behavior
- Show progressive translation updates in the markdown viewer
- Support translation cancellation with `t`
- Surface cache hits in the status area
- Improve empty-state and help text clarity
- Preserve the existing markdown viewer, tree navigation, and translation pipeline

## Non-Goals

- New search UI
- Cache management commands beyond basic behavior description
- Multi-language target selection
- Replacing `deep-translator`

## Recommended Approach

Keep the current layout and interaction model, and refine it with clearer state transitions. The markdown viewer should immediately switch into translation mode when `t` is pressed, then render translated chunks as they arrive. The status line should communicate whether translation is running, cached, cancelled, completed, or failed.

Translation caching should persist across app runs in a platform-appropriate global cache directory. Cache validity should be based on absolute file path plus a content hash so changed files automatically invalidate old translations.

## Documentation Plan

Create `README.md` with:

- What the tool does
- Requirements and setup using `uv`
- How to run `./md-man <path>`
- Main key bindings
- Translation workflow:
  - live chunk-by-chunk updates
  - `t` to toggle / cancel
  - global translation cache
- Cache location behavior:
  - macOS: `~/Library/Caches/md-man/translations/`
  - Linux: `~/.cache/md-man/translations/`
  - Windows: `%LOCALAPPDATA%/md-man/translations/`
- Known limitations

## UX Polish Details

### Translation UX

- If a cached translation exists, show it immediately and set status to indicate a cache hit
- If no cache exists, switch the viewer into translation mode right away
- Update the viewer after each translated chunk
- Show status text such as `번역 중 2/8`
- If `t` is pressed while translation is running or showing translated output, cancel / exit translation mode and restore the source markdown
- If translation fails, restore source markdown and show a clear error

### Navigation / Status UX

- Tighten empty-state text to distinguish:
  - no file selected
  - no markdown files found
  - invalid root path
- Keep the status bar concise and informative
- Make help text emphasize the most important keys only
- Keep current focus and tree behavior unchanged unless needed for clarity

## Architecture Changes

### Translator Layer

- Extend the translator abstraction with:
  - progressive per-chunk callbacks
  - persistent cache read/write
- Keep chunking and markdown-aware exclusion rules in `src/md_man/translator.py`
- Store cache files in a global cache directory using hashed file keys

### App Layer

- Run translation in a background worker
- Push partial updates back onto the UI thread
- Track the active translation request so stale worker updates do not overwrite the current file view
- Distinguish translation states:
  - source view
  - translating
  - translated from cache
  - translated live

## Error Handling

- Translation worker errors must not crash the app
- Cache read/write failures should degrade gracefully to uncached translation
- Cancelling translation should stop future UI updates from the in-flight request

## Testing Strategy

- Translator tests:
  - persistent cache reuse across instances
  - code fence / inline code preservation
  - chunk fallback on `None`
- App tests:
  - translation progressively updates the viewer
  - cached translation shows immediately
  - cancel returns to source markdown
- Existing scanning and viewer tests remain green

## Risks

- Worker cancellation in Textual is stateful; stale updates must be ignored by request ID
- Partial markdown rendering may look odd if chunks split awkwardly, so chunk boundaries should remain paragraph-oriented
- Persistent cache can become large over time; v1 will document behavior but not add pruning
