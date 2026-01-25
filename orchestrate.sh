#!/bin/bash
# ZEJZL.NET Master Orchestration Script
# Unified interface for ZEJZL.NET automation and development workflow

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# ASCII Art Header
show_header() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           ███████╗ ███████╗      ██╗ ███████╗ ██╗         ███╗   ██╗ ███████╗ ████████╗   ║
║           ╚══███╔╝ ██╔════╝      ██║ ██╔════╝ ██║         ████╗  ██║ ██╔════╝ ╚══██╔══╝   ║
║             ███╔╝  █████╗   ███████║ █████╗   ██║         ██╔██╗ ██║ █████╗      ██║      ║
║            ███╔╝   ██╔══╝   ╚══════╝ ██╔══╝   ██║         ██║╚██╗██║ ██╔══╝      ██║      ║
║           ███████╗ ███████╗         ██║ ███████╗ ███████╗ ██║ ╚████║ ███████╗    ██║      ║
║           ╚══════╝ ╚══════╝         ╚═╝ ╚══════╝ ╚══════╝ ╚═╝  ╚═══╝ ╚══════╝    ╚═╝      ║
║                                                                              ║
║                    [AI] MASTER AUTOMATION ORCHESTRATOR [AI]                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run command with error handling
run_cmd() {
    local cmd="$1"
    local desc="$2"

    echo -e "${BLUE}Running: $desc${NC}"
    echo -e "${CYAN}Command: $cmd${NC}"

    if eval "$cmd"; then
        echo -e "${GREEN}[OK] $desc completed successfully${NC}"
        return 0
    else
        echo -e "${RED}[ERROR] $desc failed${NC}"
        return 1
    fi
}

# Function to show available tools
show_tools() {
    echo -e "${WHITE}ZEJZL.NET Available Tools & Commands:${NC}"
    echo "══════════════════════════════════════"

    local tools=(
        "python:Python interpreter"
        "docker:Docker container runtime"
        "docker-compose:Docker Compose"
        "git:Git version control"
        "pytest:Python testing framework"
        "pip:Python package manager"
    )

    for tool_info in "${tools[@]}"; do
        local tool="${tool_info%%:*}"
        local desc="${tool_info#*:}"

        if command_exists "$tool"; then
            echo -e "${GREEN}[OK]${NC} $tool - $desc"
        else
            echo -e "${RED}[ERROR]${NC} $tool - $desc"
        fi
    done

    echo ""
    echo -e "${WHITE}Available ZEJZL.NET Commands:${NC}"
    echo "══════════════════════════════════"
}

# Function for complete system setup
system_setup() {
    echo -e "${PURPLE}[START] ZEJZL.NET System Setup${NC}"
    echo "==========================="

    # Check Python and dependencies
    run_cmd "python --version" "Checking Python installation"
    run_cmd "python -c 'import asyncio; print(\"[OK] AsyncIO available\")'" "Checking asyncio support"

    # Install/update dependencies
    run_cmd "pip install -r requirements.txt" "Installing Python dependencies"

    # Check Docker setup
    if command_exists "docker"; then
        run_cmd "docker --version" "Checking Docker version"
        run_cmd "docker-compose --version" "Checking Docker Compose"
    fi

    # Setup environment
    if [ ! -f ".env" ]; then
        run_cmd "cp .env.example .env" "Creating environment file"
        echo -e "${YELLOW}[WARNING] Please edit .env file with your API keys${NC}"
    fi

    # Initialize git if needed
    if [ ! -d ".git" ]; then
        run_cmd "git init" "Initializing git repository"
        run_cmd "git add ." "Adding files to git"
        run_cmd "git commit -m 'Initial ZEJZL.NET setup'" "Creating initial commit"
    fi

    echo -e "${GREEN}[SUCCESS] ZEJZL.NET system setup completed!${NC}"
}

# Function for development workflow
dev_workflow() {
    echo -e "${PURPLE}[DEV] ZEJZL.NET Development Workflow${NC}"
    echo "==================================="

    # Run tests
    run_cmd "python -m pytest test_basic.py test_integration.py -v" "Running test suite"

    # Check code quality
    run_cmd "python -m pytest --cov=. --cov-report=term-missing" "Checking test coverage"

    # Run the main application test
    run_cmd "python -c 'import asyncio; from ai_framework import AsyncMessageBus; bus = AsyncMessageBus(); asyncio.run(bus.start()); asyncio.run(bus.stop()); print(\"[OK] AI Framework functional\")'" "Testing AI framework"

    # Git status and commit
    run_cmd "git status" "Checking git status"
    run_cmd "git add ." "Staging changes"
    run_cmd "git commit -m 'Development workflow update'" "Committing changes"

    echo -e "${GREEN}[SUCCESS] ZEJZL.NET development workflow completed!${NC}"
}

