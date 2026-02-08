import discord
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
VERSION = "3.1.0-STABLE"
BRAND_NAME = "Maestro Digital Solutions"
DEVELOPER_NAME = "Kaleb McIntosh"
PORTFOLIO_LINK = "https://www.kalebmcintosh.com"
GITHUB_PROJECT_LINK = "https://github.com/MacTheAnon/study-helper"

# Brand Palette
COLOR_PRIMARY = 0x38bdf8  # Cyber Cyan
COLOR_ACCENT = 0xf59e0b   # Executive Gold
COLOR_SUCCESS = 0x22c55e  # Green
COLOR_ERROR = 0xef4444    # Red
COLOR_BG = "#0f172a"      # Navy Slate

# Logging Setup
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
    """
    Manages all local JSON storage with robust error handling and backups.
    Ensures data survives Render's restart cycles.
    """
    def __init__(self):
        self.files = {
            "optin": "dm_optin.json",
            "reactions": "role_reactions.json",
            "logs": "admin_audit.json"
        }
        self.dm_optins = self._load_set(self.files["optin"])
        self.role_reactions = self._load_dict(self.files["reactions"])

    def _load_set(self, filepath):
        if not os.path.exists(filepath):
            return set()
        try:
            with open(filepath, 'r') as f:
                return set(json.load(f))
        except Exception as e:
            logger.error(f"Failed to load set from {filepath}: {e}")
            return set()

    def _load_dict(self, filepath):
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load dict from {filepath}: {e}")
            return {}

    def save_state(self):
        """Commits all in-memory data to disk."""
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
        # Load Keys
        self.k_google = os.getenv("GOOGLE_API_KEY")
        self.k_openai = os.getenv("OPENAI_API_KEY")
        self.k_groq = os.getenv("GROQ_API_KEY")
        
        # Init Google
        if self.k_google:
            genai.configure(api_key=self.k_google)
            self.gemini = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.gemini = None
            logger.warning("Google API Key missing.")
        
        # Init OpenAI
        self.openai = openai.OpenAI(api_key=self.k_openai) if self.k_openai else None
        
        # Init Groq
        self.groq = Groq(api_key=self.k_groq) if self.k_groq else None

        self.system_prompt = (
            f"You are Maestro Bot. Version {VERSION}. "
            f"Knowledge Base: {COURSE_NOTES[:2000]}... " # Truncate to save context
            "Persona: Professor, Architect, Senior Engineer. "
            "If asked to modify server, output ONLY JSON."
        )

    async def query(self, prompt, architect_mode=False):
        final_prompt = f"{self.system_prompt}\n\nUSER: {prompt}"
        if architect_mode:
            final_prompt += "\n\nINSTRUCTION: Output a valid JSON Action Plan."

        # Attempt 1: Gemini
        try:
            if self.gemini:
                response = self.gemini.generate_content(final_prompt)
                return response.text
        except Exception as e:
            logger.warning(f"Gemini Fail: {e}")

        # Attempt 2: OpenAI
        try:
            if self.openai:
                res = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "You are Maestro."}, {"role": "user", "content": final_prompt}]
                )
                return res.choices[0].message.content
        except Exception as e:
            logger.warning(f"OpenAI Fail: {e}")

        # Attempt 3: Groq
        try:
            if self.groq:
                res = self.groq.chat.completions.create(
                    messages=[{"role": "system", "content": "You are Maestro."}, {"role": "user", "content": final_prompt}],
                    model="llama3-8b-8192"
                )
                return res.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq Fail: {e}")

        return "❌ CRITICAL: All AI systems are offline. Please check API quotas."

brain = AIEngine()

