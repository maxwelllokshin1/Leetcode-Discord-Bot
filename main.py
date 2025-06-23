import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import random
import re
import asyncio
import headless_leetcode as ltl
import time

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

prefix = '.'

bot = commands.Bot(command_prefix=prefix, intents=intents)

monkeyLang = ["oo oog o og oogg", "ooogooo oogog oogg", "I am the supernatural being", "o ooh oo goo ohh oo", "BANANA", "I WANT BANANA"]
keyWords = ["the", "monkey", "thinking", "question", "hi", "hello"]

@bot.event
async def on_ready():
    # bot.add_view(LoginView())
    print(f"{bot.user.name} is online")
    
@bot.command()
async def cmd(ctx):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="🙊🐵COMMAND LIST🙈🙉",
            color=discord.Color.from_rgb(255, 255, 255)
        )
        embed.add_field(name=f"{prefix}Leetcode", value="🧾 Leetcode commands", inline=False)
        embed.add_field(name=f"{prefix}Utility", value="⚙️ Utilities all users can use", inline=False)
        embed.add_field(name=f"{prefix}Admin", value="👤 Admin commands", inline=False)

        await ctx.send(embed=embed)
    
@bot.event
async def msg(msg):
    if msg.author == bot.user:
        return
    
    pattern = r'\b(?:' + '|'.join(re.escape(word) for word in keyWords) + r')\b'
    if re.search(pattern, msg.content.lower()):
        await msg.channel.send(monkeyLang[random.randint(1, len(monkeyLang))])

# """-----------------------LEETCODE COMMANDS-----------------------"""

@bot.group()
async def Leetcode(ctx):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="🧾 LeetCode Commands",
            description="All commands must be written as **.Leetcode {command}**",
            color=discord.Color.from_rgb(255, 255, 255)
        )
        embed.add_field(name="login", value="🔓 Login to leetcode", inline=False)
        embed.add_field(name="problems", value="📝 Present all leetcode problems", inline=False)
        embed.add_field(name="daily", value="☀️ View the daily leetcode problem", inline=False)
        embed.add_field(name="reset", value="♻️ Resets the users login", inline=False)
        embed.add_field(name="account", value="👤 View amount of problems completed", inline=False)

        await ctx.send(embed=embed)

@Leetcode.command()
async def login(ctx):
    try:
        await ctx.send("📫We sent you a message in **DM'S** for you to enter your info...")
        def check(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)
            # Wait for username
            # prompt1 = await ctx.author.send("👤**Username**:")
            # user_msg = await bot.wait_for('message', check=check, timeout=60)
            # username = user_msg.content
        status = await ctx.author.send("🔐 Opening browser. Please login...")
        time.sleep(1)

        # run login flow in separate thread avoiding blocking the bot
        loop = asyncio.get_running_loop()
        message = await loop.run_in_executor(None, ltl.login, ctx.author.id)

        await status.edit(content=message)
        return
    except discord.Forbidden:
        await ctx.send("❌ CANNOT send DM's. Check privacy settings")

@Leetcode.command()
async def daily(ctx):
    try:
        msg = await ctx.send("🍌 Fetching daily problem...")

        # Run in background
        loop = asyncio.get_running_loop()
        link = await loop.run_in_executor(None, ltl.problem, True)
        embed = await embed_set(0, link[0], link, False, "☀️ DAILY PROBLEM")
        await msg.edit(embed=embed)
        return
    except discord.Forbidden:
        await ctx.send("❌ CANNOT send DM's. Check privacy settings")
    except Exception as e:
        print(f"Unexpected error: {e}")
        await ctx.send("❌ Something went wrong while fetching your problems.")

