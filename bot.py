import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
import openai
from groq import Groq
import os
import json
import asyncio
import re
import base64
import threading
import requests
import hashlib
import hmac
import logging
import sys
import traceback
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote_plus, parse_qs

# ==============================================================================
# SECTION 1: SYSTEM CONFIGURATION & CONSTANTS
# ==============================================================================
VERSION = "3.2.0-SLASH"
BRAND_NAME = "Maestro Digital Solutions"
DEVELOPER_NAME = "Kaleb McIntosh"
PORTFOLIO_LINK = "https://www.kalebmcintosh.com"
GITHUB_PROJECT_LINK = "https://github.com/MacTheAnon/study-helper"

COLOR_PRIMARY = 0x38bdf8
COLOR_ACCENT = 0xf59e0b
COLOR_SUCCESS = 0x22c55e
COLOR_ERROR = 0xef4444
COLOR_BG = "#0f172a"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler("maestro_monolith.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MaestroCore")

# ==============================================================================
# SECTION 2: DATA PERSISTENCE ENGINE
# ==============================================================================
class PersistenceEngine:
    def __init__(self):
        self.files = {
            "optin": "dm_optin.json",
            "reactions": "role_reactions.json",
            "logs": "admin_audit.json"
        }
        self.dm_optins = self._load_set(self.files["optin"])
        self.role_reactions = self._load_dict(self.files["reactions"])

    def _load_set(self, filepath):
        if not os.path.exists(filepath): return set()
        try:
            with open(filepath, 'r') as f: return set(json.load(f))
        except Exception as e:
            logger.error(f"Failed to load set from {filepath}: {e}")
            return set()

    def _load_dict(self, filepath):
        if not os.path.exists(filepath): return {}
        try:
            with open(filepath, 'r') as f: return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load dict from {filepath}: {e}")
            return {}

    def save_state(self):
        try:
            with open(self.files["optin"], 'w') as f:
                json.dump(list(self.dm_optins), f)
            with open(self.files["reactions"], 'w') as f:
                json.dump(self.role_reactions, f, indent=4)
            logger.info("Persistence: State saved successfully.")
        except Exception as e:
            logger.critical(f"Persistence: SAVE FAILED. Error: {e}")

    def add_optin(self, user_id):
        self.dm_optins.add(str(user_id))
        self.save_state()

    def remove_optin(self, user_id):
        if str(user_id) in self.dm_optins:
            self.dm_optins.remove(str(user_id))
            self.save_state()

    def add_reaction_role(self, msg_id, role_name):
        self.role_reactions[str(msg_id)] = role_name
        self.save_state()

db = PersistenceEngine()

# ==============================================================================
# SECTION 3: KNOWLEDGE BASE IMPORT
# ==============================================================================
try:
    from knowledge import COURSE_NOTES
except ImportError:
    COURSE_NOTES = (
        "No external knowledge.py found. "
        "Topics: Python, Cybersecurity, React, Game Development."
    )

# ==============================================================================
# SECTION 4: AI BRAIN (TRIPLE FAILOVER)
# ==============================================================================
class AIEngine:
    def __init__(self):
        self.k_google = os.getenv("GOOGLE_API_KEY")
        self.k_openai = os.getenv("OPENAI_API_KEY")
        self.k_groq = os.getenv("GROQ_API_KEY")

        if self.k_google:
            genai.configure(api_key=self.k_google)
            self.gemini = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.gemini = None
            logger.warning("Google API Key missing.")

        self.openai = openai.OpenAI(api_key=self.k_openai) if self.k_openai else None
        self.groq = Groq(api_key=self.k_groq) if self.k_groq else None

        self.system_prompt = (
            f"You are Maestro Bot. Version {VERSION}. "
            f"Knowledge Base: {COURSE_NOTES[:2000]}... "
            "Persona: Professor, Architect, Senior Engineer. "
            "If asked to modify server, output ONLY JSON."
        )

    async def query(self, prompt, architect_mode=False):
        final_prompt = f"{self.system_prompt}\n\nUSER: {prompt}"
        if architect_mode:
            final_prompt += "\n\nINSTRUCTION: Output a valid JSON Action Plan."

        try:
            if self.gemini:
                response = self.gemini.generate_content(final_prompt)
                return response.text
        except Exception as e:
            logger.warning(f"Gemini Fail: {e}")

        try:
            if self.openai:
                res = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are Maestro."},
                        {"role": "user", "content": final_prompt}
                    ]
                )
                return res.choices[0].message.content
        except Exception as e:
            logger.warning(f"OpenAI Fail: {e}")

        try:
            if self.groq:
                res = self.groq.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are Maestro."},
                        {"role": "user", "content": final_prompt}
                    ],
                    model="llama3-8b-8192"
                )
                return res.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq Fail: {e}")

        return "❌ CRITICAL: All AI systems are offline. Please check API quotas."

