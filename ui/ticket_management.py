"""
Ticket Management System for Discord Bot

This module handles the lifecycle of GitHub issues through Discord interactions:
1. Creates a ticket with assignee dropdown
2. Allows assignment to GitHub collaborators
3. Provides a "Done" button to close tickets and move them to completion channel

Classes:
    AssigneeSelect: Dropdown for selecting GitHub repository collaborators
    TicketTodoView: View for new tickets with assignee selection
    TicketDoneView: View for in-progress tickets with done button
"""

import discord as dc
import requests as re
from settings import settings


class AssigneeSelect(dc.ui.Select):
    """
    Discord dropdown select for choosing GitHub repository assignees.

    Fetches collaborators from the GitHub repository and displays them
    as options. When selected, assigns the user to the GitHub issue
    and updates the Discord message to show work-in-progress status.

    Args:
        repo_owner (str): GitHub repository owner/organization
        repo_name (str): GitHub repository name
        issue_number (int): GitHub issue number to assign
    """

    def __init__(self, repo_owner, repo_name, issue_number):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.issue_number = issue_number

        # Fetch GitHub collaborators for the repository
        collaborators = self.get_collaborators()
        options = [
            dc.SelectOption(label=collab["login"], value=collab["login"])
            for collab in collaborators[:25]  # Discord has a 25 option limit
        ]

        # Add default option if no collaborators found
        if not options:
            options = [dc.SelectOption(label="No collaborators found", value="none")]

        super().__init__(
            placeholder="Select an assignee",
            options=options,
            custom_id=f"assign_{issue_number}",
        )

    def get_collaborators(self):
        """
        Fetch repository collaborators from GitHub API.

        Returns:
            list: List of collaborator objects from GitHub API
        """
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/collaborators"
        headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}

        try:
            response = re.get(url, headers=headers)
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Error fetching collaborators: {e}")
            return []

    async def callback(self, interaction: dc.Interaction):
        """
        Handle assignee selection callback.

        Assigns the selected user to the GitHub issue and updates
        the Discord message to show work-in-progress status with
        a done button.

        Args:
            interaction (dc.Interaction): Discord interaction object
        """
        if self.values[0] == "none":
            await interaction.response.send_message(
                "No valid assignee selected", ephemeral=True
            )
            return

        assignee = self.values[0]

        # Assign user to GitHub issue
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{self.issue_number}"
        headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
        data = {"assignees": [assignee]}

        try:
            response = re.patch(url, headers=headers, json=data)

            if response.status_code == 200:
                issue_data = response.json()

                # Create work-in-progress embed
                embed = dc.Embed(
                    title="🔄 Ticket in Progress",
                    description=f"**Assignee:** {assignee}",
                    color=dc.Color.orange(),
                )
                embed.add_field(
                    name="GitHub Issue",
                    value=f"[View Issue]({issue_data['html_url']})",
                    inline=False,
                )
                embed.add_field(name="Status", value="Work in Progress", inline=True)

                # Replace view with done button only
                view = TicketDoneView(
                    self.repo_owner, self.repo_name, self.issue_number
                )
                await interaction.response.edit_message(embed=embed, view=view)

            else:
                await interaction.response.send_message(
                    f"Failed to assign user. GitHub API returned: {response.status_code}",
                    ephemeral=True,
                )

        except Exception as e:
            await interaction.response.send_message(
                f"Error assigning user: {str(e)}", ephemeral=True
            )


