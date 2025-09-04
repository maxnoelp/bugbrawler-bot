import discord as dc
from discord.ui import Modal
import requests as re
from settings import settings


class TicketModal(Modal, title="Ticket erstellen"):
    def __init__(self, ticket_type, priority, repo_select):
        super().__init__(title="Ticket erstellen")
        self.ticket_type = ticket_type
        self.ticket_priority = priority
        self.repo_select = repo_select

        self.ticket_title = dc.ui.TextInput(
            label="Ticket Titel",
            placeholder="Ticket Titel",
            style=dc.TextStyle.short,
            required=True,
        )

        self.ticket_description = dc.ui.TextInput(
            label="Ticket Beschreibung",
            placeholder="Ticket Beschreibung",
            style=dc.TextStyle.paragraph,
            required=True,
        )
        self.technical_description = dc.ui.TextInput(
            label="Technische Beschreibung",
            placeholder="Technische Beschreibung",
            style=dc.TextStyle.paragraph,
            required=False,
        )

        self.add_item(self.ticket_title)
        self.add_item(self.ticket_description)
        self.add_item(self.technical_description)

    async def on_submit(self, interaction: dc.Interaction):
        issue_title = str(self.ticket_title)
        issue_body = (
            f"### Beschreibung\n"
            f"{(self.ticket_description.value or '-').strip()}\n\n"
            f"### Technische Beschreibung\n"
            f"{(self.technical_description.value or '-').strip()}\n"
        )

        if self.repo_select == "frontend":
            url = f"https://api.github.com/repos/{settings.REPO_OWNER}/{settings.REPO_NAME_FRONTEND}/issues"
        elif self.repo_select == "backend":
            url = f"https://api.github.com/repos/{settings.REPO_OWNER}/{settings.REPO_NAME}/issues"

        headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
        data = {
            "title": issue_title,
            "body": issue_body,
            "labels": [self.ticket_type, self.ticket_priority],
        }
        response = re.post(url, headers=headers, json=data)
        if response.status_code == 201:
            issue_url = response.json()["html_url"]
            role = interaction.guild.get_role(settings.DEV_ROLE_ID)
            await interaction.response.send_message(
                f"Ticket erstellt: {issue_url}\n{role.mention}"
            )
        else:
            await interaction.response.send_message(
                f"Ticket konnte nicht erstellt werden\n{response.text}", ephemeral=True
            )