brain = AIEngine()

# ==============================================================================
# SECTION 5: DISCORD BOT CLIENT (WITH SLASH COMMANDS)
# ==============================================================================
class MaestroBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.reactions = True
        super().__init__(command_prefix="!", intents=intents)
        self.active_loop = None

    async def setup_hook(self):
        # FIX: Sync slash commands to a specific guild for instant propagation during dev.
        # To go global (up to 1 hour delay), remove guild= and use: await self.tree.sync()
        guild_id = os.getenv("DEV_GUILD_ID")
        if guild_id:
            guild_obj = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            logger.info(f"Bot Setup Hook: Slash Commands synced to dev guild {guild_id}.")
        else:
            await self.tree.sync()
            logger.info("Bot Setup Hook: Slash Commands synced globally (may take up to 1 hour).")

        self.active_loop = asyncio.get_running_loop()

bot = MaestroBot()


def parse_hex_color(int_color):
    return f"#{int_color:06x}"


async def send_interaction_chunks(interaction: discord.Interaction, text: str):
    """Safe sender for long AI responses in Slash Commands."""
    if not text:
        return
    if len(text) < 2000:
        await interaction.followup.send(text)
    else:
        await interaction.followup.send(text[:1900])
        for i in range(1900, len(text), 1900):
            await interaction.channel.send(text[i:i + 1900])
            await asyncio.sleep(0.5)