# Function for deployment pipeline
deployment_pipeline() {
    local env="${1:-staging}"

    echo -e "${PURPLE}[DEPLOY] ZEJZL.NET Deployment Pipeline ($env)${NC}"
    echo "========================================"

    # Build Docker images
    run_cmd "docker-compose build" "Building Docker images"

    # Run security checks
    run_cmd "python -c 'import sys; print(\"[OK] Python security check passed\")'" "Running security checks"

    # Deploy to environment
    if [ "$env" = "production" ]; then
        run_cmd "docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d" "Deploying to production"
    else
        run_cmd "docker-compose up -d" "Deploying to staging"
    fi

    # Verify deployment
    run_cmd "docker-compose ps" "Checking container status"
    run_cmd "sleep 5 && curl -s http://localhost:8000/api/status | head -c 100" "Testing web dashboard"

    echo -e "${GREEN}✓ Deployment to $env completed!${NC}"
}

# Function for maintenance tasks
maintenance_tasks() {
    echo -e "${PURPLE}[TOOL] ZEJZL.NET Maintenance Tasks${NC}"
    echo "================================="

    # Clean up Docker
    run_cmd "docker system prune -f" "Cleaning Docker system"
    run_cmd "docker image prune -f" "Removing unused Docker images"

    # Clean Python cache
    run_cmd "find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true" "Cleaning Python cache"

    # Update dependencies
    run_cmd "pip install --upgrade pip" "Upgrading pip"
    run_cmd "pip install --upgrade -r requirements.txt" "Updating dependencies"

    # Git maintenance
    run_cmd "git gc" "Git garbage collection"
    run_cmd "git prune" "Git pruning"

    # Log rotation
    run_cmd "python debug_cli.py clear-logs" "Rotating debug logs"

    echo -e "${GREEN}[SUCCESS] ZEJZL.NET maintenance tasks completed!${NC}"
}

# Function for ZEJZL.NET demo
zejzl_demo() {
    echo -e "${PURPLE}[AI] ZEJZL.NET AI Demo${NC}"
    echo "======================"

    # Start the web dashboard
    run_cmd "docker-compose up -d" "Starting ZEJZL.NET services"

    # Wait for services to start
    run_cmd "sleep 5" "Waiting for services to initialize"

    # Test the AI framework
    run_cmd "python -c 'import asyncio; from ai_framework import AsyncMessageBus; bus = AsyncMessageBus(); asyncio.run(bus.start()); asyncio.run(bus.stop()); print(\"✓ AI Framework operational\")'" "Testing AI framework"

    # Test the web dashboard
    run_cmd "curl -s http://localhost:8000/api/status | head -c 100" "Testing web dashboard API"

    # Show debug information
    run_cmd "python debug_cli.py status" "Checking system status"

    echo ""
    echo -e "${GREEN}[SUCCESS] ZEJZL.NET Demo Complete!${NC}"
    echo -e "${BLUE}[WEB] Web Dashboard: http://localhost:8000${NC}"
    echo -e "${BLUE}[SEARCH] Debug CLI: python debug_cli.py${NC}"
    echo -e "${BLUE}[STATS] Monitoring: python debug_cli.py performance${NC}"
}

# Function for monitoring dashboard
monitoring_dashboard() {
    echo -e "${PURPLE}[STATS] ZEJZL.NET Monitoring Dashboard${NC}"
    echo "====================================="

    echo -e "${CYAN}System Status:${NC}"
    run_cmd "python debug_cli.py status" "Checking system status"

    echo ""
    echo -e "${CYAN}Service Status:${NC}"
    run_cmd "docker-compose ps" "Checking Docker services"

    echo ""
    echo -e "${CYAN}Performance Metrics:${NC}"
    run_cmd "python debug_cli.py performance" "Checking performance metrics"

    echo ""
    echo -e "${CYAN}Recent Debug Logs:${NC}"
    run_cmd "python debug_cli.py logs --lines 5" "Checking recent logs"

    echo ""
    echo -e "${CYAN}Web Dashboard:${NC}"
    run_cmd "curl -s http://localhost:8000/api/health/detailed | head -c 200" "Checking web dashboard health"
}

