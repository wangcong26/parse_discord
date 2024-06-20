import os
from dotenv import load_dotenv
import discord
import pandas as pd
import re

# Load environment variables from .env file
load_dotenv()

# Get the token from the environment variable
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

if TOKEN is None:
    raise ValueError("No token found. Please set the DISCORD_TOKEN environment variable.")
if CHANNEL_ID is None:
    raise ValueError("No channel ID found. Please set the CHANNEL_ID environment variable.")

print("Token found:", TOKEN)
print("Channel ID found:", CHANNEL_ID)

# Enable intents
intents = discord.Intents.default()
intents.message_content = True  # Enable if your bot needs to read messages
intents.members = True  # Enable if your bot needs to access member updates

basePath = os.getcwd()
folderName = 'data'
fileName = 'miji_signal_record.xlsx'
filePath = os.path.join(basePath, folderName, fileName)
print("Current Working Directory:", basePath)
print("File Path:", filePath)


class MyClient(discord.Client):
    def __init__(self, **options):
        super().__init__(intents=intents, **options)

    async def on_ready(self):
        try:
            print(f'Logged in as {self.user} (ID: {self.user.id})')
            print('------')

            print("Available guilds and their channels:")
            for guild in self.guilds:
                print(f"Guild: {guild.name} (ID: {guild.id})")
                for channel in guild.channels:
                    print(f"  Channel: {channel.name} (ID: {channel.id}, Type: {channel.type})")
                    if channel.id == int(CHANNEL_ID):
                        print(f"  -> Found target channel: {channel.name} (ID: {channel.id})")

            # Attempt to fetch the channel
            channel = self.get_channel(int(CHANNEL_ID))
            if channel is None:
                raise ValueError(f'Channel with ID {CHANNEL_ID} not found.')

            if channel.type != discord.ChannelType.text:
                raise ValueError(f'Channel with ID {CHANNEL_ID} is not a text channel.')

            permissions = channel.permissions_for(channel.guild.me)
            if not permissions.read_messages or not permissions.read_message_history:
                raise ValueError(f"Bot does not have permission to read messages in channel with ID {CHANNEL_ID}.")

            messages = await channel.history(limit=100).flatten()

            data = []
            for msg in messages:
                data.append([msg.created_at, msg.author.name, msg.content])

            import pandas as pd
            df = pd.DataFrame(data, columns=['Timestamp', 'Author', 'Content'])
            df.to_csv('discord_chat.csv', index=False)

            print('Messages have been saved to discord_chat.csv')
            await self.close()
        except Exception as e:
            print(f'An error occurred: {e}')


# Define a function to extract the patterns
def extract_patterns(text):
    if isinstance(text, str):
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+)，压力(\d+\.\d+)，止损(\d+\.\d+)'
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)，(止损(\d+\.\d+|\d+))?'
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)，止损(\d+\.\d+|\d+)。?' # good
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)(?:（.*?）)?，止损(\d+\.\d+|\d+)'
        # pattern2 = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)。?'
        pattern = r'([A-Z]+) 支撑(\d+\.\d+|\d+)(?:（.*?）)?，压力(\d+\.\d+|\d+)(?:（.*?）)?，止损(\d+\.\d+|\d+)(?:（.*?）)?'
        matches = re.findall(pattern, text)
        return matches
    return None

def format_currency(x):
    return "${:,.2f}".format(x)

if __name__ == '__main__':
    # client = MyClient()
    # client.run(TOKEN)

    df = pd.read_excel(filePath)
    df['extracted'] = df['Content'].apply(extract_patterns)
    df = df[df['extracted'].apply(lambda x: x != [])]
    df = df[df['extracted'].notna()]
    df = df.explode('extracted').reset_index(drop=True)
    df[['Symbol', 'LimitPrice', 'TakeProfit', 'StopLoss']] = pd.DataFrame(df['extracted'].tolist(), index=df.index)
    df['LotID'] = df.groupby('Date').cumcount() + 1
    df['LotID'] = df['LotID'].astype(object)
    df.loc[df.duplicated(subset=['Date'], keep=False) == False, 'LotID'] = ''

    targetHeader = ["Index", "Timestamp", "Symbol", "Action", "LotID", "Amount", "Quantity", "LimitPrice", "TakeProfit", "StopLoss", "Ready"]
    targetDataFrame = pd.DataFrame(columns=targetHeader)
    targetDataFrame['Timestamp'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M')
    targetDataFrame['Symbol'] = df['Symbol']
    targetDataFrame['Action'] = 'TRADE'
    targetDataFrame['LotID'] = df['LotID']
    targetDataFrame['Amount'] = 100_000 / targetDataFrame.groupby('Timestamp')['Timestamp'].transform('count')
    targetDataFrame['Amount'] = targetDataFrame['Amount'].astype(float).apply(lambda x: '${:,.0f}'.format(x))
    targetDataFrame['LimitPrice'] = df['LimitPrice'].astype(float)
    targetDataFrame['TakeProfit'] = df['TakeProfit'].astype(float)
    targetDataFrame['StopLoss'] = df['StopLoss'].astype(float)
    targetDataFrame['Ready'] = 'YES'
    targetDataFrame['Index'] = pd.RangeIndex(start=1, stop=len(df) + 1, step=1)

    targetDataFrame.to_excel('result.xlsx', index=False)
    targetDataFrame.to_csv('result.csv', index=False)
    print('Done')