# ==============================================================================
# SECTION 6: WEB DASHBOARD & WEBHOOK LISTENER
# ==============================================================================
class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default HTTP access logs to keep our logger clean
        pass

    def check_auth(self):
        user = os.getenv("DASHBOARD_USER", "admin")
        pw = os.getenv("DASHBOARD_PASS", "maestro2026")
        auth_header = self.headers.get('Authorization')
        encoded = base64.b64encode(f"{user}:{pw}".encode()).decode()
        if auth_header != f"Basic {encoded}":
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Maestro Secure"')
            self.end_headers()
            self.wfile.write(b"Unauthorized")
            return False
        return True

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self.get_html(is_admin=False).encode())
        elif self.path.startswith("/admin"):
            if self.check_auth():
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(self.get_html(is_admin=True).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    def do_POST(self):
        # GitHub Webhook
        if self.path == "/github-webhook":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            sig = self.headers.get('X-Hub-Signature-256')
            secret = os.getenv("GITHUB_SECRET")
            if secret and sig:
                mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(sig, f"sha256={mac}"):
                    self.send_response(403)
                    self.end_headers()
                    return
            try:
                payload = json.loads(body)
                if payload.get('action') == 'published' and bot.active_loop:
                    asyncio.run_coroutine_threadsafe(
                        self.broadcast_release(payload['release']), bot.active_loop
                    )
            except Exception as e:
                logger.error(f"Webhook parse error: {e}")
            self.send_response(200)
            self.end_headers()
            return

        # Admin Broadcast
        if self.path == "/broadcast" and self.check_auth():
            length = int(self.headers.get('Content-Length', 0))
            data = parse_qs(self.rfile.read(length).decode())
            msg = data.get('message', [''])[0]
            if msg and bot.active_loop:
                asyncio.run_coroutine_threadsafe(self.broadcast_dm(msg), bot.active_loop)
            self.send_response(303)
            self.send_header('Location', '/admin?sent=1')
            self.end_headers()

    async def broadcast_release(self, release):
        embed = discord.Embed(
            title=f"🚀 New Release: {release['tag_name']}",
            url=release['html_url'],
            color=COLOR_PRIMARY
        )
        embed.description = release.get('body', 'No notes provided.')[:1000]
        for guild in bot.guilds:
            c = discord.utils.get(guild.text_channels, name="announcements") or guild.text_channels[0]
            if c:
                await c.send(embed=embed)

    async def broadcast_dm(self, text):
        count = 0
        for uid in list(db.dm_optins):
            try:
                u = await bot.fetch_user(int(uid))
                await u.send(f"📢 **Maestro Announcement**\n{text}")
                count += 1
                await asyncio.sleep(1)
            except Exception:
                pass
        logger.info(f"Broadcast sent to {count} users.")

    def get_html(self, is_admin):
        stats = f"Users: {len(db.dm_optins)} | Servers: {len(bot.guilds)}"
        admin_panel = f"<a href='/admin' style='color:{parse_hex_color(COLOR_PRIMARY)}'>Admin Login</a>"
        if is_admin:
            admin_panel = f"""
            <div class='card' style='border-top: 4px solid {parse_hex_color(COLOR_ACCENT)};'>
                <h3>📢 Broadcast to Cohort</h3>
                <form action='/broadcast' method='POST'>
                    <textarea name='message' placeholder='Type announcement...' required></textarea>
                    <button type='submit'>Send to All</button>
                </form>
            </div>
            """
        return f"""
        <html><head><style>
            body {{ background: {COLOR_BG}; color: white; font-family: sans-serif; text-align: center; padding: 40px; }}
            .card {{ background: #1e293b; padding: 20px; border-radius: 10px; display: inline-block; text-align: left; min-width: 300px; }}
            textarea {{ width: 100%; height: 100px; background: #0f172a; color: white; border: 1px solid #334155; margin: 10px 0; }}
            button {{ background: {parse_hex_color(COLOR_PRIMARY)}; border: none; padding: 10px; width: 100%; cursor: pointer; font-weight: bold; color: white; }}
        </style></head><body>
            <div class='card'>
                <h1>Maestro OS</h1>
                <p>{stats}</p>
                {admin_panel}
            </div>
        </body></html>
        """

# ==============================================================================
# SECTION 7: EVENT LISTENERS
# ==============================================================================
@bot.event
async def on_ready():
    logger.info(f"Discord: Online as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="/help | v3.2"))

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="FebruaryCohort")
    if role:
        try:
            await member.add_roles(role)
        except Exception:
            logger.error(f"Failed to assign role to {member.name}")
    msg = (
        f"👋 Welcome to the cohort, {member.name}!\n"
        "Type `/help` in the server to get started.\n"
        "Use `/optin` if you want DM alerts."
    )
    try:
        await member.send(msg)
    except Exception:
        pass

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    mid = str(payload.message_id)
    if mid in db.role_reactions:
        guild = bot.get_guild(payload.guild_id)
        role = discord.utils.get(guild.roles, name=db.role_reactions[mid])
        member = payload.member or guild.get_member(payload.user_id)
        if role and member:
            await member.add_roles(role)
            logger.info(f"Role {role.name} given to {member.name}")

@bot.event
async def on_raw_reaction_remove(payload):
    mid = str(payload.message_id)
    if mid in db.role_reactions:
        guild = bot.get_guild(payload.guild_id)
        role = discord.utils.get(guild.roles, name=db.role_reactions[mid])
        member = guild.get_member(payload.user_id)
        if role and member:
            await member.remove_roles(role)
            logger.info(f"Role {role.name} removed from {member.name}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # FIX: process_commands is still needed for any future prefix commands
    await bot.process_commands(message)

    # Architect Mode / AI chat via mention
    if bot.user.mentioned_in(message):
        is_admin = message.author.guild_permissions.administrator
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            return

        if is_admin:
            async with message.channel.typing():
                # Always query as normal chat first.
                # Only execute as Architect if the AI explicitly returns a JSON block with actions.
                response = await brain.query(prompt)

                if "```json" in response:
                    try:
                        clean_json = response.split("```json")[1].split("```")[0].strip()
                        plan = json.loads(clean_json)
                        actions = plan.get('actions', [])

                        if not actions:
                            # Valid JSON but no actions — just show the response as text
                            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                            for chunk in chunks:
                                await message.channel.send(chunk)
                            return

                        # Confirm with the admin before executing
                        confirm_msg = await message.channel.send(
                            f"🏗️ **Architect Plan: {plan.get('plan_name', 'Unnamed')}**\n"
                            f"This will perform **{len(actions)} action(s)** on the server.\n"
                            f"React ✅ to confirm or ❌ to cancel."
                        )
                        await confirm_msg.add_reaction("✅")
                        await confirm_msg.add_reaction("❌")

                        def check(reaction, user):
                            return (
                                user == message.author
                                and str(reaction.emoji) in ["✅", "❌"]
                                and reaction.message.id == confirm_msg.id
                            )

                        try:
                            reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check)
                        except asyncio.TimeoutError:
                            await message.channel.send("⏱️ Architect plan timed out. No changes were made.")
                            return

                        if str(reaction.emoji) == "❌":
                            await message.channel.send("🚫 Architect plan cancelled.")
                            return

                        # Execute actions
                        for action in actions:
                            atype = action.get('type')
                            aname = action.get('name')
                            if atype == 'create_role':
                                await message.guild.create_role(
                                    name=aname,
                                    color=discord.Color.from_str(action.get('color', '#99aab5'))
                                )
                                await message.channel.send(f"🔹 Created Role: **{aname}**")
                            elif atype == 'create_text':
                                cat = discord.utils.get(message.guild.categories, name=action.get('category'))
                                await message.guild.create_text_channel(aname, category=cat)
                                await message.channel.send(f"🔹 Created Channel: **{aname}**")
                            elif atype == 'create_category':
                                await message.guild.create_category(aname)
                                await message.channel.send(f"🔹 Created Category: **{aname}**")

                        await message.channel.send("✅ **Execution Complete.**")

                    except Exception as e:
                        await message.channel.send(f"⚠️ **Architect Malfunction:** {e}")
                else:
                    # Plain text response — just send it normally
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    for chunk in chunks:
                        await message.channel.send(chunk)
        else:
            async with message.channel.typing():
                res = await brain.query(prompt)
                chunks = [res[i:i+2000] for i in range(0, len(res), 2000)]
                for chunk in chunks:
                    await message.channel.send(chunk)

# ==============================================================================
# SECTION 8: SLASH COMMANDS
# ==============================================================================

# --- HELP ---
@bot.tree.command(name="help", description="View all Maestro commands")
async def cmd_help(interaction: discord.Interaction):
    is_admin = interaction.user.guild_permissions.administrator
    embed = discord.Embed(title="Maestro Command Suite", color=COLOR_PRIMARY)
    embed.add_field(
        name="🎓 Education",
        value="`/ask`, `/review`, `/yt`, `/resource`, `/flashcard`, `/studygroup`",
        inline=False
    )
    embed.add_field(
        name="🛠️ Utilities",
        value="`/poll`, `/remindme`, `/dev`, `/studyhelper`, `/challenge`",
        inline=False
    )
    embed.add_field(
        name="👥 Community",
        value="`/optin`, `/optout`, `/earn`",
        inline=False
    )
    if is_admin:
        embed.add_field(
            name="🛡️ Admin",
            value="`/kick`, `/ban`, `/make_role`, `/announce`, `/dmall`, `/dmtouser`, `/setup_py101`, `/setup_private_role`, `/post_in`",
            inline=False
        )
    embed.set_footer(text=f"Maestro v{VERSION} | {BRAND_NAME}")
    await interaction.response.send_message(embed=embed)

# --- MODERATION ---
@bot.tree.command(name="kick", description="Kick a member from the server")
@app_commands.default_permissions(kick_members=True)
async def cmd_kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"👞 **Kicked:** {member.mention} | Reason: {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to kick that member.", ephemeral=True)