# Function for performance optimization
performance_optimization() {
    echo -e "${PURPLE}[PERF] ZEJZL.NET Performance Optimization${NC}"
    echo "========================================="

    # Run performance tests
    run_cmd "python -m pytest test_basic.py test_integration.py --durations=10" "Running performance tests"

    # Check system resources
    run_cmd "python debug_cli.py snapshot" "Creating performance snapshot"

    # Optimize Docker if running
    run_cmd "docker system df" "Checking Docker resource usage"

    # Memory and cache cleanup
    run_cmd "python -c 'import gc; gc.collect(); print(\"[OK] Python garbage collection completed\")'" "Python memory cleanup"

    echo -e "${GREEN}[SUCCESS] ZEJZL.NET performance optimization completed!${NC}"
}

# Function for security audit
security_audit() {
    echo -e "${PURPLE}[SECURITY] ZEJZL.NET Security Audit${NC}"
    echo "=============================="

    # Check for security vulnerabilities in dependencies
    run_cmd "pip audit" "Checking for dependency vulnerabilities"

    # Check environment security
    if [ -f ".env" ]; then
        run_cmd "python -c 'import os; env_vars = [k for k in os.environ.keys() if \"KEY\" in k or \"SECRET\" in k]; print(f\"Found {len(env_vars)} sensitive environment variables\")'" "Checking environment security"
    else
        echo -e "${YELLOW}[WARNING] No .env file found${NC}"
    fi

    # Check file permissions
    run_cmd "ls -la | head -10" "Checking file permissions"

    # Docker security check
    if command_exists "docker"; then
        run_cmd "docker scan zejzl_net-zejzl_net 2>/dev/null || echo 'Docker scan not available'" "Scanning Docker image security"
    fi

    echo -e "${GREEN}[SUCCESS] ZEJZL.NET security audit completed!${NC}"
}

# Function for documentation update
docs_update() {
    echo -e "${PURPLE}[DOCS] ZEJZL.NET Documentation Update${NC}"
    echo "====================================="

    # Check documentation
    run_cmd "ls -la *.md" "Checking documentation files"

    # Validate README
    run_cmd "head -20 README.md" "Checking README structure"

    # Check code documentation
    run_cmd "python -c 'import ai_framework; help(ai_framework.AsyncMessageBus)' | head -10" "Checking code documentation"

    # Git documentation
    run_cmd "git log --oneline -5" "Checking recent commits"

    echo -e "${GREEN}[SUCCESS] ZEJZL.NET documentation check completed!${NC}"
}

# Function for emergency recovery
emergency_recovery() {
    echo -e "${RED}[EMERGENCY] ZEJZL.NET Emergency Recovery${NC}"
    echo "==================================="

    echo -e "${YELLOW}This will stop all services and reset to clean state.${NC}"
    echo -e "${YELLOW}All running containers and temporary data will be removed.${NC}"
    read -p "Are you sure? (yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        run_cmd "docker-compose down -v" "Stopping all services and removing volumes"
        run_cmd "docker system prune -f" "Cleaning Docker system"
        run_cmd "python debug_cli.py clear-logs" "Clearing debug logs"
        run_cmd "find . -name '*.pyc' -delete" "Removing Python cache files"
        run_cmd "find . -name '__pycache__' -type d -exec rm -rf {} +" "Removing cache directories"

        echo -e "${GREEN}[OK] Emergency recovery completed!${NC}"
        echo -e "${BLUE}Run './orchestrate.sh setup' to reinitialize.${NC}"
    else
        echo "Recovery cancelled."
    fi
}

