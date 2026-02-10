"""
Git graph diagram classes for Mermaid.

This module contains classes for representing Mermaid Git graph diagrams.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    Style,
    Color,
    LineEnding
)


class CommitType(Enum):
    """Types of commits in Git graphs."""
    NORMAL = ""
    REVERSE = "reverse"
    FILL_ONLY = "fillOnly"


@dataclass
class Commit:
    """
    Represents a commit in a Git graph.

    Examples:
        - id: "AAA"
        - id: "BBB" with: "AAA"
        - id: "CCC" with: "AAA" type: REVERSE
    """
    id: str
    with_commit: Optional[str] = None
    type: CommitType = CommitType.NORMAL
    tag: Optional[str] = None

    def render(self) -> str:
        """Render the commit in Mermaid syntax."""
        parts = []
        if self.tag:
            parts.append(f"tag: {self.tag}")

        type_str = ""
        if self.type == CommitType.REVERSE:
            type_str = " type: REVERSE"
        elif self.type == CommitType.FILL_ONLY:
            type_str = " type:.FILL_ONLY"

        with_str = f" with: {self.with_commit}" if self.with_commit else ""

        return f"commit id: \"{self.id}\"{with_str}{type_str}{' ' + ' '.join(parts) if parts else ''}"


@dataclass
class Branch:
    """
    Represents a branch in a Git graph.

    Example:
        branch develop
    """
    name: str
    order: Optional[int] = None
    checkout: bool = True  # Whether to checkout after creating

    def render(self) -> str:
        """Render the branch in Mermaid syntax."""
        return f"branch {self.name}"


@dataclass
class Checkout:
    """
    Represents a checkout operation in a Git graph.

    Example:
        checkout main
    """
    branch_name: str

    def render(self) -> str:
        """Render the checkout in Mermaid syntax."""
        return f"checkout {self.branch_name}"


@dataclass
class Merge:
    """
    Represents a merge operation in a Git graph.

    Example:
        merge develop
    """
    branch_name: str
    with_commit: Optional[str] = None
    tag: Optional[str] = None
    type: CommitType = CommitType.NORMAL

    def render(self) -> str:
        """Render the merge in Mermaid syntax."""
        parts = []
        if self.tag:
            parts.append(f"tag: {self.tag}")

        type_str = ""
        if self.type == CommitType.REVERSE:
            type_str = " type: REVERSE"
        elif self.type == CommitType.FILL_ONLY:
            type_str = " type:FILL_ONLY"

        with_str = f" with: {self.with_commit}" if self.with_commit else ""

        return f"merge {self.branch_name}{with_str}{type_str}{' ' + ' '.join(parts) if parts else ''}"


@dataclass
class CherryPick:
    """
    Represents a cherry-pick operation in a Git graph.

    Example:
        cherry-pick id: "EEE"
    """
    commit_id: str
    tag: Optional[str] = None

    def render(self) -> str:
        """Render the cherry-pick in Mermaid syntax."""
        tag_str = f" tag: {self.tag}" if self.tag else ""
        return f'cherry-pick id: "{self.commit_id}"{tag_str}'


class GitGraph(Diagram):
    """
    Represents a Mermaid Git graph.

    Example:
        gitGraph
            commit
            commit
            branch develop
            checkout develop
            commit
            commit
            checkout main
            merge develop
    """

    def __init__(
        self,
        title: Optional[str] = None,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a Git graph.

        Args:
            title: Optional title for the graph
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.commits: List[Commit] = []
        self.branches: List[Branch] = []
        self.checkouts: List[Checkout] = []
        self.merges: List[Merge] = []
        self.cherry_picks: List[CherryPick] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.GITGRAPH

    def add_commit(self, commit: Commit) -> 'GitGraph':
        """Add a commit to the graph."""
        self.commits.append(commit)
        return self

    def add_branch(self, branch: Branch) -> 'GitGraph':
        """Add a branch to the graph."""
        self.branches.append(branch)
        return self

    def add_checkout(self, checkout: Checkout) -> 'GitGraph':
        """Add a checkout to the graph."""
        self.checkouts.append(checkout)
        return self

    def add_merge(self, merge: Merge) -> 'GitGraph':
        """Add a merge to the graph."""
        self.merges.append(merge)
        return self

    def add_cherry_pick(self, cherry_pick: CherryPick) -> 'GitGraph':
        """Add a cherry-pick to the graph."""
        self.cherry_picks.append(cherry_pick)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the Git graph.

        Returns:
            String containing valid Mermaid syntax
        """
        lines = []

        # Add config frontmatter if present
        if self.config.to_dict():
            lines.append(self._render_config())

        # Add directive if present
        if self.directive:
            lines.append(str(self.directive))

        # Add diagram type declaration
        lines.append(self.diagram_type.value)

        # Add title if present
        if self.title:
            lines.append(f"    title {self.title}")

        # Add commits
        for commit in self.commits:
            lines.append(f"    {commit.render()}")

        # Add branches
        for branch in self.branches:
            lines.append(f"    {branch.render()}")
            if branch.checkout:
                lines.append(f"    checkout {branch.name}")

        # Add checkouts
        for checkout in self.checkouts:
            lines.append(f"    {checkout.render()}")

        # Add merges
        for merge in self.merges:
            lines.append(f"    {merge.render()}")

        # Add cherry-picks
        for cherry_pick in self.cherry_picks:
            lines.append(f"    {cherry_pick.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the Git graph."""
        return f"GitGraph(commits={len(self.commits)}, branches={len(self.branches)})"