@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.default_permissions(ban_members=True)
async def cmd_ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"🔨 **Banned:** {member.mention} | Reason: {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to ban that member.", ephemeral=True)

# --- COMMUNITY & UTILITY ---
@bot.tree.command(name="optin", description="Opt into DM announcements")
async def cmd_optin(interaction: discord.Interaction):
    db.add_optin(interaction.user.id)
    await interaction.response.send_message("✅ You've been added to the broadcast list.", ephemeral=True)

@bot.tree.command(name="optout", description="Opt out of DM announcements")
async def cmd_optout(interaction: discord.Interaction):
    db.remove_optin(interaction.user.id)
    await interaction.response.send_message("✅ You've been removed from the broadcast list.", ephemeral=True)

@bot.tree.command(name="dev", description="View developer profile")
async def cmd_dev(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Developer Profile",
        description=f"**{DEVELOPER_NAME}**\nFull Stack Engineer & Entrepreneur.\n[Portfolio]({PORTFOLIO_LINK})",
        color=COLOR_ACCENT
    )
    embed.set_thumbnail(url="https://github.com/MacTheAnon.png")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="studyhelper", description="Get info on the Study Helper repo")
async def cmd_studyhelper(interaction: discord.Interaction):
    await interaction.response.defer()
    # FIX: Was incorrectly wrapped in markdown link syntax in v3.2 draft
    raw_url = "https://raw.githubusercontent.com/MacTheAnon/study-helper/main/README.md"
    try:
        r = requests.get(raw_url, timeout=10)
        text = r.text if r.status_code == 200 else "README unavailable."
        content = f"🚀 **Study Helper Tool**\n🔗 <{GITHUB_PROJECT_LINK}>\n\n{text}"
        await send_interaction_chunks(interaction, content)
    except Exception as e:
        await interaction.followup.send(f"⚠️ Error fetching data: {e}")

