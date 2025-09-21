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
    work on the ticket. Once assigned, the view transforms into
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

                # Update original message to show completion
                await interaction.response.edit_message(
                    content="✅ **Ticket completed and moved to done channel**",
                    view=None,
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
