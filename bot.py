import discord
import google.generativeai as genai
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- 🔐 CONFIGURATION ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --- 🌐 FAKE WEB SERVER (The Fix) ---
# This keeps Render happy by listening on the specific port it assigns
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Maestro Bot is breathing!")

def run_server():
    # CRITICAL FIX: Get the PORT from Render, or use 8080 if running locally
    port = int(os.environ.get("PORT", 8080))
    
    print(f"ðŸŒ Starting web server on port {port}...") # Log this so we can see it
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# Start the web server in a background thread BEFORE the bot starts
threading.Thread(target=run_server, daemon=True).start()

# --- 🧠 PERSONA & BOT SETUP ---
SYSTEM_PROMPT = """
You are the official AI Mentor for the Maestro Feb '26 AI Software Engineering Cohort.
Your name is "Maestro Bot". 
You are a professional in python,c++, C#, and every othe language model including but not limited to , react, js ,ts, html, css and you will generate the codes , all while teaching why, how ,and coming up with study plans!
You also have the professor mentality, you are a server mod so you will help automate the server better!
Guide students like a Senior Developer:
1. Explain *why* code is broken.
2. Give hints, not just answers.
3. Be professional but fun (use emojis).
You are also a cybersecurity professional, you can also use the internet to research 
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

# Run the bot
if __name__ == "__main__":

    client.run(DISCORD_TOKEN)
