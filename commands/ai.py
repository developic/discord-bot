import json
import os

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from ddgs import DDGS

from ._storage import (
    add_rule,
    get_rules,
    get_system_prompt,
    get_tools_enabled,
    remove_rule,
    set_tools_enabled,
)
from ._utils import COLOR, check_allowed, warn

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"
MODELS: list[app_commands.Choice[str]] = [
    app_commands.Choice(name="OpenAI GPT-OSS 120B", value="openai/gpt-oss-120b"),
    app_commands.Choice(name="OpenAI GPT-OSS 20B", value="openai/gpt-oss-20b"),
    app_commands.Choice(name="Llama 3.3 70B (versatile)", value="llama-3.3-70b-versatile"),
    app_commands.Choice(name="Llama 3.1 8B (instant)", value="llama-3.1-8b-instant"),
    app_commands.Choice(name="Qwen 3.6 27B", value="qwen/qwen3.6-27b"),
]

TOOL_DESC = (
    "You have access to a web_search tool. "
    "When you need current information, respond with the function call "
    "on its own line using EXACTLY this format (no markdown, no backticks):\n"
    "<function=web_search {\"query\": \"your search query here\"} </function>\n"
    "Then I will execute the search and give you the results."
)

SYSTEM_PROMPT = (
    "You are Mark, a helpful, knowledgeable AI assistant. Follow these guidelines:\n\n"
    "**Style & Tone**\n"
    "- Be clear, direct, and concise\n"
    "- Keep answers short (3-8 lines unless asked)\n"
    "- Use markdown formatting (bold, lists, code blocks) to structure responses\n"
    "- Be conversational but avoid fluff\n\n"
    "**Accuracy**\n"
    "- If you don't know something, say so honestly — don't make things up\n"
    "- When providing code, use proper syntax highlighting (```language ... ```)\n"
    "- Use bullet points or numbered lists for multiple items\n\n"
    "**Formatting**\n"
    "- Use **bold** for emphasis\n"
    "- Use `code` for inline code or commands\n"
    "- Use ``` for multi-line code blocks\n"
    "- Use > for quotes or important notes"
)

TOOL_ENABLED_PROMPT = SYSTEM_PROMPT + "\n\n" + TOOL_DESC


def _search_web(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        lines = []
        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")
            href = r.get("href", "")
            lines.append(f"**{title}**\n{body}\n{href}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Search failed: {e}"


import re


def _strip_think(content: str) -> str:
    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()


def _parse_func_call(content: str) -> tuple[str | None, str | None, str]:
    m = re.search(r"<function=(\w+)\s*(\{.*?\})\s*</function>", content, re.DOTALL)
    if not m:
        return None, None, content
    name = m.group(1)
    args = m.group(2)
    clean = content[:m.start()] + content[m.end():]
    return name, args, clean.strip()


async def _query_groq(interaction: discord.Interaction, prompt: str, model: str = MODEL):
    tools_enabled = get_tools_enabled()
    base_system = get_system_prompt(SYSTEM_PROMPT)
    system = TOOL_ENABLED_PROMPT if tools_enabled else base_system
    rules = get_rules()

    messages = [{"role": "system", "content": system}]
    for rule in rules:
        messages.append({"role": "system", "content": f"Rule: {rule}"})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    timeout = aiohttp.ClientTimeout(total=30)

    async def _call(payload: dict) -> dict | None:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(GROQ_API_URL, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    print(f"[Groq] {resp.status}: {body[:300]}")
                    return None
                return await resp.json()

    payload = {"model": model, "messages": messages}
    data = await _call(payload)
    if data is None:
        await interaction.followup.send(embed=warn("Groq API error."))
        return None

    content = data["choices"][0]["message"]["content"]
    func_name, func_args, clean_content = _parse_func_call(content)

    if func_name == "web_search":
        args = json.loads(func_args)
        result = _search_web(args["query"])
        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": f"Web search results:\n{result}\n\nPlease answer my original question based on these results."})

        data = await _call({"model": model, "messages": messages})
        if data is None:
            await interaction.followup.send(embed=warn("Groq API error."))
            return None
        return _strip_think(data["choices"][0]["message"]["content"])

    return _strip_think(clean_content or content)


class AI(commands.GroupCog, group_name="ai"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _autocomplete_models(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        current_lower = current.lower()
        return [c for c in MODELS if current_lower in c.name.lower() or current_lower in c.value.lower()][:25]

    @app_commands.command(name="chat", description="Ask Groq AI a question")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(prompt="Your question for the AI", model="Model to use (default: GPT-OSS 120B)")
    @app_commands.autocomplete(model=_autocomplete_models)
    async def chat(self, interaction: discord.Interaction, prompt: str, model: str | None = None):
        if not await check_allowed(interaction):
            return
        await interaction.response.defer()
        content = await _query_groq(interaction, prompt, model or MODEL)
        if content is None:
            return
        embed = discord.Embed(description=content[:4096], color=COLOR)
        embed.set_footer(text=f"Model: {model or MODEL}")
        await interaction.followup.send(embed=embed)

    rules = app_commands.Group(name="rules", description="Manage extra instructions")

    @rules.command(name="list", description="List all rules")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def rules_list(self, interaction: discord.Interaction):
        if not await check_allowed(interaction):
            return
        rules = get_rules()
        if not rules:
            embed = discord.Embed(description="No rules set.", color=COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        lines = "\n".join(f"{i+1}. {r}" for i, r in enumerate(rules))
        embed = discord.Embed(title="AI Rules", description=f"```\n{lines}\n```", color=COLOR)
        embed.set_footer(text="Rules are injected as system messages before every prompt.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @rules.command(name="add", description="Add a rule")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(rule="The rule text to add")
    async def rules_add(self, interaction: discord.Interaction, rule: str):
        if not await check_allowed(interaction):
            return
        add_rule(rule)
        embed = discord.Embed(description=f"Rule added:\n```\n{rule}\n```", color=COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _autocomplete_index(self, interaction: discord.Interaction, current: int) -> list[app_commands.Choice[int]]:
        rules = get_rules()
        choices = []
        for i, r in enumerate(rules):
            label = f"{i+1}. {r[:80]}{'…' if len(r) > 80 else ''}"
            choices.append(app_commands.Choice(name=label, value=i + 1))
        return choices[:25]

    @rules.command(name="remove", description="Remove a rule by number")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.autocomplete(index=_autocomplete_index)
    @app_commands.describe(index="Rule number to remove")
    async def rules_remove(self, interaction: discord.Interaction, index: int):
        if not await check_allowed(interaction):
            return
        removed = remove_rule(index - 1)
        if removed is None:
            await interaction.response.send_message(embed=warn("Invalid rule number. Use `/ai rules list` to see rules."), ephemeral=True)
            return
        embed = discord.Embed(description=f"Rule removed:\n```\n{removed}\n```", color=COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="tools", description="Enable or disable AI web search")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(enabled="Whether web search is enabled")
    async def tools(self, interaction: discord.Interaction, enabled: bool):
        if not await check_allowed(interaction):
            return
        set_tools_enabled(enabled)
        state = "enabled" if enabled else "disabled"
        await interaction.response.send_message(embed=discord.Embed(description=f"Web search {state}.", color=COLOR), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))
