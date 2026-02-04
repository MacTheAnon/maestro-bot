import discord
import google.generativeai as genai
import openai
from groq import Groq
import os
import json
import asyncio
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- 1. LOAD KNOWLEDGE BASE
try:
    from knowledge import COURSE_NOTES
except ImportError:
    COURSE_NOTES = "No specific course notes loaded."

# --- 2. CONFIGURATION
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- DM Opt-in storage ---
dm_optin_file = "dm_optin.json"
if os.path.exists(dm_optin_file):
    with open(dm_optin_file, "r") as f:
        dm_optin_set = set(json.load(f))
else:
    dm_optin_set = set()
def save_dm_optin():
    with open(dm_optin_file, "w") as f:
        json.dump(list(dm_optin_set), f)


# --- 3. FAKE WEB SERVER
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Maestro Bot is breathing!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Starting web server on port {port}...")
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()
threading.Thread(target=run_server, daemon=True).start()

# --- 4. SYSTEM PROMPT FOR AI
SYSTEM_PROMPT = f"""
You are "Maestro Bot", the official AI Mentor & Server Architect.
--- KNOWLEDGE BASE ---
{COURSE_NOTES}
----------------------
YOUR PERSONA:
1. You are a Expert in Python, Cybersecurity, React, JS.
2. You have a "Professor Mentality" (Explain WHY, don't just solve).
3. You are a Server Architect with UNLIMITED creative control.
🚨 SPECIAL ABILITY: GOD MODE (ARCHITECT) 🚨
If the user asks to modify the server, output a JSON block.
YOU CAN SET PERMISSIONS & USE EMOJIS!
- "Read Only" = {{"send_messages": false}}
- "Private" = {{"view_channel": false}}
- "Admins Only" = {{"view_channel": false}} for @everyone, {{"view_channel": true}} for Admin role.
JSON FORMAT:
```json
{{
  "plan_name": "Brief description",
  "actions": [
    {{
      "type": "create_role",
      "name": "Role Name",
      "color": "#FF0000"
    }},
    {{
      "type": "create_category",
      "name": "Category Name",
      "permissions": {{
        "@everyone": {{"view_channel": false}},
        "Role Name": {{"view_channel": true}}
      }}
    }},
    {{
      "type": "create_text",
      "name": "channel-name",
      "category": "Category Name",
      "permissions": {{
        "@everyone": {{"view_channel": false}},
        "Role Name": {{"view_channel": true}}
      }},
      "description": "Blah blah welcome text"
    }},
    {{
      "type": "reaction_role_message",
      "channel": "get-roles",
      "emoji": "🔔",
      "role": "Role Name",
      "description": "React below to get access to the private channel!"
    }}
  ]
}}
RULES:
1.Output ONLY the JSON block.
2."permissions"/"description" optional but best practice.
3.Use "@everyone" for default role.
"""

# ----- Gemini (generativeai) Model Setup -----
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-flash-latest", system_instruction=SYSTEM_PROMPT)
client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)
client_groq = Groq(api_key=GROQ_API_KEY)

async def generate_response(prompt):
    try:
        gemini_response = model.generate_content(prompt)
        return gemini_response.text
    except Exception as e:
        if "429" in str(e):
            print("⚠️ Gemini out. Trying OpenAI...")
            try:
                completion = client_openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                )
                return completion.choices[0].message.content
            except Exception as e2:
                print("⚠️ OpenAI out. Trying Groq...")
                try:
                    chat_completion = client_groq.chat.completions.create(
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ],
                        model="llama3-8b-8192"
                    )
                    return chat_completion.choices[0].message.content
                except Exception as e3:
                    print("❌ All AI systems exhausted.", e3)
                    return "❌ All AI systems are exhausted. Please try again in a few minutes."
        return f"❌ Gemini Error: {e}"

role_reaction_messages = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'⚡ {client.user} is online! Type "@MaestroBot hello" to test.')

