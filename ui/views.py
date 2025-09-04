import discord as dc
from discord.ui import View
from .select_ui import TicketPrioritySelect, TicketTypeSelect
from .modal import TicketModal


class TicketSetupView(View):
    def __init__(self):
        super().__init__(timeout=180)

    @dc.ui.button(
        label="Weiter",
        style=dc.ButtonStyle.success,
        row=1,
        custom_id="ticket_submit_button",
    )
    async def continue_btn(self, interaction: dc.Interaction, button: dc.ui.Button):
        if not self.ticket_type or not self.ticket_priority:
            await interaction.response.send_message(
                "Bitte wähle eine Kategorie und eine Priorität", ephemeral=True
            )
            return
        await interaction.response.send_modal(
            TicketModal(self.ticket_type, self.ticket_priority)
        )

    @dc.ui.button(
        label="Abbrechen",
        style=dc.ButtonStyle.danger,
        row=1,
        custom_id="ticket_break_button",
    )
    async def cancel_btn(self, interaction: dc.Interaction, button: dc.ui.Button):
        await interaction.response.send_message("Abgebrochen", ephemeral=True)


# ------------------------------------------------------------------------------
# View für Ticket erstellen
class TicketCreateView(dc.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.ticket_type = None
        self.ticket_priority = None

        self.add_item(TicketTypeSelect(row=0))
        self.add_item(TicketPrioritySelect(row=1))

    def get_embed(self):
        return dc.Embed(
            title="🎫 Ticket erstellen",
            description="Bitte wähle die Ticket-Kategorie und Priorität aus.\n"
            "Klicke danach auf **Ticket erstellen**.",
            color=dc.Color.blurple(),
        )

    @dc.ui.button(
        label="🎟️ Ticket erstellen",
        style=dc.ButtonStyle.success,
        custom_id="ticket_create_button",
        row=2,
    )
    async def create_ticket(self, interaction: dc.Interaction, button: dc.ui.Button):
        if not self.ticket_type or not self.ticket_priority:
            await interaction.response.send_message(
                "Bitte zuerst Kategorie und Priorität auswählen!", ephemeral=True
            )
            return

        await interaction.response.send_modal(
            TicketModal(ticket_type=self.ticket_type, priority=self.ticket_priority)
        )
