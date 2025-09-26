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

            # Create a dedicated channel for this ticket
            channel_name = f"DEV-{self.repo_select}-{issue_title.lower().replace(' ', '-')[:20]}"
            
            # Find the "Support Tickets" category
            category = None
            for cat in interaction.guild.categories:
                if cat.name.lower() == "support tickets":
                    category = cat
                    break
            
            # If "Support Tickets" category doesn't exist, fallback to main ticket category
            if not category:
                category = interaction.guild.get_channel(int(settings.TICKET_CREATE_CHANNEL_ID)).category
            
            # Set up channel permissions - only specific roles can see the channel
            overwrites = {
                interaction.guild.default_role: dc.PermissionOverwrite(read_messages=False),
                interaction.guild.get_role(settings.DEV_ROLE_ID): dc.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
            }
            
            # Add staff roles if they exist
            if settings.STAFF_ROLE_ID:
                staff_role = interaction.guild.get_role(settings.STAFF_ROLE_ID)
                if staff_role:
                    overwrites[staff_role] = dc.PermissionOverwrite(
                        read_messages=True, send_messages=True, manage_messages=True
                    )
            
            if settings.ADMIN_ROLE_ID:
                admin_role = interaction.guild.get_role(settings.ADMIN_ROLE_ID)
                if admin_role:
                    overwrites[admin_role] = dc.PermissionOverwrite(
                        read_messages=True, send_messages=True, manage_messages=True, manage_channels=True
                    )
                    
            if settings.OWNER_ROLE_ID:
                owner_role = interaction.guild.get_role(settings.OWNER_ROLE_ID)
                if owner_role:
                    overwrites[owner_role] = dc.PermissionOverwrite(
                        read_messages=True, send_messages=True, manage_messages=True, manage_channels=True
                    )
            if settings.HEAD_STAFF_ID:
                head_staff_role = interaction.guild.get_role(settings.HEAD_STAFF_ID)
                if head_staff_role:
                    overwrites[head_staff_role] = dc.PermissionOverwrite(
                        read_messages=True, send_messages=True, manage_messages=True, manage_channels=True
                    )
            if settings.HEAD_MOD_ID:
                head_mod_role = interaction.guild.get_role(settings.HEAD_MOD_ID)
                if head_mod_role:
                    overwrites[head_mod_role] = dc.PermissionOverwrite(
                        read_messages=True, send_messages=True, manage_messages=True, manage_channels=True
                    )
            if settings.TRIAL_MOD_ID:
                trial_mod_role = interaction.guild.get_role(settings.TRIAL_MOD_ID)
                if trial_mod_role:
                    overwrites[trial_mod_role] = dc.PermissionOverwrite(
                        read_messages=True, send_messages=True, manage_messages=True
                    )
            if settings.DESIGNER_ROLE_ID:
                designer_role = interaction.guild.get_role(settings.DESIGNER_ROLE_ID)
                if designer_role:
                    overwrites[designer_role] = dc.PermissionOverwrite(
                        read_messages=True, send_messages=True, manage_messages=True
                    )
            
            # Create the new ticket channel with permissions
            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                topic=f"Ticket #{issue_number}: {issue_title}",
                overwrites=overwrites
            )

            # Create embedded message for the dedicated ticket channel
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
            embed.add_field(
                name="Description", 
                value=self.ticket_description.value or "No description provided", 
                inline=False
            )
            if self.technical_description.value:
                embed.add_field(
                    name="Technical Description", 
                    value=self.technical_description.value, 
                    inline=False
                )

            # Create view with assignee dropdown
            view = TicketTodoView(
                settings.REPO_OWNER, repo_name, issue_number, issue_url
            )

            # Post to the dedicated ticket channel
            await ticket_channel.send(
                f"{role.mention} New ticket requires assignment:",
                embed=embed,
                view=view,
            )

            # Also post a summary in the main todo channel for visibility
            main_todo_channel = interaction.guild.get_channel(
                int(settings.TICKET_TODO_CHANNEL_ID)
            )
            
            if main_todo_channel:
                summary_embed = dc.Embed(
                    title="🎫 New Ticket Channel Created",
                    description=f"**{issue_title}**",
                    color=dc.Color.green(),
                )
                summary_embed.add_field(
                    name="Channel", value=ticket_channel.mention, inline=True
                )
                summary_embed.add_field(
                    name="GitHub Issue", value=f"[View Issue]({issue_url})", inline=True
                )
                summary_embed.add_field(
                    name="Priority", value=self.ticket_priority.title(), inline=True
                )
                
                await main_todo_channel.send(embed=summary_embed)

            # Confirm creation to user
            await interaction.response.send_message(
                f"✅ Ticket created successfully!\n"
                f"📌 Channel: {ticket_channel.mention}\n"
                f"🔗 GitHub Issue: {issue_url}", 
                ephemeral=True
            )

        else:
            # Handle creation failure
            await interaction.response.send_message(
                f"❌ Failed to create ticket\nError: {response.text}", ephemeral=True
            )