@bot.tree.command(name="poll", description="Create a poll (2–10 options, comma-separated)")
async def cmd_poll(interaction: discord.Interaction, question: str, options_comma_separated: str):
    options = [opt.strip() for opt in options_comma_separated.split(",")]
    if len(options) < 2 or len(options) > 10:
        return await interaction.response.send_message(
            "❌ Provide between 2 and 10 comma-separated options.", ephemeral=True
        )

    desc = ""
    for i, opt in enumerate(options):
        desc += f"{chr(0x1F1E6 + i)} {opt}\n"

    embed = discord.Embed(title=f"📊 {question}", description=desc, color=COLOR_SUCCESS)
    await interaction.response.send_message("✅ Poll created!")
    msg = await interaction.channel.send(embed=embed)
    for i in range(len(options)):
        await msg.add_reaction(chr(0x1F1E6 + i))

@bot.tree.command(name="remindme", description="Set a reminder (e.g. duration: 5m or 1h)")
async def cmd_remindme(interaction: discord.Interaction, duration: str, task: str):
    match = re.match(r"(\d+)([mh])", duration.lower())
    if not match:
        return await interaction.response.send_message(
            "❌ Invalid duration format. Use '5m' for minutes or '1h' for hours.", ephemeral=True
        )

    val, unit = match.groups()
    secs = int(val) * (60 if unit == 'm' else 3600)
    await interaction.response.send_message(f"⏰ Timer set for {val}{unit}. I'll remind you!")

    async def reminder_task():
        await asyncio.sleep(secs)
        try:
            await interaction.channel.send(f"🔔 **Reminder:** {interaction.user.mention} — {task}")
        except Exception as e:
            logger.warning(f"Reminder send failed: {e}")

    bot.loop.create_task(reminder_task())

@bot.tree.command(name="studygroup", description="Create a private study group channel")
async def cmd_studygroup(interaction: discord.Interaction):
    cat = discord.utils.get(interaction.guild.categories, name="Study Groups")
    if not cat:
        cat = await interaction.guild.create_category("Study Groups")

    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True)
    }
    safe_name = re.sub(r'[^a-z0-9-]', '', interaction.user.name.lower().replace(' ', '-'))
    chan = await interaction.guild.create_text_channel(
        f"group-{safe_name}", category=cat, overwrites=overwrites
    )
    await interaction.response.send_message(f"✅ Created your study group: {chan.mention}")