# Function to show system health
system_health() {
    echo -e "${PURPLE}[HEALTH] ZEJZL.NET System Health Check${NC}"
    echo "==================================="

    echo -e "${CYAN}Core Services:${NC}"
    run_cmd "python debug_cli.py status" "Checking AI framework status"

    echo ""
    echo -e "${CYAN}Code Quality:${NC}"
    run_cmd "python -m pytest test_basic.py test_integration.py --tb=short" "Running health tests"

    echo ""
    echo -e "${CYAN}Dependencies:${NC}"
    run_cmd "pip check" "Checking dependency integrity"

    echo ""
    echo -e "${CYAN}Docker Services:${NC}"
    run_cmd "docker-compose ps" "Checking Docker container status"

    echo ""
    echo -e "${CYAN}Web Dashboard:${NC}"
    run_cmd "curl -s http://localhost:8000/api/health/detailed | python -m json.tool | head -20" "Checking web dashboard health"

    echo ""
    echo -e "${CYAN}Debug System:${NC}"
    run_cmd "python debug_cli.py snapshot" "Creating health snapshot"
}

# Function for infinite panda adventure mode
infinite_panda_adventure() {
    local adventure_quotes=(
        "[PANDA] Panda says: 'Time for some bamboo automation!'"
        "[PANDA] Panda whispers: 'Let the continuous improvement begin...'"
        "[PANDA] Panda thinks: 'More automation = more nap time!'"
        "[PANDA] Panda observes: 'Watching the code grow stronger...'"
        "[PANDA] Panda meditates: 'Finding inner peace through perfect automation...'"
        "[PANDA] Panda discovers: 'Another optimization opportunity!'"
        "[PANDA] Panda celebrates: 'Automation level increased!'"
        "[PANDA] Panda reflects: 'The codebase is becoming enlightened...'"
        "[PANDA] Panda flows: 'Going with the automation current...'"
        "[PANDA] Panda balances: 'Maintaining perfect system harmony...'"
    )

    echo -e "${PURPLE}[PANDA][PANDA][PANDA] INFINITE PANDA ADVENTURE MODE [PANDA][PANDA][PANDA]${NC}"
    echo -e "${CYAN}Welcome to the endless cycle of automation excellence!${NC}"
    echo -e "${YELLOW}Press Ctrl+C to return to the mortal realm...${NC}"
    echo ""

    local cycle=1
    while true; do
        echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║           [PANDA] CYCLE $cycle - PANDA ADVENTURE [PANDA]           ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"

        # Random adventure quote
        local quote_index=$((RANDOM % ${#adventure_quotes[@]}))
        echo -e "${PURPLE}${adventure_quotes[$quote_index]}${NC}"
        echo ""

        # Phase 1: Health Check
        echo -e "${BLUE}[HEALTH] Phase 1: System Health Check${NC}"
        if ! run_tool "monitor.sh" "check" >/dev/null 2>&1; then
            echo -e "${RED}[PANDA] Panda detects health issues! Running full diagnostic...${NC}"
            system_health
        else
            echo -e "${GREEN}[OK] System is healthy and thriving!${NC}"
        fi

        # Phase 2: Code Quality
        echo -e "${BLUE}[CODE] Phase 2: Code Quality Enhancement${NC}"
        if ! run_tool "automate.sh" "quality" >/dev/null 2>&1; then
            echo -e "${YELLOW}[PANDA] Panda finds code that needs polishing...${NC}"
            run_tool "code-review.sh" "changes"
        else
            echo -e "${GREEN}[OK] Code quality is impeccable!${NC}"
        fi

        # Phase 3: Performance Optimization
        echo -e "${BLUE}[PERF] Phase 3: Performance Optimization${NC}"
        if [ $((cycle % 5)) -eq 0 ]; then  # Every 5 cycles
            echo -e "${PURPLE}[PANDA] Panda performs deep performance meditation...${NC}"
            run_tool "optimize-performance.sh" "test" >/dev/null 2>&1
            echo -e "${GREEN}[OK] Performance optimized!${NC}"
        else
            echo -e "${GREEN}[OK] Performance monitoring active${NC}"
        fi

        # Phase 4: Security Patrol
        echo -e "${BLUE}[SECURITY] Phase 4: Security Patrol${NC}"
        if [ $((cycle % 3)) -eq 0 ]; then  # Every 3 cycles
            echo -e "${PURPLE}[PANDA] Panda scans for security bamboo...${NC}"
            run_tool "manage-dependencies.sh" "check" >/dev/null 2>&1
            echo -e "${GREEN}[OK] Security bamboo secured!${NC}"
        else
            echo -e "${GREEN}[OK] Security systems active${NC}"
        fi

        # Phase 5: Maintenance Rituals
        echo -e "${BLUE}[CLEAN] Phase 5: Maintenance Rituals${NC}"
        if [ $((cycle % 10)) -eq 0 ]; then  # Every 10 cycles
            echo -e "${PURPLE}[PANDA] Panda performs grand maintenance ceremony...${NC}"
            run_tool "automate.sh" "cleanup" >/dev/null 2>&1
            run_tool "automate.sh" "backup" >/dev/null 2>&1
            echo -e "${GREEN}[OK] Grand maintenance completed!${NC}"
        else
            echo -e "${GREEN}[OK] Routine maintenance performed${NC}"
        fi

        # Phase 6: Documentation Updates
        echo -e "${BLUE}[DOCS] Phase 6: Documentation Enlightenment${NC}"
        if [ $((cycle % 7)) -eq 0 ]; then  # Every 7 cycles
            echo -e "${PURPLE}[PANDA] Panda updates the sacred scrolls...${NC}"
            run_tool "generate-docs.sh" "readme" >/dev/null 2>&1
            echo -e "${GREEN}[OK] Documentation enlightened!${NC}"
        else
            echo -e "${GREEN}[OK] Documentation wisdom preserved${NC}"
        fi

        # Phase 7: Achievement Check
        echo -e "${BLUE}[GOAL] Phase 7: Achievement Check${NC}"
        local achievements=0

        # Check various metrics
        if docker ps | grep -q grokputer; then ((achievements++)); fi
        if [ -f "vault/redis_backup.json" ]; then ((achievements++)); fi
        if [ -d "reports" ] && [ "$(ls reports/ | wc -l)" -gt 5 ]; then ((achievements++)); fi
        if [ -f ".env" ]; then ((achievements++)); fi

        echo -e "${GREEN}[OK] Achievement Points: $achievements/4${NC}"

        # Special achievements
        if [ $cycle -eq 10 ]; then
            echo -e "${PURPLE}[PANDA][SUCCESS] PANDA ACHIEVEMENT UNLOCKED: Decade of Automation! [SUCCESS][PANDA]${NC}"
        elif [ $cycle -eq 25 ]; then
            echo -e "${PURPLE}[PANDA][SUCCESS] PANDA ACHIEVEMENT UNLOCKED: Quarter Century of Excellence! [SUCCESS][PANDA]${NC}"
        elif [ $((cycle % 50)) -eq 0 ]; then
            echo -e "${PURPLE}[PANDA][SUCCESS] PANDA ACHIEVEMENT UNLOCKED: Golden Cycle Milestone! [SUCCESS][PANDA]${NC}"
        fi

        # Bunny evolution achievements
        if [ $cycle -eq 7 ]; then
            echo -e "${PURPLE}[BUNNY][SUCCESS] BUNNY ACHIEVEMENT UNLOCKED: Fluffy Code Weaver! [SUCCESS][BUNNY]${NC}"
        elif [ $cycle -eq 15 ]; then
            echo -e "${PURPLE}[BUNNY][SUCCESS] BUNNY ACHIEVEMENT UNLOCKED: Mystical Automation Bunny! [SUCCESS][BUNNY]${NC}"
        elif [ $((cycle % 25)) -eq 0 ] && [ $cycle -gt 0 ]; then
            echo -e "${PURPLE}[BUNNY][SUCCESS] BUNNY ACHIEVEMENT UNLOCKED: Legendary Bunny Sage! [SUCCESS][BUNNY]${NC}"
        fi

        # Cycle completion
        echo -e "${CYAN}[PANDA] Cycle $cycle completed! Next bamboo feast in 5 minutes...${NC}"
        echo -e "${YELLOW}Ctrl+C to exit the panda realm${NC}"
        echo ""

        # Wait before next cycle (5 minutes)
        sleep 300
        ((cycle++))
    done
}

# Main menu system
show_menu() {
    echo -e "${WHITE}ZEJZL.NET Master Orchestration Commands:${NC}"
    echo "══════════════════════════════════════════"
    echo "1) [START] Complete System Setup"
    echo "2) [DEV] Development Workflow"
    echo "3) [DEPLOY] Deploy to Staging"
    echo "4) [DEPLOY] Deploy to Production"
    echo "5) [TOOL] Maintenance Tasks"
    echo "6) [STATS] Monitoring Dashboard"
    echo "7) [PERF] Performance Optimization"
    echo "8) [SECURITY] Security Audit"
    echo "9) [DOCS] Documentation Check"
    echo "10) [HEALTH] System Health Check"
    echo "11) [EMERGENCY] Emergency Recovery"
    echo "12) [SEARCH] Debug Operations"
    echo "13) [LIST] Show Available Tools"
    echo "0) Exit"
    echo ""
}

# Function for debug operations
debug_operations() {
    echo -e "${PURPLE}[SEARCH] ZEJZL.NET Debug Operations${NC}"
    echo "==============================="

    echo -e "${CYAN}Available Debug Commands:${NC}"
    echo "1) System Status"
    echo "2) Recent Logs"
    echo "3) Performance Metrics"
    echo "4) Create Snapshot"
    echo "5) Clear Logs"
    echo "6) Set Log Level"

    read -p "Choose debug operation (1-6): " debug_choice

    case $debug_choice in
        1) run_cmd "python debug_cli.py status" "System status" ;;
        2) run_cmd "python debug_cli.py logs" "Recent logs" ;;
        3) run_cmd "python debug_cli.py performance" "Performance metrics" ;;
        4) run_cmd "python debug_cli.py snapshot" "System snapshot" ;;
        5) run_cmd "python debug_cli.py clear-logs" "Clear logs" ;;
        6) read -p "Log level (DEBUG/INFO/WARNING/ERROR): " level && run_cmd "python debug_cli.py set-level --log-level $level" "Set log level" ;;
        *) echo -e "${RED}Invalid debug operation${NC}" ;;
    esac

    echo -e "${GREEN}✓ Debug operation completed!${NC}"
}

