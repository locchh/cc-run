"""
Claude Agent SDK Skills Documentation

When using the Claude Agent SDK, Skills are:

Defined as filesystem artifacts: Created as SKILL.md files in specific directories (.claude/skills/)

Loaded from filesystem: Skills are loaded from configured filesystem locations.

You must specify settingSources (TypeScript) or setting_sources (Python) to load Skills from the filesystem

Automatically discovered: Once filesystem settings are loaded, Skill metadata is discovered at startup from user and project directories; 
full content loaded when triggered

Model-invoked: Claude autonomously chooses when to use them based on context

Enabled via allowed_tools: Add "Skill" to your allowed_tools to enable 
Skills

Unlike subagents (which can be defined programmatically), Skills must be created as filesystem artifacts. The SDK does not provide a programmatic API for registering Skills.

Default behavior: By default, the SDK does not load any filesystem settings.
To use Skills, you must explicitly configure 
`settingSources=['user', 'project']` (TypeScript) or 
`setting_sources=['user', 'project']` (Python) in your options.
"""

from dotenv import load_dotenv

load_dotenv()
