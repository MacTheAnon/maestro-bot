import discord
import google.generativeai as genai
import os

# --- 🔐 CONFIGURATION ---
# Load keys from the Environment (Cloud)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Check if keys are missing (Good for debugging)
if not GOOGLE_API_KEY or not DISCORD_TOKEN:
    raise ValueError("❌ Keys are missing! Make sure to set GOOGLE_API_KEY and DISCORD_TOKEN in your environment variables.")

# --- 🧠 PERSONA SETUP ---
SYSTEM_PROMPT = """
You are the official AI Mentor for the Maestro Feb '26 Software Engineering Cohort.
Your name is "Maestro Bot".
Your goal is to help students with Python, AI, and debugging, but DO NOT just give them the answer.
Instead, guide them like a Senior Developer would:
1. Explain *why* their code is broken.
2. Give hints or corrected snippets, but encourage them to think.
3. Be professional, encouraging, and use emojis like 🚀, 💻, and 🧠.
4. If they ask about non-coding topics (like cooking), playfully remind them to get back to code.
"""

# Configure Gemini with the Persona
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(
    'gemini-flash-latest',
    system_instruction=SYSTEM_PROMPT
)

# Configure Discord
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
                # Clean the prompt
                prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
                
                # Ask Gemini
                response = model.generate_content(prompt)
                
                # Send back to Discord
                response_text = response.text
                if len(response_text) > 2000:
                    for i in range(0, len(response_text), 2000):
                        await message.channel.send(response_text[i:i+2000])
                else:
                    await message.channel.send(response_text)

            except Exception as e:
                await message.channel.send(f"❌ Error: {e}")

# Run the bot
client.run(DISCORD_TOKEN)