#!/bin/bash
# Script to run Ruff for formatting and linting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default action
ACTION="${1:-all}"

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if ruff is available
if ! command -v ruff &> /dev/null; then
    # Try using uv to run ruff
    if command -v uv &> /dev/null; then
        print_info "Ruff not found in PATH, using uv to run ruff..."
        RUFF_CMD="uv run ruff"
    else
        print_error "Ruff not found and uv is not available."
        print_error "Please install ruff: uv add --dev ruff"
        exit 1
    fi
else
    RUFF_CMD="ruff"
fi

# Run based on action
case "$ACTION" in
    format)
        print_info "Formatting Python files..."
        $RUFF_CMD format .
        print_info "Formatting complete!"
        ;;
    check-format)
        print_info "Checking Python file formatting..."
        if $RUFF_CMD format --check .; then
            print_info "All files are properly formatted!"
        else
            print_error "Some files need formatting. Run './scripts/ruff.sh format' to fix."
            exit 1
        fi
        ;;
    lint)
        print_info "Linting Python files..."
        $RUFF_CMD check .
        print_info "Linting complete!"
        ;;
    lint-fix)
        print_info "Linting and auto-fixing Python files..."
        $RUFF_CMD check --fix .
        print_info "Linting and fixing complete!"
        ;;
    check)
        print_info "Checking Python files (linting only, no fixes)..."
        if $RUFF_CMD check .; then
            print_info "No linting issues found!"
        else
            print_error "Linting issues found. Run './scripts/ruff.sh lint-fix' to auto-fix."
            exit 1
        fi
        ;;
    all)
        print_info "Running all checks (format check + lint check)..."
        echo ""
        print_info "Step 1/2: Checking formatting..."
        if $RUFF_CMD format --check .; then
            print_info "✓ Formatting is correct"
        else
            print_warn "✗ Formatting issues found"
            FORMAT_ISSUES=1
        fi
        echo ""
        print_info "Step 2/2: Checking linting..."
        if $RUFF_CMD check .; then
            print_info "✓ No linting issues"
        else
            print_warn "✗ Linting issues found"
            LINT_ISSUES=1
        fi
        echo ""
        if [ -z "$FORMAT_ISSUES" ] && [ -z "$LINT_ISSUES" ]; then
            print_info "All checks passed! ✓"
            exit 0
        else
            print_error "Some checks failed."
            print_info "Run './scripts/ruff.sh fix' to auto-fix issues."
            exit 1
        fi
        ;;
    fix)
        print_info "Auto-fixing all issues (format + lint)..."
        echo ""
        print_info "Step 1/2: Formatting files..."
        $RUFF_CMD format .
        print_info "✓ Formatting complete"
        echo ""
        print_info "Step 2/2: Fixing linting issues..."
        $RUFF_CMD check --fix .
        print_info "✓ Linting fixes complete"
        echo ""
        print_info "All fixes applied!"
        ;;
    *)
        echo "Usage: $0 [action]"
        echo ""
        echo "Actions:"
        echo "  format       - Format all Python files"
        echo "  check-format - Check formatting without making changes"
        echo "  lint         - Lint all Python files (show issues only)"
        echo "  lint-fix     - Lint and auto-fix all Python files"
        echo "  check        - Check linting without making changes"
        echo "  all          - Run format check + lint check (default)"
        echo "  fix          - Format + auto-fix linting issues"
        echo ""
        echo "Examples:"
        echo "  $0              # Run all checks"
        echo "  $0 format       # Format all files"
        echo "  $0 fix          # Format and fix linting issues"
        exit 1
        ;;
esac




