def run_interactive_menu(debug: bool = True, max_iterations: int = 10, max_rounds: int = 5, skip_boot: bool = False):
    """
    Run interactive menu mode - user selects agent mode.
    """
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     ████████╗███████╗███████╗██╗ ██████╗██╗     ██╗ ██████╗       ║
║     ╚══██╔══╝██╔════╝██╔════╝██║██╔════╝██║     ██║██╔═══██╗      ║
║        ██║   █████╗  █████╗  ██║██║     ██║     ██║██║   ██║      ║
║        ██║   ██╔══╝  ██╔══╝  ██║██║     ██║     ██║██║   ██║      ║
║        ██║   ███████╗███████╗██║╚██████╗███████╗██║╚██████╔╝      ║
║        ╚═╝   ╚══════╝╚══════╝╚═╝ ╚═════╝╚══════╝╚═╝ ╚═════╝       ║
║                                                                   ║
║                       ZEJZL.NET - INITIALIZED                     ║
║            AI FRAMEWORK CLI - PANTHEON 9-AGENT SYSTEM             ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

        [INTERACTIVE MODE] Welcome to zejzl.net - Choose your agent mode!

        1. Single Agent (Grok only) - Observe-Reason-Act loop
        2. Collaboration Mode (Grok + Claude) - Dual AI planning
        3. Swarm Mode (Multi-agent) - Async team coordination
        4. Pantheon Mode (9-agent) - Full AI orchestration with validation & learning
        5. Improver Manual - Run self-improvement on specific session/log
        6. Offline Mode - Cached/local fallback (no API, uses vault/KB)
        7. Community Vault Sync - Pull/push evolutions and tools
        8. Save Game - Invoke progress save script
        9. Quit
""")

    choice = input("        Choose mode (1-9): ").strip()
    return choice
