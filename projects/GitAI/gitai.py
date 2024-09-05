import subprocess
from typing import List, Optional
from amp_lib import AmpClient  # Ensure amp_lib is installed or provide a stub file
import uuid

"""
GitAI: An intelligent Git commit message generator

This project provides a tool that analyzes Git diffs and generates suggested commit messages using AI. Key features include:

1. Parsing Git diffs for both staged and unstaged changes
2. Using the AmpClient to interact with an AI model for generating commit messages
3. Maintaining a conversation context for iterative refinement of suggestions
4. Displaying Git status information
5. Allowing user input to influence subsequent suggestions

The main class, GitDiffParser, handles the core functionality, while the main() function provides a simple CLI for interacting with the tool.
"""


class GitDiffParser:
    def __init__(self):
        self.amp_client = AmpClient()
        self.conversation_id = f"GITAI_{uuid.uuid4()}"
        self.system_message_is_set = False

    def get_suggested_commit_message(self) -> Optional[str]:
        if not self.system_message_is_set:
            diff_lines = self.get_git_diff()
            if not diff_lines:
                print("No changes found.")
                return None

            changes = self.parse_diff(diff_lines)

            if not changes:
                print("No changes found.")
                return "No changes found."

            changes_prompt = "\n".join(
                [f"```diff\n{change}\n```" for change in changes]
            )

            self.amp_client.add_system_message(
                conversation_id=self.conversation_id,
                message=f"""You are a helpful assistant that generates commit messages for git diffs. Provide only a single-line commit message, without any additional explanations or text. Start the commit message with an imperative verb like 'Create', 'Update', 'Delete', etc. 

In the git diff below:
- Lines starting with '+' indicate added content
- Lines starting with '-' indicate removed content
- All other lines are there for context

Here is the git diff to consider:

{changes_prompt}""",
            )
            self.system_message_is_set = True

        response = self.amp_client.generate_response(
            conversation_id=self.conversation_id,
            message="Based on the provided git diff in the system message, generate a concise and informative single-line commit message of the most important changes. Start with an imperative verb like 'Create', 'Update', 'Delete', etc.",
        )

        return response.strip().split("\n")[0] if response else None

    def get_git_diff(self) -> List[str]:
        try:
            # Get staged changes
            staged = subprocess.run(
                ["git", "diff", "--cached", "--unified=3"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Get unstaged changes
            # unstaged = subprocess.run(
            #     ["git", "diff", "--unified=3"],
            #     capture_output=True,
            #     text=True,
            #     check=True,
            # )

            # Combine staged and unstaged changes
            all_changes = staged.stdout
            return all_changes.split("\n")
        except subprocess.CalledProcessError:
            print(
                "Error: Unable to get git diff. Make sure you're in a git repository."
            )
            return []

    def parse_diff(self, diff_lines: List[str]) -> List[str]:
        changes = []
        current_change = []
        for line in diff_lines:
            if line.startswith("diff --git"):
                if current_change:
                    changes.append("\n".join(current_change))
                    current_change = []
            current_change.append(line)

        if current_change:
            changes.append("\n".join(current_change))

        return [] if all(change.strip() == "" for change in changes) else changes

    def process_diff(self):
        diff_lines = self.get_git_diff()
        if not diff_lines:
            return

        self.parse_diff(diff_lines)

    def add_user_input(self, user_input: str):
        self.amp_client.add_user_message(
            conversation_id=self.conversation_id, message=user_input
        )
        self.amp_client.add_assistant_message(
            conversation_id=self.conversation_id,
            message="I understand. I'll take your input into consideration for the next suggestion.",
        )

    def get_git_status(self) -> str:
        try:
            git_status = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            return f"Git Status:\n{git_status.stdout}"
        except subprocess.CalledProcessError:
            return (
                "Error: Unable to get git status. Make sure you're in a git repository."
            )


def main():
    parser = GitDiffParser()
    parser.process_diff()

    # Print git status
    print(parser.get_git_status())

    while True:
        suggestion = parser.get_suggested_commit_message()
        if suggestion:
            print(f"Suggestion: {suggestion}")
        else:
            print("No suggestion available.")

        user_input = input("Input: ").strip()
        if not user_input:
            break

        parser.add_user_input(user_input)


if __name__ == "__main__":
    main()