# ==============================================================================
# SECTION 5: WEB DASHBOARD & WEBHOOK LISTENER
# ==============================================================================
class DashboardHandler(BaseHTTPRequestHandler):
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
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
            self.wfile.write(self.get_html(is_admin=False).encode())
        elif self.path == "/admin":
            if self.check_auth():
                self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
                self.wfile.write(self.get_html(is_admin=True).encode())
        elif self.path == "/health":
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK")

    def do_POST(self):
        # GitHub Webhook
        if self.path == "/github-webhook":
            length = int(self.headers['Content-Length'])
            body = self.rfile.read(length)
            sig = self.headers.get('X-Hub-Signature-256')
            secret = os.getenv("GITHUB_SECRET")
            if secret and sig:
                mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(sig, f"sha256={mac}"):
                    self.send_response(403); self.end_headers(); return
            
            payload = json.loads(body)
            if payload.get('action') == 'published':
                asyncio.run_coroutine_threadsafe(self.broadcast_release(payload['release']), bot.loop)
            self.send_response(200); self.end_headers(); return

        # Admin Broadcast
        if self.path == "/broadcast" and self.check_auth():
            length = int(self.headers['Content-Length'])
            data = parse_qs(self.rfile.read(length).decode())
            msg = data.get('message', [''])[0]
            if msg:
                asyncio.run_coroutine_threadsafe(self.broadcast_dm(msg), bot.loop)
            self.send_response(303); self.send_header('Location', '/admin?sent=1'); self.end_headers()

    async def broadcast_release(self, release):
        embed = discord.Embed(title=f"🚀 New Release: {release['tag_name']}", url=release['html_url'], color=COLOR_PRIMARY)
        embed.description = release.get('body', 'No notes provided.')[:1000]
        for guild in bot.guilds:
            c = discord.utils.get(guild.text_channels, name="announcements") or guild.text_channels[0]
            if c: await c.send(embed=embed)

    async def broadcast_dm(self, text):
        count = 0
        for uid in list(db.dm_optins):
            try:
                u = await bot.fetch_user(int(uid))
                await u.send(f"📢 **Maestro Announcement**\n{text}")
                count += 1
                await asyncio.sleep(1)
            except: pass
        logger.info(f"Broadcast sent to {count} users.")

    def get_html(self, is_admin):
        stats = f"Users: {len(db.dm_optins)} | Servers: {len(bot.guilds)}"
        admin_panel = ""
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
        else:
            admin_panel = f"<a href='/admin' style='color:{parse_hex_color(COLOR_PRIMARY)}'>Admin Login</a>"
            
        return f"""
        <html><head><style>
            body {{ background: {COLOR_BG}; color: white; font-family: sans-serif; text-align: center; padding: 40px; }}
            .card {{ background: #1e293b; padding: 20px; border-radius: 10px; display: inline-block; text-align: left; min-width: 300px; }}
            textarea {{ width: 100%; height: 100px; background: #0f172a; color: white; border: 1px solid #334155; margin: 10px 0; }}
            button {{ background: {parse_hex_color(COLOR_PRIMARY)}; border: none; padding: 10px; width: 100%; cursor: pointer; font-weight: bold; }}
        </style></head><body>
            <div class='card'>
                <h1>Maestro OS</h1>
                <p>{stats}</p>
                {admin_panel}
            </div>
        </body></html>
        """

def parse_hex_color(int_color):
    return f"#{int_color:06x}"

# ==============================================================================
# SECTION 6: DISCORD BOT CLIENT
# ==============================================================================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True
bot = discord.Client(intents=intents)

async def send_chunks(channel, text):
    """Safe sender for long AI responses."""
    if not text:
        return
    if len(text) < 2000:
        await channel.send(text)
    else:
        for i in range(0, len(text), 1900):
            await channel.send(text[i:i+1900])
            await asyncio.sleep(0.5)

@bot.event
async def on_ready():
    logger.info(f"Discord: Online as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!help | v3.1"))

@bot.event
async def on_member_join(member):
    # 1. Role Assignment
    role = discord.utils.get(member.guild.roles, name="FebruaryCohort")
    if role:
        try: await member.add_roles(role)
        except: logger.error(f"Failed to assign role to {member.name}")
    
    # 2. Welcome DM
    msg = (f"👋 Welcome to the cohort, {member.name}!\n"
           "Type `!help` in the server to get started.\n"
           "Reply with `!optin` if you want DM alerts.")
    try: await member.send(msg)
    except: pass

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id: return
    mid = str(payload.message_id)
    
    # Check persistent role reactions
    if mid in db.role_reactions:
        guild = bot.get_guild(payload.guild_id)
        role = discord.utils.get(guild.roles, name=db.role_reactions[mid])
        member = payload.member or guild.get_member(payload.user_id)
        if role and member: 
            await member.add_roles(role)
            logger.info(f"Role {role.name} given to {member.name}")
            
    # Legacy hardcoded checks (e.g. YouTube bell) can be added here if needed

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

