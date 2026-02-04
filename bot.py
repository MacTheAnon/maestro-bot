import discord
import google.generativeai as genai
import os
import json
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# =========================================================
# 🧠 1. LOAD KNOWLEDGE BASE
# =========================================================
try:
    from knowledge import COURSE_NOTES
except ImportError:
    COURSE_NOTES = "No specific course notes loaded."
# =========================================================
# 🔐 2. CONFIGURATION
# =========================================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# =========================================================
# 🌐 3. FAKE WEB SERVER (Render Fix)
# =========================================================
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
# =========================================================
# 🧠 4. PERSONA & UNLIMITED ARCHITECT PROMPT
# =========================================================
SYSTEM_PROMPT = f"""
You are "Maestro Bot", the official AI Mentor & Server Architect.

--- KNOWLEDGE BASE ---
{COURSE_NOTES}
----------------------

YOUR PERSONA:
1. You are a professional in Python, Cybersecurity, React, JS.
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
      "type": "create_category", 
      "name": "✨ Emojis & Custom Names Allowed ✨",
      "permissions": {{"@everyone": {{"view_channel": true}}, "Muted": {{"send_messages": false}}}} 
    }},
    {{
      "type": "create_text", 
      "name": "channel-name", 
      "category": "Category Name",
      "permissions": {{"@everyone": {{"send_messages": false}}}} 
    }},
    {{
      "type": "delete_channel", "name": "channel-name"
    }},
    {{
      "type": "kick", "user": "username"
    }}
  ]
}}
RULES:

1.Output ONLY the JSON block.

2. "permissions" is optional.

3. Use "@everyone" to refer to the default role. """

genai.configure(api_key=GOOGLE_API_KEY) 
model = genai.GenerativeModel('gemini-flash-latest', system_instruction=SYSTEM_PROMPT)
# =========================================================
# 🤖 5. DISCORD CLIENT SETUP
# =========================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # CRITICAL for Permissions & Kick
client = discord.Client(intents=intents)
@client.event
async def on_ready():
    print(f'⚡ {client.user} is online! Type "@MaestroBot hello" to test.')
@client.event
async def on_member_join(member):
    # Change "Student" to the exact name of the role you want to give
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
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # =========================================================
    # 🛠️ PART A: MANUAL COMMANDS
    # =========================================================
    if message.content == "!setup_py101":
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
            await status_msg.edit(content=f"✅ **Success!** Created {cat.name} and posted notes.")
        except Exception as e:
            await status_msg.edit(content=f"❌ Setup Failed: {e}")
        return
    # =========================================================
    # 🎥 NEW: YOUTUBE SEARCH COMMAND
    # =========================================================
    if message.content.startswith("!yt"):
        search_query = message.content.replace("!yt", "").strip()
        if not search_query:
            await message.channel.send("⚠️ Please provide a topic! Example: `!yt python tutorial`")
            return

        async with message.channel.typing():
            # Ask the AI to find a relevant educational YouTube link
            yt_prompt = f"Find a high-quality, relevant YouTube video link for this topic: {search_query}. Return ONLY the URL."
            yt_response = model.generate_content(yt_prompt)
            await message.channel.send(f"🎬 **Maestro's Top Pick for '{search_query}':**\n{yt_response.text}")
        return
    # =========================================================
    # 🧠 PART B: AI ARCHITECT (The Unlimited Engine)
    # =========================================================
    if client.user.mentioned_in(message):
        async with message.channel.typing():
            try:
                prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
                response = model.generate_content(prompt)
                response_text = response.text

                # DETECT JSON
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
                                # --- 1. BUILD PERMISSIONS ---
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
                                
                                # --- 2. EXECUTE ACTIONS ---
                                if action['type'] == 'create_category':
                                    cat = await guild.create_category(action['name'], overwrites=overwrites)
                                    created_categories[action['name']] = cat
                                    await message.channel.send(f"📂 Created: **{action['name']}**")
                                
                                elif action['type'] == 'create_text':
                                    target_cat = None
                                    if 'category' in action:
                                        target_cat = created_categories.get(action['category'])
                                        if not target_cat:
                                            target_cat = discord.utils.get(guild.categories, name=action['category'])
                                    await guild.create_text_channel(action['name'], category=target_cat, overwrites=overwrites)
                                    await message.channel.send(f"💬 Created Text: **{action['name']}**")
                                
                                elif action['type'] == 'create_voice':
                                    target_cat = None
                                    if 'category' in action:
                                        target_cat = created_categories.get(action['category']) or discord.utils.get(guild.categories, name=action['category'])
                                    await guild.create_voice_channel(action['name'], category=target_cat, overwrites=overwrites)
                                    await message.channel.send(f"🔊 Created Voice: **{action['name']}**")
                                
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
                                await message.channel.send(f"⚠️ Action Failed ({action.get('name')}): {e}")

                        await message.channel.send("✅ **Execution Complete.**")
                    except json.JSONDecodeError:
                        await message.channel.send("❌ AI JSON Error. Please retry.")
                else:
                    # NORMAL RESPONSE
                    if len(response_text) > 2000:
                        for i in range(0, len(response_text), 2000):
                            await message.channel.send(response_text[i:i+2000])
                    else:
                        await message.channel.send(response_text)

            except Exception as e:
                await message.channel.send(f"❌ Error: {e}")

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
