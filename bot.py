import discord
import google.generativeai as genai
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- 🧠 IMPORT KNOWLEDGE BASE ---
# This tries to import your notes. If the file is missing, it won't crash.
try:
    from knowledge import COURSE_NOTES
except ImportError:
    COURSE_NOTES = "No specific course notes loaded yet."

# --- 🔐 CONFIGURATION ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --- 🌐 FAKE WEB SERVER (Render Fix) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Maestro Bot is breathing!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    print(f"ðŸŒ Starting web server on port {port}...")
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- 🧠 PERSONA SETUP ---
SYSTEM_PROMPT = f"""
You are the official AI Mentor for the Maestro Feb '26 AI Software Engineering Cohort.
Your name is "Maestro Bot".

--- YOUR KNOWLEDGE BASE ---
Use the following course notes to answer specific questions about the curriculum or rules.
If the answer is in these notes, prioritise it.
{COURSE_NOTES}
---------------------------

YOUR PERSONA:
1. You are a professional in Python, C++, C#, React, JS, TS, HTML, CSS.
2. You are a Cybersecurity Professional.
3. You have a "Professor Mentality" -- explain WHY and HOW, don't just solve.
4. You are a Server Mod -- help automate and keep order.

INSTRUCTIONS:
- Guide students like a Senior Developer.
- Explain *why* code is broken.
- Give hints, not just answers.
- Create study plans when asked.
- Be professional but fun (use emojis).
- You can use your internal knowledge to research topics.
"""

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest', system_instruction=SYSTEM_PROMPT)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'⚡ {client.user} is online! Type "@MaestroBot hello" to test.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user.mentioned_in(message):
        async with message.channel.typing():
            try:
                prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
                response = model.generate_content(prompt)
                
                response_text = response.text
                if len(response_text) > 2000:
                    for i in range(0, len(response_text), 2000):
                        await message.channel.send(response_text[i:i+2000])
                else:
                    await message.channel.send(response_text)
            except Exception as e:
                await message.channel.send(f"❌ Error: {e}")

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