# ==============================================================================
# SECTION 7: COMMAND HANDLER (THE MONOLITH)
# ==============================================================================
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    content = message.content.strip()
    cmd = content.lower().split(" ")[0]
    is_admin = message.author.guild_permissions.administrator

    # --------------------------------------------------------------------------
    # GROUP A: COMMUNITY & UTILITY COMMANDS
    # --------------------------------------------------------------------------
    if cmd == "!help":
        embed = discord.Embed(title="Maestro Command Suite", color=COLOR_PRIMARY)
        embed.add_field(name="🎓 Education", value="`!ask`, `!review`, `!yt`, `!resource`, `!flashcard`", inline=False)
        embed.add_field(name="🛠️ Utilities", value="`!poll`, `!remindme`, `!dev`, `!studyhelper`", inline=False)
        embed.add_field(name="👥 Community", value="`!optin`, `!optout`, `!earn`, `!challenge`", inline=False)
        if is_admin:
            embed.add_field(name="🛡️ Admin", value="`!announce`, `!dmall`, `!setup_private_role`, `!setup_py101`, `!post_in`", inline=False)
        await message.channel.send(embed=embed)

    elif cmd == "!optin":
        db.add_optin(message.author.id)
        await message.channel.send(f"✅ {message.author.mention} added to broadcast list.")

    elif cmd == "!optout":
        db.remove_optin(message.author.id)
        await message.channel.send(f"✅ {message.author.mention} removed from broadcast list.")

    elif cmd == "!dev":
        embed = discord.Embed(title="Developer Profile", color=COLOR_ACCENT)
        embed.description = f"**{DEVELOPER_NAME}**\nFull Stack Engineer & Entrepreneur.\n[Portfolio]({PORTFOLIO_LINK})"
        embed.set_thumbnail(url="https://github.com/MacTheAnon.png")
        await message.channel.send(embed=embed)

    elif cmd == "!studyhelper":
        # Pulls from GitHub as requested
        repo = GITHUB_PROJECT_LINK
        raw_url = "https://raw.githubusercontent.com/MacTheAnon/study-helper/main/README.md"
        async with message.channel.typing():
            try:
                r = requests.get(raw_url)
                text = r.text if r.status_code == 200 else "README unavailable."
                await send_chunks(message.channel, f"🚀 **Study Helper Tool**\n🔗 <{repo}>\n\n" + text)
            except Exception as e:
                await message.channel.send(f"⚠️ Error fetching data: {e}")

    elif cmd == "!poll":
        # Format: !poll Question | Opt1 | Opt2
        try:
            parts = content[6:].split("|")
            question = parts[0].strip()
            options = [x.strip() for x in parts[1:]]
            if len(options) < 2: raise ValueError
            
            desc = ""
            for i, opt in enumerate(options):
                desc += f"{chr(0x1F1E6+i)} {opt}\n"
            
            embed = discord.Embed(title=f"📊 {question}", description=desc, color=COLOR_SUCCESS)
            msg = await message.channel.send(embed=embed)
            for i in range(len(options)):
                await msg.add_reaction(chr(0x1F1E6+i))
        except:
            await message.channel.send("Usage: `!poll Question | Option A | Option B`")

    elif cmd == "!remindme":
        # Format: !remindme 5m Take out trash
        match = re.match(r"!remindme (\d+)([mh]) (.+)", content, re.I)
        if match:
            val, unit, text = match.groups()
            secs = int(val) * (60 if unit.lower() == 'm' else 3600)
            await message.channel.send(f"⏰ Timer set for {val}{unit}.")
            
            # Non-blocking sleep
            async def reminder_task(s, txt, usr):
                await asyncio.sleep(s)
                await message.channel.send(f"🔔 **Reminder:** {usr.mention} {txt}")
            
            asyncio.create_task(reminder_task(secs, text, message.author))
        else:
            await message.channel.send("Usage: `!remindme 10m Check server`")

    elif cmd == "!challenge":
        async with message.channel.typing():
            prompt = "Generate a beginner Python coding challenge. No code solution, just the problem description."
            res = await brain.query(prompt)
            await message.channel.send(f"🧩 **Daily Challenge**\n{res}")

    elif cmd == "!earn":
        # Gamification: Assign "Learner" badge
        role_name = "Python Learner"
        role = discord.utils.get(message.guild.roles, name=role_name)
        if not role:
            try: role = await message.guild.create_role(name=role_name, color=discord.Color.gold())
            except: pass
        if role:
            await message.author.add_roles(role)
            await message.channel.send(f"🏆 {message.author.mention} has earned the **{role_name}** badge!")

    elif cmd == "!flashcard":
        topic = content[11:].strip() or "Python"
        async with message.channel.typing():
            res = await brain.query(f"Create a flashcard for {topic}. Format: Question: [Q] || Answer: [A].")
            if "||" in res:
                q, a = res.split("||")
                try:
                    await message.author.send(f"❓ **Flashcard ({topic})**\n{q}")
                    await message.channel.send("📩 Check your DMs for a flashcard!")
                except:
                    await message.channel.send("❌ I couldn't DM you. Check privacy settings.")
            else:
                await message.channel.send(res)

    elif cmd == "!studygroup":
        # Creates a private voice/text channel for the user
        cat = discord.utils.get(message.guild.categories, name="Study Groups")
        if not cat: cat = await message.guild.create_category("Study Groups")
        
        c_name = f"group-{message.author.name}"
        overwrites = {
            message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            message.author: discord.PermissionOverwrite(read_messages=True)
        }
        chan = await message.guild.create_text_channel(c_name, category=cat, overwrites=overwrites)
        await message.channel.send(f"✅ Created study group: {chan.mention}")

    # --------------------------------------------------------------------------
    # GROUP B: AI LEARNING TOOLS
    # --------------------------------------------------------------------------
    elif cmd.startswith("!ask"):
        query = content[5:].strip()
        if not query: return await message.channel.send("Please provide a question.")
        async with message.channel.typing():
            response = await brain.query(query)
            await send_chunks(message.channel, response)

    elif cmd.startswith("!review"):
        code_snippet = content[8:].strip()
        if not code_snippet: return await message.channel.send("Please provide code.")
        async with message.channel.typing():
            prompt = f"Review this code for bugs and improvements:\n{code_snippet}"
            response = await brain.query(prompt)
            await send_chunks(message.channel, response)

    elif cmd.startswith("!yt"):
        topic = content[4:].strip()
        async with message.channel.typing():
            prompt = f"Provide one high-quality YouTube URL for learning: {topic}. Output ONLY the URL."
            response = await brain.query(prompt)
            await message.channel.send(f"📺 **Maestro Pick:** {response}")

    elif cmd.startswith("!resource"):
        topic = content[10:].strip()
        async with message.channel.typing():
            res = await brain.query(f"List 3 free learning resources for {topic} with URLs.")
            await send_chunks(message.channel, res)

    # --------------------------------------------------------------------------
    # GROUP C: ADMIN & ARCHITECT TOOLS (Restricted)
    # --------------------------------------------------------------------------
    elif is_admin:
        if cmd == "!setup_py101":
            # Restored functionality: Creates full course structure
            await message.channel.send("⏳ Initializing PY101 Course Structure...")
            cat = await message.guild.create_category("PY101 - Python")
            await message.guild.create_text_channel("syllabus", category=cat)
            await message.guild.create_text_channel("homework-help", category=cat)
            res_chan = await message.guild.create_text_channel("resources", category=cat)
            await res_chan.send(f"📚 **Course Notes:**\n{COURSE_NOTES[:1500]}")
            await message.channel.send("✅ Course Environment Ready.")

        elif cmd.startswith("!make_role"):
            # Format: !make_role Name | HexColor
            try:
                parts = content[11:].split("|")
                r_name = parts[0].strip()
                r_col = discord.Color(int(parts[1].strip().replace("#", ""), 16)) if len(parts) > 1 else discord.Color.default()
                await message.guild.create_role(name=r_name, color=r_col)
                await message.channel.send(f"✅ Role **{r_name}** created.")
            except:
                await message.channel.send("Usage: `!make_role Name | #HexColor`")

        elif cmd.startswith("!announce"):
            # Format: !announce Title | Body
            try:
                t, b = content[10:].split("|", 1)
                embed = discord.Embed(title=t.strip(), description=b.strip(), color=COLOR_ACCENT)
                await message.channel.send(embed=embed)
            except:
                await message.channel.send("Usage: `!announce Title | Description`")

        elif cmd.startswith("!dmall"):
            msg_body = content[7:].strip()
            count = 0
            for uid in list(db.dm_optins):
                try:
                    u = await bot.fetch_user(int(uid))
                    await u.send(f"🚨 **Admin Notice:** {msg_body}")
                    count += 1
                except: pass
            await message.channel.send(f"✅ Sent to {count} users.")

        elif cmd.startswith("!dmtouser"):
            # Format: !dmtouser @User Message
            if message.mentions:
                target = message.mentions[0]
                text = content.split(f"{target.id}>")[1]
                try:
                    await target.send(f"📩 **Message from Admin:** {text}")
                    await message.channel.send("✅ Sent.")
                except: await message.channel.send("❌ Could not DM user.")

        elif cmd.startswith("!post_in"):
            # Format: !post_in #channel | message
            match = re.search(r"<#(\d+)> \| (.+)", content)
            if match:
                cid, txt = match.groups()
                c = message.guild.get_channel(int(cid))
                if c: await c.send(txt); await message.channel.send("✅ Posted.")
            else: await message.channel.send("Usage: `!post_in #channel | Message`")

        elif cmd.startswith("!setup_private_role"):
            # The Complex Setup: Role + Category + Channel + Reaction Message
            try:
                # Format: Role | Category | Channel | Desc | Emoji
                args = [x.strip() for x in content[19:].split("|")]
                if len(args) < 5: raise ValueError
                role_n, cat_n, chan_n, desc, emoji = args
                
                # 1. Role
                role = discord.utils.get(message.guild.roles, name=role_n) or await message.guild.create_role(name=role_n)
                
                # 2. Permissions
                overwrites = {
                    message.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    role: discord.PermissionOverwrite(view_channel=True)
                }
                
                # 3. Channels
                cat = discord.utils.get(message.guild.categories, name=cat_n) or await message.guild.create_category(cat_n, overwrites=overwrites)
                chan = await message.guild.create_text_channel(chan_n, category=cat, overwrites=overwrites)
                await chan.send(f"**Welcome to {role_n}!**\n{desc}")
                
                # 4. Reaction Gate
                gate_chan = discord.utils.get(message.guild.text_channels, name="get-roles")
                if gate_chan:
                    gate_msg = await gate_chan.send(f"{emoji} React here to join **{role_n}**")
                    await gate_msg.add_reaction(emoji)
                    db.add_reaction_role(gate_msg.id, role_n)
                    
                await message.channel.send(f"✅ Private ecosystem setup for **{role_n}**.")
            except Exception as e:
                await message.channel.send(f"❌ Setup Error: {e}")

    # --------------------------------------------------------------------------
    # GROUP D: ARCHITECT MODE (Mention Trigger)
    # --------------------------------------------------------------------------
    
    if bot.user.mentioned_in(message) and is_admin:
        async with message.channel.typing():
            prompt = content.replace(f"<@{bot.user.id}>", "").strip()
            # Ask AI for JSON
            json_response = await brain.query(prompt, architect_mode=True)
            
            if "```json" in json_response:
                try:
                    # Extract JSON block
                    clean_json = json_response.split("```json")[1].split("```")[0].strip()
                    plan = json.loads(clean_json)
                    
                    await message.channel.send(f"🏗️ **Architect Plan: {plan.get('plan_name', 'Unnamed')}**")
                    
                    for action in plan.get('actions', []):
                        atype = action.get('type')
                        aname = action.get('name')
                        
                        if atype == 'create_role':
                            await message.guild.create_role(
                                name=aname, 
                                color=discord.Color.from_str(action.get('color', '#99aab5'))
                            )
                            await message.channel.send(f"🔹 Created Role: {aname}")
                            
                        elif atype == 'create_text':
                            cat_name = action.get('category')
                            cat = discord.utils.get(message.guild.categories, name=cat_name) if cat_name else None
                            await message.guild.create_text_channel(aname, category=cat)
                            await message.channel.send(f"🔹 Created Channel: {aname}")
                            
                        elif atype == 'create_category':
                            await message.guild.create_category(aname)
                            await message.channel.send(f"🔹 Created Category: {aname}")
                            
                    await message.channel.send("✅ **Execution Complete.**")
                except Exception as e:
                    await message.channel.send(f"⚠️ **Architect Malfunction:** {e}")
            else:
                # Fallback to normal chat if AI didn't return JSON
                await send_chunks(message.channel, json_response)
    
    elif bot.user.mentioned_in(message) and not is_admin:
        # Non-admin mention behavior
        async with message.channel.typing():
            res = await brain.query(content)
            await send_chunks(message.channel, res)

# ==============================================================================
# SECTION 8: SYSTEM ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    # 1. Start Web Server Thread (Daemon)
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    logger.info(f"System: Dashboard active on port {port}")

    # 2. Start Discord Bot (Main Thread)
    token = os.getenv("DISCORD_TOKEN")
    if token:
        try:
            bot.run(token)
        except Exception as e:
            logger.critical(f"System: Bot Crash: {e}")
    else:
        logger.critical("System: DISCORD_TOKEN missing from environment.")
