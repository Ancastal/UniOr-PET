#!/bin/bash

# UniOr-PET Heroku Deployment Script
# This script automates the Heroku deployment process

set -e  # Exit on error

echo "========================================="
echo "UniOr-PET Heroku Deployment"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo -e "${RED}Error: Heroku CLI is not installed${NC}"
    echo "Please install it from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

echo -e "${GREEN}✓ Heroku CLI is installed${NC}"

# Check if logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Heroku. Opening login...${NC}"
    heroku login
fi

echo -e "${GREEN}✓ Logged in to Heroku${NC}"
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo -e "${YELLOW}Git repository not initialized. Initializing...${NC}"
    git init
    git add .
    git commit -m "Initial commit for Heroku deployment"
    echo -e "${GREEN}✓ Git repository initialized${NC}"
else
    echo -e "${GREEN}✓ Git repository exists${NC}"
fi

echo ""

# Ask for app name
read -p "Enter Heroku app name (or press Enter for random name): " APP_NAME

if [ -z "$APP_NAME" ]; then
    echo -e "${YELLOW}Creating Heroku app with random name...${NC}"
    heroku create
else
    echo -e "${YELLOW}Creating Heroku app: $APP_NAME${NC}"
    heroku create "$APP_NAME"
fi

echo -e "${GREEN}✓ Heroku app created${NC}"
echo ""

# Set environment variables
echo -e "${YELLOW}Setting environment variables...${NC}"

# Check if .env file exists
if [ -f .env ]; then
    echo "Found .env file. Reading configuration..."
    source .env

    # Set Supabase variables
    if [ ! -z "$PROJECT_URL" ]; then
        heroku config:set PROJECT_URL="$PROJECT_URL"
        echo -e "${GREEN}✓ Set PROJECT_URL${NC}"
    fi

    if [ ! -z "$PROJECT_API_KEY" ]; then
        heroku config:set PROJECT_API_KEY="$PROJECT_API_KEY"
        echo -e "${GREEN}✓ Set PROJECT_API_KEY${NC}"
    fi
else
    echo -e "${RED}Warning: .env file not found${NC}"
    echo "Please set environment variables manually:"
    echo "  heroku config:set PROJECT_URL=your-url"
    echo "  heroku config:set PROJECT_API_KEY=your-key"
fi

# Set VERSION
heroku config:set VERSION="1.0.0"
echo -e "${GREEN}✓ Set VERSION${NC}"

echo ""

# Deploy to Heroku
echo -e "${YELLOW}Deploying to Heroku...${NC}"
echo "This may take several minutes..."
echo ""

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Deploy
if git push heroku "$BRANCH":main; then
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}✓ Deployment successful!${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""

    # Open the app
    echo -e "${YELLOW}Opening your app...${NC}"
    heroku open

    echo ""
    echo "Useful commands:"
    echo "  heroku logs --tail          # View logs"
    echo "  heroku restart              # Restart app"
    echo "  heroku ps                   # Check status"
    echo "  heroku config               # View config vars"
    echo ""
else
    echo ""
    echo -e "${RED}=========================================${NC}"
    echo -e "${RED}✗ Deployment failed!${NC}"
    echo -e "${RED}=========================================${NC}"
    echo ""
    echo "Check the error messages above."
    echo "Common issues:"
    echo "  - Slug size too large (remove large dependencies)"
    echo "  - Missing dependencies in requirements.txt"
    echo "  - Syntax errors in code"
    echo ""
    echo "View logs:"
    echo "  heroku logs --tail"
    exit 1
fi