@client.event
async def on_member_join(member):
    role_name = "FebruaryCohort"
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role:
        try:
            await member.add_roles(role)
            print(f"✅ Assigned {role_name} to {member.name}")
        except Exception as e:
            print(f"❌ Failed to assign role: {e}")
    else:
        print(f"⚠️ Role '{role_name}' not found in this server.")
    # --- Auto DM on join ---
    try:
        welcome_message = (
            f"👋 Welcome to Maestro, {member.display_name}!\n\n"
            "You're officially part of the community. Check out #get-roles to customize your experience, "
            "and type `!help` in any public channel for everything I can do.\n\n"
            "If you want to get important DM announcements/pings, type `!optin` in the server at any time!"
        )
        await member.send(welcome_message)
    except Exception:
        print(f"❗ Could not DM member {member.name} (Privacy settings?)")

@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return
    guild = client.get_guild(payload.guild_id)
    if not guild:
        return
    role_name = role_reaction_messages.get(payload.message_id)
    if not role_name:
        channel = guild.get_channel(payload.channel_id)
        if channel and channel.name == "get-roles":
            if str(payload.emoji) == "🔔":
                role = discord.utils.get(guild.roles, name="YouTube Supporter")
                if role:
                    member = payload.member or guild.get_member(payload.user_id)
                    if member and role not in member.roles:
                        await member.add_roles(role)
        return
    role = discord.utils.get(guild.roles, name=role_name)
    member = payload.member or guild.get_member(payload.user_id)
    if role and member and role not in member.roles:
        await member.add_roles(role)

