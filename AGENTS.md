# AGENTS.md — discord-bot

## Run

```bash
source venv/bin/activate
python main.py
```

No test/lint/typecheck config exists. No `pyproject.toml` or `setup.cfg`.

## Structure

- `main.py` — entry point. Loads all `.py` files in `commands/` (skips `_`-prefixed) as cogs. Slash commands synced on startup.
- `commands/_utils.py` — shared helpers: `COLOR`, `ok()`/`warn()` embeds, `fetch_json`, `parse_duration`, `check_allowed()` auth guard, `TimeoutView`.
- `commands/_storage.py` — JSON-backed persistence (`ai_data.json`) for AI rules, tools toggle, system prompt.
- `no-work/` — inactive/decommissioned cogs, not loaded.
- `.env` — required: `BOT_TOKEN`, `ALLOWED_USER_IDS`, `GROQ_API_KEY`, `GEMINI_API_KEY`. Gitignored.

## Conventions

- **All active cogs** use `@app_commands.command` (slash commands) with `@app_commands.allowed_installs(guilds=False, users=True)` and `@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)`. New commands should follow this.
- **Auth guard**: each command calls `check_allowed(interaction)` first. If `ALLOWED_USER_IDS` is set, only those users can run commands.
- **Cog registration**: each file ends with `async def setup(bot): await bot.add_cog(MyCog(bot))`.
- **Components V2** supported (discord.py 2.6+). **Build layouts dynamically in `__init__`** with final values — avoid class-level skeletons with `find_item` updates. Use `ui.LayoutView` (not `ui.View`) for V2 messages. No `content`, `embeds`, `stickers`, or `polls` allowed — use `TextDisplay`/`Container` instead. 40 component max across all nesting. `TextDisplay` has a shared 4000-char limit across all text displays in a view.
  - **Top-level** (directly under LayoutView): `TextDisplay`, `ActionRow`, `Section`, `Separator`, `MediaGallery`, `File`, `Container`.
  - **Non-top-level**: `Button`/`SelectMenu` (must be in `ActionRow`), `Thumbnail` (must be `accessory` of `Section`).
  - **Container**: wraps children in a bordered box with optional `accent_color`. Can hold any top-level components. No nested Containers.
  - **Section**: text + accessory (`Thumbnail` or `Button`) side-by-side. Text can be a raw string (auto-wrapped) or `TextDisplay`.
  - **ActionRow**: holds buttons/selects only. Not auto-laid-out in V2 — must be placed explicitly in the layout.
  - **MediaGallery**: 1–10 items. `add_item(media=url)` (keyword). `MediaGalleryItem` has no `id` param.
  - **Separator**: `spacing` is `SeparatorSpacing.small` or `.large` (no `medium`).
  - **`id` parameter**: on most components but NOT on `MediaGalleryItem`. Use `find_item(id)` for deep lookups.
  - **Migration**: old messages can be edited to V2 by setting `content=None, embeds=[]`, but not back.
  - Buttons inside a Container's ActionRow must be built in `__init__` with explicit `custom_id` and callback set manually.
- **All responses** use `discord.Embed` with `COLOR=0x2b2d31` via `_utils.ok()`/`_utils.warn()`.
- **AI** uses Groq API by default, Gemini for `gemini/`-prefixed models. Web search via `ddgs`. Model list in `commands/ai.py:MODELS`.

## Env

- `.env` is gitignored. Template: `BOT_TOKEN`, `ALLOWED_USER_IDS` (comma-sep), `GROQ_API_KEY`, `GEMINI_API_KEY`. For `/crypto balance`: `TATUM_API_KEY` (get at [tatum.io](https://tatum.io)).
- `ai_data.json` is gitignored (matches `*.json` rule in `.gitignore`).
