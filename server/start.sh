#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to get local IP address
get_local_ip() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        ipconfig getifaddr en0 || ipconfig getifaddr en1
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        hostname -I | awk '{print $1}'
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows (Git Bash)
        ipconfig | grep "IPv4" | grep -v "127.0.0.1" | head -n 1 | awk '{print $NF}'
    else
        echo "127.0.0.1"
    fi
}

# Function to check if port is available
check_port() {
    if [[ "$OSTYPE" == "darwin"* || "$OSTYPE" == "linux-gnu"* ]]; then
        lsof -i :$1 > /dev/null 2>&1
    else
        netstat -an | grep ":$1" | grep "LISTEN" > /dev/null 2>&1
    fi
    return $?
}

# Function to activate conda environment
activate_conda() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source "$(dirname $(which conda))/../etc/profile.d/conda.sh"
    else
        # macOS/Linux
        source "$(conda info --base)/etc/profile.d/conda.sh"
    fi
}

# Default port
PORT=5000

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./start.sh [options]"
            echo "Options:"
            echo "  -p, --port PORT    Specify port number (default: 5000)"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if port is available
if check_port $PORT; then
    echo -e "${YELLOW}Port $PORT is already in use. Please choose a different port.${NC}"
    exit 1
fi

# Get local IP
LOCAL_IP=$(get_local_ip)

# Set environment variables
export FLASK_APP="src/app.py"
export FLASK_ENV="development"

# Print server information
echo -e "${GREEN}Starting Flask server...${NC}"
echo -e "Local URL: ${YELLOW}http://localhost:$PORT${NC}"
echo -e "Network URL: ${YELLOW}http://$LOCAL_IP:$PORT${NC}"
echo -e "Press Ctrl+C to stop the server${NC}"

# Start the server
if command -v conda &> /dev/null; then
    # Activate conda environment
    activate_conda
    conda activate ai-hedge-fund  # Replace with your conda environment name
    python src/app.py
else
    echo -e "${YELLOW}Conda not found. Using system Python...${NC}"
    python src/app.py
fi 