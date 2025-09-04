import discord as dc
from discord.ui import Select


class TicketTypeSelect(dc.ui.Select):
    def __init__(self, *args, **kwargs):
        options = [
            dc.SelectOption(label="🐞 Bug", value="bug"),
            dc.SelectOption(label="✨ Feature", value="feature"),
            dc.SelectOption(label="📚 Dokumentation", value="documentation"),
            dc.SelectOption(label="🆘 Hilfe", value="help"),
        ]
        super().__init__(
            placeholder="Kategorie wählen", options=options, *args, **kwargs
        )

    async def callback(self, interaction: dc.Interaction):
        self.view.ticket_type = self.values[0]
        await interaction.response.defer()


class TicketPrioritySelect(dc.ui.Select):
    def __init__(self, *args, **kwargs):
        options = [
            dc.SelectOption(label="🔴 Hoch", value="high"),
            dc.SelectOption(label="🟡 Mittel", value="medium"),
            dc.SelectOption(label="🟢 Niedrig", value="low"),
        ]
        super().__init__(
            placeholder="Priorität wählen", options=options, *args, **kwargs
        )

    async def callback(self, interaction: dc.Interaction):
        self.view.ticket_priority = self.values[0]
        await interaction.response.defer()
