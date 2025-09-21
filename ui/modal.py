import discord as dc
from discord.ui import Modal
import requests as re
from settings import settings
from .ticket_management import TicketTodoView


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
        """
        Handle ticket form submission.

        Creates a GitHub issue and posts it to the todo channel with
        an assignee selection dropdown for workflow management.

        Args:
            interaction (dc.Interaction): Discord interaction from form submission
        """
        issue_title = str(self.ticket_title)
        issue_body = (
            f"### Description\n"
            f"{(self.ticket_description.value or '-').strip()}\n\n"
            f"### Technical Description\n"
            f"{(self.technical_description.value or '-').strip()}\n"
        )

        # Determine repository URL based on selection
        if self.repo_select == "frontend":
            url = f"https://api.github.com/repos/{settings.REPO_OWNER}/{settings.REPO_NAME_FRONTEND}/issues"
            repo_name = settings.REPO_NAME_FRONTEND
        elif self.repo_select == "backend":
            url = f"https://api.github.com/repos/{settings.REPO_OWNER}/{settings.REPO_NAME}/issues"
            repo_name = settings.REPO_NAME

        # Prepare GitHub API request
        headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
        data = {
            "title": issue_title,
            "body": issue_body,
            "labels": [self.ticket_type, self.ticket_priority],
        }

        # Create GitHub issue
        response = re.post(url, headers=headers, json=data)

        if response.status_code == 201:
            issue_data = response.json()
            issue_url = issue_data["html_url"]
            issue_number = issue_data["number"]
            role = interaction.guild.get_role(settings.DEV_ROLE_ID)

            # Create embedded message for todo channel
            embed = dc.Embed(
                title="🎫 New Ticket Created",
                description=f"**{issue_title}**",
                color=dc.Color.blue(),
            )
            embed.add_field(
                name="GitHub Issue", value=f"[View Issue]({issue_url})", inline=False
            )
            embed.add_field(
                name="Repository", value=self.repo_select.title(), inline=True
            )
            embed.add_field(
                name="Priority", value=self.ticket_priority.title(), inline=True
            )
            embed.add_field(name="Type", value=self.ticket_type.title(), inline=True)
            embed.add_field(name="Status", value="Waiting for Assignment", inline=False)

            # Create view with assignee dropdown
            view = TicketTodoView(
                settings.REPO_OWNER, repo_name, issue_number, issue_url
            )

            # Post to todo channel
            ticket_channel = interaction.guild.get_channel(
                int(settings.TICKET_TODO_CHANNEL_ID)
            )

            if not ticket_channel:
                await interaction.response.send_message(
                    "Todo channel not found! Check TICKET_TODO_CHANNEL_ID in settings.",
                    ephemeral=True,
                )
                return

            await ticket_channel.send(
                f"{role.mention} New ticket requires assignment:",
                embed=embed,
                view=view,
            )

            # Confirm creation to user
            await interaction.response.send_message(
                f"✅ Ticket created successfully: {issue_url}", ephemeral=True
            )

        else:
            # Handle creation failure
            await interaction.response.send_message(
                f"❌ Failed to create ticket\nError: {response.text}", ephemeral=True
            )
