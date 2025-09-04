import discord as dc
import json
from settings import settings
from ui.views import TicketCreateView

intents = dc.Intents.default()
intents.guilds = True
bot = dc.Client(intents=intents)


@bot.event
async def on_ready():
    channel = await bot.fetch_channel(int(settings.TICKET_CHANNEL_ID))

    try:
        with open("ticket_message.json", "r") as f:
            data = json.load(f)
        msg_id = data["message_id"]

        msg = await channel.fetch_message(msg_id)
        # View re-anhängen, sonst sind Buttons/Drops nach Restart „tot“
        await msg.edit(view=TicketCreateView())
        print("✅ Ticket-Nachricht reaktiviert")
    except FileNotFoundError:
        # Falls keine gespeicherte Nachricht existiert
        view = TicketCreateView()
        msg = await channel.send(embed=view.get_embed(), view=view)
        with open("ticket_message.json", "w") as f:
            json.dump({"message_id": msg.id}, f)
        print("✅ Neue Ticket-Nachricht erstellt")


print(settings.DEV_ROLE_ID)

bot.run(settings.DC_TOKEN)
