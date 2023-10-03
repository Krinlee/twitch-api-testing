import os, discord, requests, json
from discord.ext import tasks, commands
from twitchAPI.twitch import Twitch
from discord.utils import get
from dotenv import load_dotenv

dServer = os.getenv('DISCORD_SERVER')
lChan = os.getenv('GOING_LIVE')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='-', intents=intents)

TOKEN = os.getenv('DISCORD_TOKEN')

# Authentication with Twitch API
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
twitch = Twitch(client_id, client_secret)
twitch.authenticate_app([])
TWITCH_STREAM_API_ENDPOINT_V5 = "https://api.twitch.tv/kraken/streams/{}"
API_HEADERS = {
	'Client_ID': client_id,
	'Accept': 'application/vnd.twitchtv.v5=json',
}

# Returns true if online, false if not.
def checkuser(user):
	try:
		userid = twitch.get_users(logins=[user])['data'][0]['id']
		url = TWITCH_STREAM_API_ENDPOINT_V5.format(userid)
		try:
			req = requests.Session().get(url, headers=API_HEADERS)
			jsondata = req.json()
			if 'stream' in jsondata:
				if jsondata['stream'] is not None:
					return True
				else:
					return False
		except Exception as e:
			print("Error checking user: ", e)
			return False
	except IndexError:
		return False

# Execute when bot is started
@bot.event
async def on_ready():
	@tasks.loop(seconds=10)
	async def live_notifs_loop():
		with open('streamers.json', 'r') as file:
			streamers = json.loads(file.read())
		if streamers is not None:
			guild = bot.get_guild(dServer)
			channel = bot.get_channel(lChan)
			role = get(guild.roles, id=1057725396096917555)
			for user_id, twitch_name in streamers.items():
				status = checkuser(twitch_name)
				user = bot.get_user(int(user_id))
				if status is True:
					async for message in channel.history(limit=200):
						if str(user.mention) in message.content and "is not streaming" in message.content:
							break
						else:
							async for member in guild.fetch_members(limit=None):
								if member.id == int(user_id):
									await member.add_roles(role)
							async for message in channel.history(limit=200):
								if str(user.mention) in message.content and "is now streaming" in message.content:
									await message.delete()


@bot.command(name='addtwitch', help='Adds your Twitch to the live notifs.', pass_context=True)
async def add_twitch(ctx, twitch_name):
	with open('streamers.json', 'r') as file:
		streamers = json.loads(file.read())
	user_id = ctx.author.id
	streamers[user_id] = twitch_name

	with open('streamers.json', 'w') as file:
		file.write(json.dumps(streamers))
	await ctx.send(f"Added {twitch_name} for {ctx.author} to the notifications list.")

print('Server Running')
bot.run(TOKEN)