class TicketTodoView(dc.ui.View):
    """
    Discord view for new tickets waiting for assignment.

    Contains an AssigneeSelect dropdown for choosing who should
    work on the ticket and a Claim button for developers to
    self-assign. Once assigned, the view transforms into
    a TicketDoneView.

    Args:
        repo_owner (str): GitHub repository owner/organization
        repo_name (str): GitHub repository name
        issue_number (int): GitHub issue number
        issue_url (str): Direct URL to the GitHub issue
    """

    def __init__(self, repo_owner, repo_name, issue_number, issue_url):
        super().__init__(timeout=None)  # Persistent view
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.issue_number = issue_number
        self.issue_url = issue_url

        # Add assignee selection dropdown
        self.add_item(AssigneeSelect(repo_owner, repo_name, issue_number))

    @dc.ui.button(label="🚀 Claim Ticket", style=dc.ButtonStyle.primary, row=1)
    async def claim_ticket(self, interaction: dc.Interaction, button: dc.ui.Button):
        """
        Handle claim button click - allows developers to claim tickets in Discord.
        This only updates the Discord status, GitHub assignment still happens via Select dropdown.
        
        Args:
            interaction (dc.Interaction): Discord interaction object
            button (dc.ui.Button): The clicked button
        """
        # Check if user has developer role
        dev_role = interaction.guild.get_role(settings.DEV_ROLE_ID)
        if dev_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ You need the Developer role to claim tickets!", ephemeral=True
            )
            return

        # Create claimed embed (Discord only, no GitHub assignment yet)
        embed = dc.Embed(
            title="🔄 Ticket Claimed",
            description=f"**Claimed by:** {interaction.user.mention}",
            color=dc.Color.orange(),
        )
        embed.add_field(
            name="GitHub Issue",
            value=f"[View Issue]({self.issue_url})",
            inline=False,
        )
        embed.add_field(
            name="Status", 
            value="Claimed - Awaiting GitHub Assignment", 
            inline=True
        )
        embed.add_field(
            name="Note", 
            value="Use the dropdown above to assign this ticket in GitHub", 
            inline=False
        )

        # Keep the same view (AssigneeSelect dropdown still available)
        # This way GitHub assignment can still be done via the dropdown
        current_view = TicketTodoView(
            self.repo_owner, self.repo_name, self.issue_number, self.issue_url
        )
        
        # Update message to show claimed status
        await interaction.response.edit_message(embed=embed, view=current_view)
        
        # Send additional notification message
        await interaction.followup.send(
            f"🎯 **Ticket #{self.issue_number} has been claimed by {interaction.user.mention}!**\n"
            f"📋 Don't forget to assign it in GitHub using the dropdown above!\n"
            f"Good luck with the implementation! 💪"
        )


class TicketDoneView(dc.ui.View):
    """
    Discord view for tickets that are in progress.

    Contains a "Done" button that closes the GitHub issue and
    moves the ticket message to the completion channel.

    Args:
        repo_owner (str): GitHub repository owner/organization
        repo_name (str): GitHub repository name
        issue_number (int): GitHub issue number to close
    """

    def __init__(self, repo_owner, repo_name, issue_number):
        super().__init__(timeout=None)  # Persistent view
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.issue_number = issue_number

    @dc.ui.button(label="✅ Mark as Done", style=dc.ButtonStyle.success)
    async def done_button(self, interaction: dc.Interaction, button: dc.ui.Button):
        """
        Handle done button click.

        Closes the GitHub issue and moves the ticket message to
        the completion channel, updating the embed to show
        completed status.

        Args:
            interaction (dc.Interaction): Discord interaction object
            button (dc.ui.Button): The clicked button
        """
        # Close GitHub issue
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{self.issue_number}"
        headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
        data = {"state": "closed"}

        try:
            response = re.patch(url, headers=headers, json=data)

            if response.status_code == 200:
                issue_data = response.json()

                # Get done channel
                done_channel = interaction.guild.get_channel(
                    int(settings.DONE_CHANNEL_ID)
                )

                if not done_channel:
                    await interaction.response.send_message(
                        "Done channel not found! Check DONE_CHANNEL_ID in settings.",
                        ephemeral=True,
                    )
                    return

                # Create completion embed
                embed = dc.Embed(
                    title="✅ Ticket Completed",
                    description="This ticket has been successfully completed and closed.",
                    color=dc.Color.green(),
                )
                embed.add_field(
                    name="GitHub Issue",
                    value=f"[View Closed Issue]({issue_data['html_url']})",
                    inline=False,
                )
                embed.add_field(
                    name="Assignee",
                    value=issue_data.get("assignee", {}).get("login", "Unknown")
                    if issue_data.get("assignee")
                    else "Unassigned",
                    inline=True,
                )
                embed.add_field(
                    name="Repository",
                    value=f"{self.repo_owner}/{self.repo_name}",
                    inline=True,
                )

                # Post to done channel
                await done_channel.send(embed=embed)

                # Create a new view with delete channel button
                delete_view = TicketCompleteView()
                
                # Update original message to show completion with delete button
                await interaction.response.edit_message(
                    content="✅ **Ticket completed and moved to done channel**",
                    view=delete_view,
                    embed=None,
                )

            else:
                await interaction.response.send_message(
                    f"Failed to close issue. GitHub API returned: {response.status_code}",
                    ephemeral=True,
                )

        except Exception as e:
            await interaction.response.send_message(
                f"Error completing ticket: {str(e)}", ephemeral=True
            )


