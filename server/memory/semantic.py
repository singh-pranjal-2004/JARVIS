"""
Tier 3: Semantic Memory (The Profile)

Manages stark_profile.json — a structured file of long-term facts about the user.
JARVIS autonomously updates this via the update_profile tool when the user mentions
preferences, projects, or personal facts.

This is NOT a conversation log. It's a living document of who the user is.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from server.config import PROFILE_PATH


# Default profile structure for first-time setup
DEFAULT_PROFILE = {
    "name": "",
    "preferred_languages": [],
    "active_projects": [],
    "preferences": {
        "communication_style": "concise, technical",
        "model_preference": "gpt-4o-mini",
        "address_as": "Sir"
    },
    "facts": [],
    "skills": [],
    "last_updated": ""
}


class SemanticMemory:
    """Manages the user's persistent profile (stark_profile.json)."""

    def __init__(self):
        self._path = Path(PROFILE_PATH)
        self._profile = self._load_or_create()

    def _load_or_create(self) -> dict:
        """Load existing profile or create a fresh one."""
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Corrupted file — back up and recreate
                backup = self._path.with_suffix(".json.bak")
                self._path.rename(backup)
                return self._create_default()
        return self._create_default()

    def _create_default(self) -> dict:
        """Create and save a default profile. Uses the template if available."""
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Check for a pre-loaded template (stark_profile.default.json)
        template_path = self._path.parent / "stark_profile.default.json"
        if template_path.exists():
            try:
                with open(template_path, "r", encoding="utf-8") as f:
                    profile = json.load(f)
                self._save(profile)
                return profile
            except (json.JSONDecodeError, IOError):
                pass

        self._save(DEFAULT_PROFILE)
        return DEFAULT_PROFILE.copy()

    def _save(self, profile: Optional[dict] = None):
        """Persist the profile to disk."""
        data = profile or self._profile
        data["last_updated"] = datetime.now().isoformat()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_profile(self) -> dict:
        """Return the full profile."""
        return self._profile.copy()

    def get_context_string(self) -> str:
        """
        Format the profile as a context string for injection into the system prompt.
        The Brain calls this before every API request.
        """
        p = self._profile
        parts = ["[USER PROFILE — KNOWN FACTS]"]

        if p.get("name"):
            parts.append(f"- Name: {p['name']}")

        if p.get("preferred_languages"):
            parts.append(f"- Preferred languages: {', '.join(p['preferred_languages'])}")

        if p.get("active_projects"):
            for proj in p["active_projects"]:
                parts.append(f"- Active project: {proj.get('name', '?')} — {proj.get('description', '?')} (Status: {proj.get('status', '?')})")

        prefs = p.get("preferences", {})
        if prefs:
            parts.append(f"- Address user as: {prefs.get('address_as', 'Sir')}")
            parts.append(f"- Communication style: {prefs.get('communication_style', 'concise')}")

        if p.get("skills"):
            parts.append(f"- Known skills: {', '.join(p['skills'])}")

        if p.get("facts"):
            for fact in p["facts"][-10:]:  # Last 10 facts to keep it concise
                parts.append(f"- Fact: {fact.get('fact', '')} (learned: {fact.get('learned_on', '?')})")

        if len(parts) <= 1:
            return ""

        return "\n".join(parts)

    # --- Update methods (called by the update_profile tool) ---

    def update_name(self, name: str) -> str:
        """Update the user's name."""
        self._profile["name"] = name
        self._save()
        return f"Profile updated: name set to '{name}'."

    def add_fact(self, fact: str) -> str:
        """Add a new fact about the user."""
        entry = {
            "fact": fact,
            "learned_on": datetime.now().strftime("%Y-%m-%d")
        }

        # Avoid exact duplicates
        existing_facts = [f["fact"].lower() for f in self._profile.get("facts", [])]
        if fact.lower() in existing_facts:
            return f"Profile note: fact already recorded — '{fact}'."

        self._profile.setdefault("facts", []).append(entry)
        self._save()
        return f"Profile updated: new fact recorded — '{fact}'."

    def add_language(self, language: str) -> str:
        """Add a preferred programming language."""
        langs = self._profile.setdefault("preferred_languages", [])
        if language not in langs:
            langs.append(language)
            self._save()
            return f"Profile updated: '{language}' added to preferred languages."
        return f"Profile note: '{language}' already in preferred languages."

    def add_project(self, name: str, description: str = "",
                    status: str = "active") -> str:
        """Add or update an active project."""
        projects = self._profile.setdefault("active_projects", [])

        # Update if project exists
        for proj in projects:
            if proj.get("name", "").lower() == name.lower():
                proj["description"] = description or proj.get("description", "")
                proj["status"] = status
                self._save()
                return f"Profile updated: project '{name}' updated."

        # Otherwise add new
        projects.append({
            "name": name,
            "description": description,
            "status": status
        })
        self._save()
        return f"Profile updated: project '{name}' added."

    def update_preference(self, key: str, value: Any) -> str:
        """Update a user preference."""
        self._profile.setdefault("preferences", {})[key] = value
        self._save()
        return f"Profile updated: preference '{key}' set to '{value}'."

    def add_skill(self, skill: str) -> str:
        """Add a known skill."""
        skills = self._profile.setdefault("skills", [])
        if skill not in skills:
            skills.append(skill)
            self._save()
            return f"Profile updated: skill '{skill}' recorded."
        return f"Profile note: skill '{skill}' already known."

    def update_from_instruction(self, field: str, action: str,
                                value: Any) -> str:
        """
        Generic profile update dispatched by the brain's tool call.
        
        Args:
            field: One of 'name', 'fact', 'language', 'project', 'preference', 'skill'
            action: 'set', 'add', or 'update'
            value: The value to set/add. For 'project', should be a dict with 'name', 'description', 'status'.
        """
        if field == "name":
            return self.update_name(str(value))
        elif field == "fact":
            return self.add_fact(str(value))
        elif field == "language":
            return self.add_language(str(value))
        elif field == "project":
            if isinstance(value, dict):
                return self.add_project(**value)
            return self.add_project(name=str(value))
        elif field == "preference":
            if isinstance(value, dict):
                for k, v in value.items():
                    self.update_preference(k, v)
                return f"Profile updated: preferences updated."
            return "Profile error: preference value must be a dict."
        elif field == "skill":
            return self.add_skill(str(value))
        else:
            return f"Profile error: unknown field '{field}'."

    def __repr__(self) -> str:
        facts_count = len(self._profile.get("facts", []))
        projects_count = len(self._profile.get("active_projects", []))
        return f"SemanticMemory(facts={facts_count}, projects={projects_count})"