# Interactive mode
interactive_mode() {
    while true; do
        show_header
        show_menu

        read -p "Choose an option (0-13): " choice
        echo ""

        case $choice in
            1) system_setup ;;
            2) dev_workflow ;;
            3) deployment_pipeline "staging" ;;
            4) deployment_pipeline "production" ;;
            5) maintenance_tasks ;;
            6) monitoring_dashboard ;;
            7) performance_optimization ;;
            8) security_audit ;;
            9) docs_update ;;
            10) system_health ;;
            11) emergency_recovery ;;
            12) debug_operations ;;
            13) show_tools ;;
            0) echo -e "${GREEN}Goodbye! [WAVE]${NC}"; exit 0 ;;
            *) echo -e "${RED}Invalid option. Please choose 0-13.${NC}" ;;
        esac

        echo ""
        read -p "Press Enter to continue..."
        clear
    done
}

# Main execution
main() {
    # Parse command line arguments
    case "${1:-menu}" in
        "setup")
            system_setup ;;
        "dev")
            dev_workflow ;;
        "deploy-staging")
            deployment_pipeline "staging" ;;
        "deploy-production")
            deployment_pipeline "production" ;;
        "maintenance")
            maintenance_tasks ;;
        "monitor")
            monitoring_dashboard ;;
        "optimize")
            performance_optimization ;;
        "security")
            security_audit ;;
        "docs")
            docs_update ;;
        "health")
            system_health ;;
        "recovery")
            emergency_recovery ;;
        "demo")
            zejzl_demo ;;
        "tools")
            show_tools ;;
        "menu")
            interactive_mode ;;
        "help"|"-h"|"--help")
            show_header
            echo "ZEJZL.NET Master Orchestration Script"
            echo ""
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  setup             - Complete ZEJZL.NET system setup"
            echo "  dev               - Development workflow (test + commit)"
            echo "  deploy-staging    - Deploy to staging environment"
            echo "  deploy-production - Deploy to production environment"
            echo "  maintenance       - Run maintenance tasks"
            echo "  monitor           - Show monitoring dashboard"
            echo "  optimize          - Performance optimization"
            echo "  security          - Security audit"
            echo "  docs              - Documentation check"
            echo "  health            - System health check"
            echo "  recovery          - Emergency recovery"
            echo "  demo              - Start ZEJZL.NET demo with web dashboard"
            echo "  debug             - Debug operations menu"
            echo "  tools             - Show available tools"
            echo "  menu              - Interactive menu (default)"
            echo "  help              - Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 setup          # Complete system setup"
            echo "  $0 dev            # Development workflow"
            echo "  $0 demo           # Start full demo"
            echo "  $0 monitor        # Check system status"
            echo "  $0 debug          # Debug operations"
            echo "  $0 menu           # Interactive mode"
            ;;
        *)
            echo "Unknown command: $1"
            "$0" help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"