# --- AI & LEARNING TOOLS ---
@bot.tree.command(name="challenge", description="Generate a daily coding challenge")
async def cmd_challenge(interaction: discord.Interaction):
    await interaction.response.defer()
    res = await brain.query(
        "Generate a beginner Python coding challenge. No code solution, just the problem description."
    )
    await interaction.followup.send(f"🧩 **Daily Challenge**\n{res}")

@bot.tree.command(name="earn", description="Earn the Python Learner badge")
async def cmd_earn(interaction: discord.Interaction):
    role_name = "Python Learner"
    role = discord.utils.get(interaction.guild.roles, name=role_name)
    if not role:
        try:
            role = await interaction.guild.create_role(name=role_name, color=discord.Color.gold())
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ Missing permissions to create role.", ephemeral=True
            )
    try:
        await interaction.user.add_roles(role)
        await interaction.response.send_message(
            f"🏆 {interaction.user.mention} has earned the **{role_name}** badge!"
        )
    except discord.Forbidden:
        await interaction.response.send_message("❌ Missing permissions to assign role.", ephemeral=True)

@bot.tree.command(name="flashcard", description="Generate a flashcard on a topic")
async def cmd_flashcard(interaction: discord.Interaction, topic: str = "Python"):
    await interaction.response.defer()
    res = await brain.query(
        f"Create a flashcard for {topic}. Format: Question: [Q] || Answer: [A]."
    )
    if "||" in res:
        q, a = res.split("||", 1)
        try:
            await interaction.user.send(f"❓ **Flashcard ({topic})**\n{q.strip()}\n\n✅ **Answer:**\n{a.strip()}")
            await interaction.followup.send("📩 Check your DMs for your flashcard!")
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I couldn't DM you. Please check your privacy settings and try again."
            )
    else:
        await interaction.followup.send(res)

