# \_utils.py — Shared Utilities

## Constants

| Name | Value |
|------|-------|
| `COLOR` | `0x2b2d31` — default embed color |

## Helpers

### `ok(description: str) -> discord.Embed`
Simple embed with green-ish text. Used for success messages.

### `warn(description: str) -> discord.Embed`
Simple embed with yellow-ish text. Used for warnings/errors.

## Author Guard

### `async ensure_author(interaction, view) -> bool`
Checks `interaction.user.id` against `view.author_id`. Sends ephemeral "This isn't your game!" and returns `False` on mismatch.

**Usage:**
```python
async def callback(self, interaction):
    if not await ensure_author(interaction, self.view):
        return
    # ... game logic
```

## View Base Class

### `TimeoutView` (extends `discord.ui.View`)
Auto-disables all children on timeout and edits the message so Discord stops accepting clicks.

```python
class MyView(TimeoutView):
    def __init__(self):
        super().__init__(timeout=60)  # defaults to 180
```

## Parsing

### `parse_duration(duration: str) -> int | None`
Parses duration strings (`10m`, `1h`, `2d`, `30`) into seconds. Returns `None` on invalid input.

```python
secs = parse_duration("5m")  # 300
secs = parse_duration("2h")  # 7200
```

## Network

### `async fetch_json(session, url, **kwargs) -> dict | None`
Performs a GET request and returns parsed JSON, or `None` on non-200 status. Passes extra kwargs to `session.get()`.

```python
async with aiohttp.ClientSession() as session:
    data = await fetch_json(session, "https://api.example.com/data")
    if data is None:
        ...
```

## Error Handlers

### `async handle_api_error(ctx, error, message="Something went wrong.") -> bool`
Catches `CommandInvokeError` and `HybridCommandError`. Sends `warn(message)` and returns `True` if handled.

```python
@command.error
async def on_error(self, ctx, error):
    if await handle_api_error(ctx, error, "API call failed."):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        ...
    raise error
```

### `async handle_command_error(ctx, error, permission_msg=None)`
Catches `MissingPermissions`, `MemberNotFound`, `MissingRequiredArgument`, `BadArgument`. Raises unhandled errors.

```python
@command.error
async def on_error(self, ctx, error):
    await handle_command_error(ctx, error, permission_msg="You need higher perms.")
```
