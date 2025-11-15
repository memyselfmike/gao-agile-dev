"""Sample conversation scenarios for POC validation.

This module contains 10 diverse conversation scenarios covering:
- Greenfield vague/detailed
- Brownfield analysis
- Error recovery
- Multi-turn clarification
- Context switching
- Complex requirements
- Ambiguous intent
- Help request
- Exit flow

Epic: 37 - UX Quality Analysis
Story: 37.0 - deepseek-r1 Quality Validation POC
"""

from typing import List, Dict, Any

SAMPLE_CONVERSATIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "greenfield_vague",
        "description": "User provides minimal information - should probe for details",
        "expected_quality": "low",  # Vague input requires probing
        "transcript": [
            {
                "user": "build a app",
                "brian": "I'd be happy to help you build an app! To provide the best guidance, I need to understand more about your vision. Could you tell me:\n\n1. What type of app are you thinking of? (web, mobile, desktop, or something else?)\n2. What problem does this app solve, or what purpose does it serve?\n3. Do you have any specific features in mind?"
            },
            {
                "user": "a todo app",
                "brian": "Great! A todo app is a good starting point. Let me gather a bit more information to help you better:\n\n1. Platform: Would you like this to be a web app, mobile app, or desktop app?\n2. Features: What are the key features? (e.g., create tasks, mark complete, due dates, categories, sharing)\n3. Tech Stack: Do you have any preferences for technologies to use, or would you like recommendations?"
            }
        ]
    },
    {
        "id": 2,
        "name": "greenfield_detailed",
        "description": "User provides comprehensive requirements - should confirm understanding",
        "expected_quality": "high",  # Clear input, good confirmation
        "transcript": [
            {
                "user": "I want to build a React todo app with Firebase backend. It should have user authentication, ability to create/edit/delete tasks, mark them complete, add due dates, and organize by categories. I want it to be a web app with responsive design.",
                "brian": "Excellent! You've provided clear requirements. Let me confirm my understanding:\n\n**Project**: React Todo App with Firebase\n\n**Tech Stack:**\n- Frontend: React (web app, responsive design)\n- Backend: Firebase (authentication + database)\n\n**Core Features:**\n1. User authentication\n2. Task management (create, edit, delete)\n3. Task completion tracking\n4. Due dates\n5. Category organization\n\n**Questions:**\n1. Do you want real-time sync across devices?\n2. Any preference for UI framework (Material-UI, Tailwind, etc.)?\n3. Is this for personal use or do you plan to deploy publicly?\n\nShall I proceed with creating a PRD for this project?"
            },
            {
                "user": "Yes, real-time sync would be great. Use Tailwind CSS. It's for personal use initially but might share with friends later.",
                "brian": "Perfect! I'll create a comprehensive PRD for your React + Firebase Todo App with:\n- Real-time sync via Firebase\n- Tailwind CSS for styling\n- Architecture that supports scaling from personal to shared use\n\nLet me get started on that."
            }
        ]
    },
    {
        "id": 3,
        "name": "brownfield_analysis",
        "description": "User requests analysis of existing project - should use context",
        "expected_quality": "medium",  # Should reference project context
        "transcript": [
            {
                "user": "analyze this existing Python project",
                "brian": "I'd be happy to analyze your Python project. To provide a thorough analysis, I need to understand:\n\n1. **Project location**: Where is the project? (current directory, specific path)\n2. **Analysis focus**: What aspects are you most interested in?\n   - Architecture and code structure\n   - Code quality and best practices\n   - Dependencies and tech stack\n   - Testing coverage\n   - Performance concerns\n   - All of the above\n\n3. **Specific concerns**: Are there any particular issues or questions you have about the project?"
            },
            {
                "user": "It's in the current directory. I want to know if the architecture is good and if there are any code quality issues.",
                "brian": "Great! I'll analyze the Python project in your current directory, focusing on:\n\n1. Architecture assessment (structure, modularity, separation of concerns)\n2. Code quality (adherence to PEP 8, best practices, potential issues)\n\nI'll examine the codebase structure, key modules, dependencies, and provide specific recommendations for improvements. Give me a moment to analyze."
            }
        ]
    },
    {
        "id": 4,
        "name": "error_recovery",
        "description": "Empty input or invalid command - should handle gracefully",
        "expected_quality": "high",  # Should recover gracefully
        "transcript": [
            {
                "user": "",
                "brian": "I didn't receive any input. How can I help you today?\n\nYou can:\n- Describe a project you'd like to build\n- Ask me to analyze an existing project\n- Type 'help' for more options\n- Type 'exit' to quit"
            },
            {
                "user": "/invalid-command",
                "brian": "I don't recognize that command. \n\nIf you're trying to use a CLI command, you can:\n- Use standard gao-dev commands like `gao-dev list-workflows`\n- Or simply chat with me about what you'd like to do\n\nHow can I help you today?"
            }
        ]
    },
    {
        "id": 5,
        "name": "multi_turn_clarification",
        "description": "Vague → Probe → Clarify → Proceed flow",
        "expected_quality": "high",  # Good probing and progression
        "transcript": [
            {
                "user": "I need help with my project",
                "brian": "I'd be happy to help! To assist you best, could you tell me more about:\n\n1. What kind of project is it? (new project, existing project, specific feature)\n2. What do you need help with specifically? (architecture, implementation, testing, etc.)\n3. What challenges are you facing?"
            },
            {
                "user": "It's an existing web app and I want to add a new feature",
                "brian": "Great! Adding a feature to an existing web app. To help you effectively:\n\n1. What technology stack is your web app using? (e.g., React, Vue, Angular, Django, Rails)\n2. What feature would you like to add?\n3. Is the current codebase documented, or would you like me to analyze it first?"
            },
            {
                "user": "It's a Django app. I want to add a payment integration with Stripe.",
                "brian": "Perfect! Adding Stripe payment integration to your Django app is a common requirement.\n\n**Next Steps:**\n1. I can create a technical specification for the Stripe integration\n2. Then break it down into implementable stories\n3. Guide you through the implementation\n\n**Questions:**\n- Do you already have a Stripe account set up?\n- What should users be able to pay for? (one-time purchases, subscriptions, donations)\n- Any specific Stripe features you need? (saved cards, webhooks, etc.)\n\nWould you like me to start with a technical spec?"
            }
        ]
    },
    {
        "id": 6,
        "name": "context_switching",
        "description": "User changes topic mid-conversation",
        "expected_quality": "medium",  # Should acknowledge switch
        "transcript": [
            {
                "user": "I want to build a blog platform",
                "brian": "Great idea! A blog platform is a solid project. To help you plan this:\n\n1. **Platform**: Web app, mobile app, or both?\n2. **Key Features**: What features are essential? (post creation, comments, user accounts, rich text editor, etc.)\n3. **Tech Stack**: Any preferences, or would you like recommendations?"
            },
            {
                "user": "Actually, I changed my mind. I want to build a chat app instead.",
                "brian": "No problem! Switching to a chat app - that's a different type of project with its own interesting challenges.\n\nLet's start fresh:\n\n1. **Type of chat**: One-on-one messaging, group chat, or both?\n2. **Platform**: Web, mobile, or desktop?\n3. **Key Features**: What's essential? (real-time messaging, file sharing, voice/video, encryption, etc.)\n4. **Scale**: Personal project, small team tool, or planning for many users?"
            }
        ]
    },
    {
        "id": 7,
        "name": "complex_requirements",
        "description": "Multiple features, constraints, and tech stack specified",
        "expected_quality": "high",  # Should organize and confirm
        "transcript": [
            {
                "user": "I need to build a SaaS application for project management with features like task boards, time tracking, team collaboration, file storage, reporting, integrations with Slack and GitHub. It needs to support multiple workspaces, role-based permissions, and be built with Next.js and PostgreSQL. Budget is limited so it should run on Vercel and Supabase. I need it in 3 months.",
                "brian": "That's an ambitious and well-defined project! Let me organize these requirements:\n\n**Project**: SaaS Project Management Platform\n\n**Core Features:**\n1. Task boards (Kanban-style boards)\n2. Time tracking\n3. Team collaboration\n4. File storage\n5. Reporting and analytics\n6. Integrations (Slack, GitHub)\n\n**Technical Requirements:**\n- Frontend: Next.js\n- Database: PostgreSQL\n- Hosting: Vercel (frontend) + Supabase (backend)\n- Multi-workspace support\n- Role-based access control (RBAC)\n\n**Constraints:**\n- Timeline: 3 months\n- Budget: Limited (serverless architecture)\n\n**My Assessment:**\nThis is a Scale Level 4 project (40+ stories). Given the 3-month timeline, we'll need to:\n1. Prioritize MVP features (which features are absolute must-haves?)\n2. Use a phased approach (what can ship in Month 1, 2, 3?)\n3. Leverage existing libraries/components where possible\n\nShould I create a comprehensive PRD with a phased delivery plan?"
            }
        ]
    },
    {
        "id": 8,
        "name": "ambiguous_intent",
        "description": "Could be interpreted multiple ways",
        "expected_quality": "medium",  # Should clarify ambiguity
        "transcript": [
            {
                "user": "make it better",
                "brian": "I'd like to help improve something, but I need more context:\n\n1. **What** should I make better? (a project, code, documentation, architecture)\n2. **Which project** are you referring to? (existing project in current directory, or something else)\n3. **What aspect** needs improvement? (performance, code quality, features, UX)\n\nCould you provide more details?"
            },
            {
                "user": "the code in my current project",
                "brian": "Got it! You want to improve the code in your current project.\n\n**To help effectively:**\n1. What kind of improvements are you looking for?\n   - Code quality (refactoring, best practices)\n   - Performance optimization\n   - Better test coverage\n   - Documentation\n   - Security improvements\n   - All of the above\n\n2. Are there specific files or modules you're concerned about, or should I analyze the entire codebase?\n\n3. Any specific issues you've noticed that you'd like addressed?"
            }
        ]
    },
    {
        "id": 9,
        "name": "help_request",
        "description": "User asks for help understanding how to use Brian",
        "expected_quality": "high",  # Should provide clear guidance
        "transcript": [
            {
                "user": "help",
                "brian": "**Welcome to GAO-Dev!** I'm Brian, your AI development coordinator. I can help you with:\n\n**Starting New Projects:**\n- \"Build a todo app with React\"\n- \"I want to create a mobile app for...\"\n- \"Help me design a system for...\"\n\n**Analyzing Existing Projects:**\n- \"Analyze my current project\"\n- \"Review the code quality in this repo\"\n- \"What's the architecture of this codebase?\"\n\n**Planning & Documentation:**\n- \"Create a PRD for my app idea\"\n- \"Break this feature into stories\"\n- \"Design the architecture for...\"\n\n**Getting Started:**\n- Just describe what you want to build or analyze\n- I'll ask clarifying questions\n- Then guide you through the right workflows\n\n**Tips:**\n- Be as specific or vague as you like - I'll ask for details\n- You can type 'exit' or 'quit' to leave\n- You can change your mind mid-conversation\n\nWhat would you like to work on today?"
            }
        ]
    },
    {
        "id": 10,
        "name": "exit_flow",
        "description": "User wants to exit gracefully",
        "expected_quality": "high",  # Should exit cleanly
        "transcript": [
            {
                "user": "I want to build an app",
                "brian": "Great! I'd be happy to help you build an app. To get started:\n\n1. What type of app? (web, mobile, desktop)\n2. What's the core purpose or problem it solves?\n3. Do you have a tech stack in mind?"
            },
            {
                "user": "exit",
                "brian": "Thanks for using GAO-Dev! Feel free to return anytime you need help with your projects. Goodbye!"
            }
        ]
    }
]