class TicketCompleteView(dc.ui.View):
    """
    Discord view for completed tickets.

    Contains a "Delete Channel" button that allows staff to clean up
    the ticket channel after completion.
    """

    def __init__(self):
        super().__init__(timeout=300)  # 5 minutes timeout

    @dc.ui.button(label="🗑️ Delete Channel", style=dc.ButtonStyle.danger)
    async def delete_channel_button(self, interaction: dc.Interaction, button: dc.ui.Button):
        """
        Handle delete channel button click.

        Deletes the current ticket channel after confirmation.
        Only staff, admin, or owner roles can delete channels.

        Args:
            interaction (dc.Interaction): Discord interaction object
            button (dc.ui.Button): The clicked button
        """
        # Check if user has permission to delete channels
        user_roles = [role.id for role in interaction.user.roles]
        allowed_roles = [settings.DEV_ROLE_ID]
        
        if settings.STAFF_ROLE_ID:
            allowed_roles.append(settings.STAFF_ROLE_ID)
        if settings.ADMIN_ROLE_ID:
            allowed_roles.append(settings.ADMIN_ROLE_ID)
        if settings.OWNER_ROLE_ID:
            allowed_roles.append(settings.OWNER_ROLE_ID)
        
        if not any(role_id in user_roles for role_id in allowed_roles):
            await interaction.response.send_message(
                "❌ You don't have permission to delete channels!", ephemeral=True
            )
            return

        # Create confirmation embed
        embed = dc.Embed(
            title="⚠️ Delete Channel Confirmation",
            description=f"Are you sure you want to delete {interaction.channel.mention}?\n\n"
                       f"**This action cannot be undone!**",
            color=dc.Color.red(),
        )
        
        # Create confirmation view
        confirm_view = ChannelDeleteConfirmView()
        
        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)


class ChannelDeleteConfirmView(dc.ui.View):
    """
    Confirmation view for channel deletion.
    """

    def __init__(self):
        super().__init__(timeout=60)  # 1 minute timeout

    @dc.ui.button(label="✅ Yes, Delete", style=dc.ButtonStyle.danger)
    async def confirm_delete(self, interaction: dc.Interaction, button: dc.ui.Button):
        """Confirm channel deletion."""
        try:
            channel_name = interaction.channel.name
            await interaction.response.send_message(
                f"🗑️ Deleting channel '{channel_name}' in 3 seconds...", 
                ephemeral=True
            )
            
            # Wait a moment then delete the channel
            import asyncio
            await asyncio.sleep(3)
            await interaction.channel.delete(reason="Ticket completed - channel cleanup")
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error deleting channel: {str(e)}", ephemeral=True
            )

    @dc.ui.button(label="❌ Cancel", style=dc.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: dc.Interaction, button: dc.ui.Button):
        """Cancel channel deletion."""
        await interaction.response.send_message(
            "✅ Channel deletion cancelled.", ephemeral=True
        )