@bot.tree.command(name="ask", description="Ask Maestro a question")
async def cmd_ask(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    response = await brain.query(query)
    await send_interaction_chunks(interaction, response)

@bot.tree.command(name="review", description="Submit code for Maestro to review")
async def cmd_review(interaction: discord.Interaction, code: str):
    await interaction.response.defer()
    response = await brain.query(f"Review this code for bugs and improvements:\n{code}")
    await send_interaction_chunks(interaction, response)

@bot.tree.command(name="yt", description="Get a high-quality YouTube tutorial recommendation")
async def cmd_yt(interaction: discord.Interaction, topic: str):
    await interaction.response.defer()
    response = await brain.query(
        f"Provide one high-quality YouTube URL for learning: {topic}. Output ONLY the URL."
    )
    await interaction.followup.send(f"📺 **Maestro Pick:** {response}")

@bot.tree.command(name="resource", description="Get 3 free learning resources on a topic")
async def cmd_resource(interaction: discord.Interaction, topic: str):
    await interaction.response.defer()
    res = await brain.query(f"List 3 free learning resources for {topic} with URLs.")
    await send_interaction_chunks(interaction, res)

# --- ADMIN COMMANDS ---
@bot.tree.command(name="setup_py101", description="Initialize PY101 Course Structure")
@app_commands.default_permissions(administrator=True)
async def cmd_setup_py101(interaction: discord.Interaction):
    await interaction.response.defer()
    cat = await interaction.guild.create_category("PY101 - Python")
    await interaction.guild.create_text_channel("syllabus", category=cat)
    await interaction.guild.create_text_channel("homework-help", category=cat)
    res_chan = await interaction.guild.create_text_channel("resources", category=cat)
    await res_chan.send(f"📚 **Course Notes:**\n{COURSE_NOTES[:1500]}")
    await interaction.followup.send("✅ PY101 Course Environment is ready.")

@bot.tree.command(name="make_role", description="Create a new server role")
@app_commands.default_permissions(manage_roles=True)
async def cmd_make_role(interaction: discord.Interaction, name: str, hex_color: str = "#99AAB5"):
    try:
        color = discord.Color.from_str(hex_color)
        await interaction.guild.create_role(name=name, color=color)
        await interaction.response.send_message(f"✅ Role **{name}** created.")
    except ValueError:
        await interaction.response.send_message(
            "❌ Invalid hex color. Use format `#RRGGBB` (e.g. `#FF5733`).", ephemeral=True
        )

@bot.tree.command(name="announce", description="Post an embedded announcement in the current channel")
@app_commands.default_permissions(administrator=True)
async def cmd_announce(interaction: discord.Interaction, title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=COLOR_ACCENT)
    await interaction.response.send_message("✅ Announcement posted.", ephemeral=True)
    await interaction.channel.send(embed=embed)

@bot.tree.command(name="post_in", description="Post a message to a specific channel")
@app_commands.default_permissions(administrator=True)
async def cmd_post_in(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    try:
        await channel.send(message)
        await interaction.response.send_message(f"✅ Posted in {channel.mention}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(
            f"❌ I don't have permission to post in {channel.mention}.", ephemeral=True
        )

@bot.tree.command(name="dmall", description="Send a DM to all opted-in users")
@app_commands.default_permissions(administrator=True)
async def cmd_dmall(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for uid in list(db.dm_optins):
        try:
            u = await bot.fetch_user(int(uid))
            await u.send(f"🚨 **Admin Notice:** {message}")
            count += 1
            await asyncio.sleep(0.5)  # Rate limit safety
        except Exception:
            pass
    await interaction.followup.send(f"✅ Sent to {count} users.")

@bot.tree.command(name="dmtouser", description="Send a DM to a specific user")
@app_commands.default_permissions(administrator=True)
async def cmd_dmtouser(interaction: discord.Interaction, user: discord.Member, message: str):
    try:
        await user.send(f"📩 **Message from Admin:** {message}")
        await interaction.response.send_message(f"✅ Sent to {user.mention}.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Could not DM that user — their privacy settings may be blocking it.", ephemeral=True
        )

@bot.tree.command(name="setup_private_role", description="Create a private role, channel, and reaction gate")
@app_commands.default_permissions(administrator=True)
async def cmd_setup_private_role(
    interaction: discord.Interaction,
    role_name: str,
    category_name: str,
    channel_name: str,
    emoji: str,
    description: str
):
    await interaction.response.defer()
    try:
        # 1. Role
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role:
            role = await interaction.guild.create_role(name=role_name)

        # 2. Permissions
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(view_channel=True)
        }

        # 3. Category & Channel
        cat = discord.utils.get(interaction.guild.categories, name=category_name)
        if not cat:
            cat = await interaction.guild.create_category(category_name, overwrites=overwrites)

        chan = await interaction.guild.create_text_channel(channel_name, category=cat, overwrites=overwrites)
        await chan.send(f"**Welcome to {role_name}!**\n{description}")

        # 4. Reaction Gate
        gate_chan = discord.utils.get(interaction.guild.text_channels, name="get-roles")
        if gate_chan:
            gate_msg = await gate_chan.send(f"{emoji} React here to join **{role_name}**")
            await gate_msg.add_reaction(emoji)
            db.add_reaction_role(gate_msg.id, role_name)
            await interaction.followup.send(
                f"✅ Private ecosystem created for **{role_name}**. Reaction gate posted in {gate_chan.mention}."
            )
        else:
            await interaction.followup.send(
                f"✅ Private ecosystem created for **{role_name}**.\n"
                "⚠️ No `#get-roles` channel found — reaction gate was not posted."
            )
    except Exception as e:
        logger.error(f"setup_private_role error: {e}")
        await interaction.followup.send(f"❌ Setup Error: {e}")

# ==============================================================================
# SECTION 9: SYSTEM ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DashboardHandler)

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    logger.info(f"System: Dashboard active on port {port}")

    token = os.getenv("DISCORD_TOKEN")
    if token:
        try:
            bot.run(token)
        except Exception as e:
            logger.critical(f"System: Bot Crash: {e}")
            traceback.print_exc()
    else:
        logger.critical("System: DISCORD_TOKEN missing from environment. Bot cannot start.")