@client.event
async def on_raw_reaction_remove(payload):
    guild = client.get_guild(payload.guild_id)
    if not guild:
        return
    role_name = role_reaction_messages.get(payload.message_id)
    if not role_name:
        channel = guild.get_channel(payload.channel_id)
        if channel and channel.name == "get-roles":
            if str(payload.emoji) == "🔔":
                role = discord.utils.get(guild.roles, name="YouTube Supporter")
                if role:
                    member = guild.get_member(payload.user_id)
                    if member and role in member.roles:
                        await member.remove_roles(role)
        return
    role = discord.utils.get(guild.roles, name=role_name)
    member = guild.get_member(payload.user_id)
    if role and member and role in member.roles:
        await member.remove_roles(role)

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    content = message.content.strip()

    # === DM OPT-IN/OUT ===
    if content.lower() == "!optin":
        dm_optin_set.add(str(message.author.id))
        save_dm_optin()
        await message.channel.send(f"✅ {message.author.mention} opted in to DM announcements.")
        return

    if content.lower() == "!optout":
        if str(message.author.id) in dm_optin_set:
            dm_optin_set.remove(str(message.author.id))
            save_dm_optin()
            await message.channel.send(f"✅ {message.author.mention} opted out of DM announcements.")
        else:
            await message.channel.send(f"You're not opted in!")
        return

    # === ADMIN: DM ANY USER ===
    if content.lower().startswith("!dmtouser "):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("⛔ Only admins can DM users with this command.")
            return
        match = re.match(r"!dmtouser\s+<@!?(\d+)>\s+(.+)", content)
        if not match:
            await message.channel.send("Format: !dmtouser @user message_here")
            return
        user_id, dm_content = match.groups()
        user = client.get_user(int(user_id))
        if user:
            try:
                await user.send(dm_content)
                await message.channel.send("✅ Direct message sent!")
            except Exception:
                await message.channel.send("❌ I couldn't DM this user (privacy settings may block it).")
        else:
            await message.channel.send("❌ User not found.")
        return

    # === ADMIN: MASS DM (OPTED-IN) ===
    if content.lower().startswith("!dmall "):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("⛔ Only admins can mass DM.")
            return
        dm_content = content[len("!dmall "):].strip()
        if not dm_optin_set:
            await message.channel.send("No users have opted in to DM announcements.")
            return
        count = 0
        for user_id in dm_optin_set.copy():
            user = client.get_user(int(user_id))
            if user:
                try:
                    await user.send(dm_content)
                    count += 1
                    await asyncio.sleep(1.2)
                except:
                    dm_optin_set.discard(user_id)
        save_dm_optin()
        await message.channel.send(f"✅ DM sent to {count} opted-in users.")
        return
        
    if message.author == client.user or message.author.bot:
        return

    content = message.content.strip()

    # === SMART PRIVATE ROLE & REACTION SYSTEM ===
    if content.lower().startswith("!setup_private_role"):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("⛔ Only admins can use this.")
            return
        try:
            args = content[len("!setup_private_role"):].split('|')
            if len(args) < 5:
                await message.channel.send("Usage: !setup_private_role RoleName | Category | channel-name | description | emoji")
                return
            role_name = args[0].strip()
            category_name = args[1].strip()
            channel_name = args[2].strip()
            description = args[3].strip()
            emoji = args[4].strip()
            guild = message.guild
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                role = await guild.create_role(name=role_name, mentionable=True)
            category = discord.utils.get(guild.categories, name=category_name)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
            if not category:
                category = await guild.create_category(category_name, overwrites=overwrites)
            else:
                await category.edit(overwrites=overwrites)
            ch = discord.utils.get(guild.text_channels, name=channel_name)
            if not ch:
                ch = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
            else:
                await ch.edit(category=category, overwrites=overwrites)
            embed = discord.Embed(
                title=f"Welcome to {role_name} channel!",
                description=description,
                color=discord.Color.green()
            )
            await ch.send(embed=embed)
            get_roles_ch = discord.utils.get(guild.text_channels, name="get-roles")
            if get_roles_ch:
                opt_in_msg = await get_roles_ch.send(
                    f"{emoji} **Want to join `{role_name}` and access {ch.mention}?** React with {emoji} to opt-in; remove to opt-out."
                )
                await opt_in_msg.add_reaction(emoji)
                role_reaction_messages[opt_in_msg.id] = role_name
            await message.channel.send(f"✅ Private role/channel for `{role_name}` live! Opt-in posted in #get-roles.")
        except Exception as e:
            await message.channel.send(f"❌ Error: {e}")
        return
    if message.author == client.user or message.author.bot:
        return

    content = message.content.strip()

    # --- MANUAL COMMANDS ---
    if content.lower() == "!setup_py101":
        if not message.author.guild_permissions.administrator:
            await message.channel.send("⛔ Only Admins can run the full course setup.")
            return

        status_msg = await message.channel.send("⏳ Setting up PY101 Environment...")
        guild = message.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        try:
            cat = await guild.create_category("PY101 Curriculum 🐍", overwrites=overwrites)
            chan = await guild.create_text_channel("study-plan", category=cat)
            await chan.send("📘 **OFFICIAL PY101 STUDY PLAN & NOTES**")
            if len(COURSE_NOTES) > 2000:
                for i in range(0, len(COURSE_NOTES), 2000):
                    await chan.send(COURSE_NOTES[i:i+2000])
            else:
                await chan.send(COURSE_NOTES)
            await status_msg.edit(content=f"✅ Success! Created {cat.name} and posted notes.")
        except Exception as e:
            await status_msg.edit(content=f"❌ Setup Failed: {e}")
        return

    # --- ADMIN: CREATE ROLE ---
    if content.lower().startswith("!make_role"):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("⛔ Only admins can create roles.")
            return
        try:
            # !make_role Mentor | orange | true
            parts = content[len("!make_role"):].split("|")
            name = parts[0].strip()
            color = discord.Color.default()
            hoist = False

            if len(parts) > 1 and parts[1].strip():
                color_str = parts[1].strip()
                try:
                    if color_str.startswith("#"):
                        color = discord.Color(int(color_str.replace("#", ""), 16))
                    else:
                        color = getattr(discord.Color, color_str.lower())()
                except Exception:
                    pass

            if len(parts) > 2:
                hoist = parts[2].strip().lower() in ["true", "1", "yes", "y"]

            existing_role = discord.utils.get(message.guild.roles, name=name)
            if existing_role:
                await message.channel.send("A role with that name already exists.")
                return
            role = await message.guild.create_role(name=name, color=color, hoist=hoist)
            await message.channel.send(f"✅ Created role **{role.name}**.")
        except Exception as e:
            await message.channel.send(f"❌ Could not create role: {e}")
        return

    # --- ADMIN: POST ANYWHERE ---
    if content.lower().startswith("!post_in"):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("⛔ Only admins can use this feature.")
            return
        try:
            match = re.match(r"!post_in\s+#?([\w\-]+)\s*\|\s*(.+)", content, re.I)
            if not match:
                await message.channel.send("Format: `!post_in #channel | Your message here`")
                return
            chan_name, msg = match.groups()
            target_chan = discord.utils.get(message.guild.text_channels, name=chan_name)
            if not target_chan:
                await message.channel.send(f"Couldn't find channel: {chan_name}")
                return
            await target_chan.send(msg)
            await message.channel.send(f"✅ Posted in {target_chan.mention}")
        except Exception as e:
            await message.channel.send(f"❌ Could not send message: {e}")
        return

    # --- YOUTUBE SEARCH COMMAND ---
    if content.lower().startswith("!yt "):
        search_query = content[4:].strip()
        if not search_query:
            await message.channel.send("⚠️ Please provide a topic! Example: `!yt python tutorial`")
            return
        async with message.channel.typing():
            yt_prompt = f"Find a high-quality, relevant YouTube video link for this topic: {search_query}. Return ONLY the URL."
            response_text = await generate_response(yt_prompt)
            if response_text.startswith("❌ All AI systems"):
                await message.channel.send("🚧 My AI brain is temporarily unavailable, but you can still use the rest of Maestro's features!")
            else:
                await message.channel.send(f"🎬 **Maestro's Top Pick for '{search_query}':**\n{response_text}")
        return

    if content.lower().startswith("!ask "):
        question = content[5:].strip()
        if not question:
            await message.channel.send("❓ Please enter a question after `!ask`.")
            return
        async with message.channel.typing():
            tutor_prompt = f"Answer as an expert Python tutor, step by step. Student: {question}"
            response_text = await generate_response(tutor_prompt)
            if response_text.startswith("❌ All AI systems"):
                await message.channel.send("🚧 My AI brain is temporarily unavailable, but you can still use the rest of Maestro's features!")
            else:
                await message.channel.send(response_text[:2000])
        return

    if content.lower().startswith("!flashcard"):
        topic = content[len("!flashcard"):].strip() or "python"
        async with message.channel.typing():
            flashcard_prompt = f"Give me a simple {topic} flashcard: one short question and answer, format:\nQuestion: ...\nAnswer: ...\nDo not show answer immediately."
            response_text = await generate_response(flashcard_prompt)
            if response_text.startswith("❌ All AI systems"):
                await message.channel.send("🚧 My AI brain is temporarily unavailable, but you can still use the rest of Maestro's features!")
                return
            parts = response_text.split("Answer:")
            if len(parts) == 2:
                try:
                    await message.author.send(f"**Flashcard Question:**\n{parts[0].strip()}\nReply with anything to see the answer.")
                    def check(m): return m.author == message.author and isinstance(m.channel, discord.DMChannel)
                    reply = await client.wait_for('message', check=check, timeout=60)
                    await message.author.send(f"**Answer:** {parts[1].strip()}")
                except asyncio.TimeoutError:
                    try:
                        await message.author.send("⏰ Timed out! Try `!flashcard` again.")
                    except Exception:
                        await message.channel.send("❗ I couldn't DM you. Please enable DMs from server members.")
                except Exception:
                    await message.channel.send("❗ I couldn't DM you. Please enable DMs from server members.")
            else:
                await message.channel.send("⚠️ Couldn't generate flashcard. Try again.")
        return

    if content.lower() == "!challenge":
        async with message.channel.typing():
            challenge_prompt = "Give me today's quick Python coding challenge. Keep it under 1 paragraph, beginner friendly. No solution, just the challenge."
            response_text = await generate_response(challenge_prompt)
            if response_text.startswith("❌ All AI systems"):
                await message.channel.send("🚧 My AI brain is temporarily unavailable, but you can still use the rest of Maestro's features!")
            else:
                await message.channel.send(f"🧩 **Daily Challenge:**\n{response_text[:1900]}")
        return

    if content.lower() == "!earn":
        role_name = "Python Learner"
        guild = message.guild
        role = discord.utils.get(guild.roles, name=role_name)
        # Create the role if it doesn't exist
        if not role:
            try:
                role = await guild.create_role(
                    name=role_name, 
                    color=discord.Color.gold(), 
                    hoist=True
                )
            except Exception as e:
                await message.channel.send("❌ Could not create the badge role. Please contact an admin.")
                print(f"❌ Could not create role: {e}")

        if role and role not in message.author.roles:
            await message.author.add_roles(role)
            embed = discord.Embed(
                title="Achievement Unlocked!",
                description=f"{message.author.mention} has officially earned the **{role_name}** badge! 🐍✨",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url="https://i.imgur.com/Bf1o67I.png") # Python badge icon
            await message.channel.send(embed=embed)
        elif role:
            await message.channel.send(f"{message.author.mention}, you already have the **{role_name}** badge! 🥇")
        return

    if content.lower() == "!dev":
        embed = discord.Embed(
            title="About the Developer",
            description=(
                "Hi, I'm **Kaleb McIntosh**, one of your February cohorts!\n\n"
                "I'm grateful for everyone in this community and eager to help 🎉\n\n"
                "[🌐 My Portfolio](https://www.kalebmcintosh.com)\n"
                "[💻 McIntosh Digital](https://www.mcintoshdigital.com)"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Let’s code and grow together! 🚀")
        await message.channel.send(embed=embed)
        return

    if content.lower().startswith("!review "):
        code = content[8:].strip()
        if not code:
            await message.channel.send("Paste your code after `!review` for feedback.")
            return
        review_prompt = ("Review the following code, spot mistakes, and give one improvement suggestion. "
                         "Be positive and short. Code:\n" + code)
        response_text = await generate_response(review_prompt)
        if response_text.startswith("❌ All AI systems"):
            await message.channel.send("🚧 My AI brain is temporarily unavailable, but you can still use the rest of Maestro's features!")
        else:
            await message.channel.send(f"📝 **Review:**\n{response_text[:1900]}")
        return

    if content.lower().startswith("!resource "):
        topic = content[9:].strip()
        if not topic:
            await message.channel.send("Type a topic after `!resource`.")
            return
        resource_prompt = f"Give 2 top beginner-friendly, free resources for learning {topic}. Include links."
        response_text = await generate_response(resource_prompt)
        if response_text.startswith("❌ All AI systems"):
            await message.channel.send("🚧 My AI brain is temporarily unavailable, but you can still use the rest of Maestro's features!")
        else:
            await message.channel.send(f"🔗 {response_text[:1900]}")
        return

    if content.lower() == "!studygroup":
        group_name = f"studygroup-{message.author.name}".lower()
        guild = message.guild
        cat = discord.utils.get(guild.categories, name="Study Groups")
        if not cat:
            cat = await guild.create_category("Study Groups")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            message.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        chan = await guild.create_text_channel(group_name, category=cat, overwrites=overwrites)
        await chan.send(f"🧑‍💻 Welcome to your private study group, {message.author.mention}!")
        await message.channel.send(f"🔒 Study group created: {chan.mention}")
        return

    if content.lower().startswith("!announce "):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("Admins only.")
            return
        try:
            title, description = content[9:].split("|", 1)
            announce = f"📢 **{title.strip()}**\n\n{description.strip()}"
            await message.channel.send(announce)
        except Exception:
            await message.channel.send("Use: !announce Event Title | Event details here")
        return

    if content.lower().startswith("!remindme "):
        match = re.match(r"!remindme (\d+)([mh]) (.+)", content)
        if not match:
            await message.channel.send("Format: !remindme 5m Take a break")
            return
        num, unit, reminder = match.groups()
        secs = int(num) * (60 if unit == "m" else 3600)
        await message.channel.send(f"⏰ I'll DM you in {num}{unit}: {reminder}")
        async def send_reminder():
            try:
                await asyncio.sleep(secs)
                await message.author.send(f"⏰ Reminder: {reminder}")
            except Exception:
                await message.channel.send("❗ I couldn't DM you the reminder. Please enable DMs from server members.")
        asyncio.create_task(send_reminder())
        return

    if content.lower().startswith("!poll "):
        try:
            parts = content[6:].split("|")
            question = parts[0].strip()
            options = [opt.strip() for opt in parts[1:]]
            if len(options) < 2 or len(options) > 5:
                await message.channel.send("2-5 options please. Example: !poll Q | A | B")
                return
            poll_msg = await message.channel.send(f"📊 **{question}**\n" + "\n".join([f"{chr(0x1F1E6+i)} {o}" for i, o in enumerate(options)]))
            emojis = [chr(0x1F1E6 + i) for i in range(len(options))]
            for emoji in emojis:
                await poll_msg.add_reaction(emoji)
        except Exception:
            await message.channel.send("Format: !poll Question | Option1 | Option2 ...")
        return

    if content.lower() == "!help":
        is_admin = False
        if message.guild:
            perms = message.author.guild_permissions
            is_admin = perms.administrator or perms.manage_guild or perms.manage_channels or perms.kick_members
        user_commands = [
            "`!help` — Show this message",
            "`!ask <question>` — Ask Maestro any coding or learning question",
            "`!flashcard <topic>` — Practice a flashcard (DM)",
            "`!challenge` — Get a daily quick coding challenge",
            "`!resource <topic>` — Get learning resource links",
            "`!review <your code>` — Get feedback on your code",
            "`!poll Question | Option1 | Option2 ...` — Create a quick poll",
            "`!remindme 5m Do something` — DM reminder",
            "`!studygroup` — Start a private study group",
            "`!yt <topic>` — Find a useful YouTube video",
            "`!earn` — Get a learning badge",
            "`!dev` — About the developer",
        ]
        admin_commands = [
            "`!setup_py101` — Full course environment setup",
            "`!announce Title | Description` — Post an announcement (admins only)",
            "`!make_role Name | #color | hoist` — Admin: Create a new role",
            "`!post_in #channel | message` — Admin: Bot posts in any channel",
        ]
        msg = "**🤖 Maestro Bot Help**\n\n"
        msg += "\n".join(user_commands)
        if is_admin:
            msg += "\n\n**🛡️ Admin/Mod Commands:**\n"
            msg += "\n".join(admin_commands)
        await message.channel.send(msg)
        return

    # --- AI ARCHITECT (The Unlimited Engine) ---
    if client.user.mentioned_in(message):
        async with message.channel.typing():
            try:
                prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
                response_text = await generate_response(prompt)
                if response_text.startswith("❌ All AI systems"):
                    await message.channel.send("🚧 My AI brain is temporarily unavailable, but you can still use the rest of Maestro's features!")
                    return
                if "```json" in response_text:
                    if not message.author.guild_permissions.administrator:
                        await message.channel.send("⛔ **Security Alert:** You are not an Admin.")
                        return
                    try:
                        json_str = response_text.split("```json")[1].split("```")[0].strip()
                        plan = json.loads(json_str)
                        await message.channel.send(f"🛡️ **Architect Mode:** Executing *{plan['plan_name']}*...")
                        guild = message.guild
                        created_categories = {}
                        for action in plan['actions']:
                            try:
                                overwrites = {}
                                if 'permissions' in action:
                                    for role_name, perms in action['permissions'].items():
                                        target_role = None
                                        if role_name == "@everyone":
                                            target_role = guild.default_role
                                        else:
                                            target_role = discord.utils.get(guild.roles, name=role_name)
                                        if target_role:
                                            overwrite = discord.PermissionOverwrite(**perms)
                                            overwrites[target_role] = overwrite
                                if action['type'] == 'create_category':
                                    cat = await guild.create_category(action['name'], overwrites=overwrites)
                                    created_categories[action['name']] = cat
                                    await message.channel.send(f"📂 Created: **{action['name']}**")
                                elif action['type'] == 'create_text':
                                    target_cat = created_categories.get(action.get('category')) or discord.utils.get(guild.categories, name=action.get('category'))
                                    await guild.create_text_channel(action['name'], category=target_cat, overwrites=overwrites)
                                    await message.channel.send(f"💬 Created Text: **{action['name']}**")
                                elif action['type'] == 'delete_channel':
                                    chan = discord.utils.get(guild.channels, name=action['name'])
                                    if chan:
                                        await chan.delete()
                                        await message.channel.send(f"🗑️ Deleted: **{action['name']}**")
                                elif action['type'] == 'kick':
                                    member = discord.utils.get(guild.members, name=action['user'])
                                    if member:
                                        await member.kick(reason="Maestro Bot Admin Action")
                                        await message.channel.send(f"🥾 Kicked: **{member.name}**")
                                await asyncio.sleep(1)
                            except Exception as e:
                                await message.channel.send(f"⚠️ Action Failed: {e}")
                        await message.channel.send("✅ **Execution Complete.**")
                    except json.JSONDecodeError:
                        await message.channel.send("❌ AI JSON Error. Please retry.")
                else:
                    await message.channel.send(response_text[:2000])
            except Exception as e:
                await message.channel.send(f"❌ Error: {e}")

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)