@Leetcode.command()
async def problems(ctx):
    try:
        msg = await ctx.send("🍌 Fetching top 100 probelms...")

        # Notify in DM

        # Run in background
        loop = asyncio.get_running_loop()
        all_links = await loop.run_in_executor(None, ltl.problem, False)

        if all_links != None:
            current_page = 0
            await msg.edit(embed=await embed_set(current_page, all_links[current_page], all_links, True, "🧾 LeetCode Problems"))

            # Add reactions
            await msg.add_reaction("⬅️")
            await msg.add_reaction("➡️")

            def check(reaction, user):
                return (
                    user == ctx.author
                    and reaction.message.id == msg.id
                    and str(reaction.emoji) in ["⬅️", "➡️"]
                )

            while True:
                try:
                    reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
                    # Remove reaction to keep it clean
                    await msg.remove_reaction(reaction, user)

                    if str(reaction.emoji) == "➡️" and current_page < len(all_links) - 1:
                        current_page += 1
                        await msg.edit(embed=await embed_set(current_page, all_links[current_page], all_links, True, "🧾 LeetCode Problems"))
                    elif str(reaction.emoji) == "⬅️" and current_page > 0:
                        current_page -= 1
                        await msg.edit(embed=await embed_set(current_page, all_links[current_page], all_links, True, "🧾 LeetCode Problems"))

                except asyncio.TimeoutError:
                    # Disable interaction after timeout
                    await msg.clear_reactions()
                    break
        return 
    except discord.Forbidden:
        await ctx.send("❌ CANNOT send DM's. Check privacy settings")
    except Exception as e:
        print(f"Unexpected error: {e}")
        await ctx.send("❌ Something went wrong while fetching your problems.")

async def embed_set(current_page, links, all_links, footer, title):
    embed = discord.Embed(
        title=f" {title} (Page {current_page + 1}/{len(all_links)})",
        color=discord.Color.from_rgb(0, 255, 0)
    )

    for link in links:
        if not link["Links"]:
            continue
        embed.add_field(
            name=link["Name"], 
            value=f"[Go to problem](https://leetcode.com{link['Links']})", 
            inline=False
        )
    if footer:
        embed.set_footer(text="Use ⬅️ ➡️ to navigate pages.")
    return embed

@Leetcode.command()
async def account(ctx):
    try:
        status = await ctx.send("👤 Here are your account detials...")
        loop = asyncio.get_running_loop()
        message = await loop.run_in_executor(None, ltl.account, ctx.author.id)
        # await ctx.send("Here’s an image:", file=discord.File("path/to/local/image.png"))

        await status.edit(content=message)
        await ctx.send(file=discord.File(f"{ctx.author.id}_stats.png"))
        if os.path.exists(f"{ctx.author.id}_stats.png"):
            os.remove(f"{ctx.author.id}_stats.png")
        return
    except discord.Forbidden:
        await ctx.send("❌ CANNOT send DM's. Check privacy settings")

@Leetcode.command()
async def reset(ctx):
    try:
        await ctx.send("📫We sent you a message in **DM'S**")

        def check(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)
        
        status = await ctx.author.send("🔐 Opening browser. Please login...")
        time.sleep(1)

        message = await asyncio.to_thread(ltl.reset_login, str(ctx.author.id))
        await status.edit(content=message)
        return
    except discord.Forbidden:
        await ctx.send("❌ CANNOT send DM's. Check privacy settings")

# """-----------------------UTILITY COMMANDS-----------------------""" 

@bot.group()
async def Utility(ctx):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="⚙️ Utility Commands",
            description="All commands must be written as **.Utility {command}**",
            color=discord.Color.from_rgb(255, 255, 255)
        )
        embed.add_field(name="clear", value="🗑️ Clears bots messages in dms", inline=False)

        await ctx.send(embed=embed)

async def delete_bot_messages_in_dm(user, bot):
    dm = await user.create_dm()
    async for message in dm.history(limit=100): 
        if message.author == bot.user:
            try:
                await message.delete()
            except discord.Forbidden:
                print("❌ Cannot delete a message (permissions).")
            except discord.HTTPException:
                print("⚠️ Failed to delete message (likely too old).")

@Utility.command()
async def clear(ctx):
    status = await ctx.send("Cleaning up DM messages...")
    await delete_bot_messages_in_dm(ctx.author, bot)
    status.edit(content="✅ Done")

# """-----------------------ADMIN COMMANDS-----------------------"""

@bot.group()
async def Admin(ctx):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="👤 Admin Commands",
            description="All commands must be written as **.Admin {command}**",
            color=discord.Color.from_rgb(255, 255, 255)
        )
        embed.add_field(name="nuke", value="💣 Nuke whole chat (use in limited cases)", inline=False)

        await ctx.send(embed=embed)

@Admin.command()
async def nuke(ctx):
    await ctx.send("🧨 **NUKING THE CHANNEL...**")
    deleted = 0
    try: 
        async for msg in ctx.channel.history(limit=None):
            try:
                await msg.delete()
                deleted += 1
            except Exception as e:
                print(f"Could not delete: {e}")
    except Exception as e:
        await ctx.send(f"❌ Failed {e}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)