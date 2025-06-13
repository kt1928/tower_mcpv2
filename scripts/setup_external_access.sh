#!/bin/bash

# External Access Setup Script for Unraid MCP Server
# This script helps configure external access with security best practices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to generate secure API key
generate_api_key() {
    if command_exists openssl; then
        openssl rand -base64 32
    else
        # Fallback to /dev/urandom
        head -c 32 /dev/urandom | base64
    fi
}

# Function to get public IP
get_public_ip() {
    if command_exists curl; then
        curl -s ifconfig.me
    elif command_exists wget; then
        wget -qO- ifconfig.me
    else
        echo "Unable to determine public IP"
        return 1
    fi
}

# Function to check if port is open
check_port() {
    local host=$1
    local port=$2
    
    if command_exists nc; then
        nc -z "$host" "$port" 2>/dev/null
    else
        # Fallback using /dev/tcp
        timeout 5 bash -c "</dev/tcp/$host/$port" 2>/dev/null
    fi
}

# Main setup function
main() {
    echo "=========================================="
    echo "  Unraid MCP Server External Access Setup"
    echo "=========================================="
    echo
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. Consider running as regular user."
    fi
    
    # Check if .env file exists
    if [[ ! -f .env ]]; then
        print_status "Creating .env file from template..."
        if [[ -f env.template ]]; then
            cp env.template .env
            print_success "Created .env file"
        else
            print_error "env.template not found. Please create .env file manually."
            exit 1
        fi
    fi
    
    # Security configuration
    echo
    print_status "Configuring security settings..."
    
    # Generate API key if not set
    if ! grep -q "API_KEY=" .env || grep -q "API_KEY=$" .env; then
        print_status "Generating secure API key..."
        API_KEY=$(generate_api_key)
        sed -i.bak "s/API_KEY=.*/API_KEY=$API_KEY/" .env
        print_success "Generated API key: $API_KEY"
    else
        print_status "API key already configured"
    fi
    
    # Enable authentication
    sed -i.bak "s/ENABLE_AUTH=.*/ENABLE_AUTH=true/" .env
    print_success "Authentication enabled"
    
    # Set log level
    sed -i.bak "s/LOG_LEVEL=.*/LOG_LEVEL=INFO/" .env
    print_success "Log level set to INFO"
    
    # Get network information
    echo
    print_status "Network Information:"
    
    # Get local IP
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    echo "Local IP: $LOCAL_IP"
    
    # Get public IP
    print_status "Getting public IP..."
    PUBLIC_IP=$(get_public_ip)
    if [[ $? -eq 0 ]]; then
        echo "Public IP: $PUBLIC_IP"
    else
        print_warning "Could not determine public IP"
    fi
    
    # Check if port 8080 is accessible
    print_status "Checking port 8080 accessibility..."
    if check_port localhost 8080; then
        print_success "Port 8080 is accessible locally"
    else
        print_warning "Port 8080 is not accessible locally"
    fi
    
    # Security recommendations
    echo
    print_status "Security Recommendations:"
    echo "1. Use HTTPS/TLS encryption"
    echo "2. Set up a reverse proxy (Nginx Proxy Manager)"
    echo "3. Consider using Cloudflare Tunnel"
    echo "4. Configure firewall rules"
    echo "5. Use strong passwords and API keys"
    echo "6. Enable monitoring and logging"
    
    # Method selection
    echo
    print_status "Choose your external access method:"
    echo "1. Reverse Proxy (Nginx Proxy Manager) - Recommended"
    echo "2. Cloudflare Tunnel - Most Secure"
    echo "3. Port Forwarding - Basic (Not recommended for production)"
    echo "4. VPN Access - Most Secure for personal use"
    echo "5. SSH Tunnel - For development/testing"
    echo "6. Skip - Configure manually later"
    
    read -p "Enter your choice (1-6): " choice
    
    case $choice in
        1)
            setup_reverse_proxy
            ;;
        2)
            setup_cloudflare_tunnel
            ;;
        3)
            setup_port_forwarding
            ;;
        4)
            setup_vpn
            ;;
        5)
            setup_ssh_tunnel
            ;;
        6)
            print_status "Skipping automatic setup. Configure manually using EXTERNAL_ACCESS.md"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    # Final steps
    echo
    print_success "Setup complete!"
    echo
    print_status "Next steps:"
    echo "1. Restart your MCP server: docker-compose down && docker-compose up -d"
    echo "2. Test local access: curl http://localhost:8080/health"
    echo "3. Configure external access using the method you chose"
    echo "4. Test external access from outside your network"
    echo "5. Monitor logs: docker logs unraid-mcp-server"
    
    echo
    print_status "Configuration files:"
    echo "- .env: Environment configuration"
    echo "- EXTERNAL_ACCESS.md: Detailed setup guide"
    echo "- PLEX_SETUP.md: Plex integration guide"
}

# Reverse proxy setup
setup_reverse_proxy() {
    print_status "Setting up Reverse Proxy configuration..."
    
    # Create nginx configuration
    cat > nginx-mcp.conf << 'EOF'
server {
    listen 80;
    server_name mcp.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
    
    print_success "Created nginx configuration: nginx-mcp.conf"
    print_status "Next steps:"
    echo "1. Install Nginx Proxy Manager in Unraid"
    echo "2. Point your domain to $PUBLIC_IP"
    echo "3. Add proxy host in Nginx Proxy Manager"
    echo "4. Enable SSL with Let's Encrypt"
}

# Cloudflare Tunnel setup
setup_cloudflare_tunnel() {
    print_status "Setting up Cloudflare Tunnel configuration..."
    
    # Create docker-compose for Cloudflare Tunnel
    cat > docker-compose-cloudflare.yml << 'EOF'
version: '3.8'
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=your_tunnel_token_here
    networks:
      - cloudflare_net

  unraid-mcp-server:
    image: kappy1928/tower_mcpv2:latest
    container_name: unraid-mcp-server
    restart: unless-stopped
    ports:
      - "8080:8080"
    env_file:
      - .env
    networks:
      - cloudflare_net

networks:
  cloudflare_net:
    driver: bridge
EOF
    
    print_success "Created Cloudflare Tunnel configuration: docker-compose-cloudflare.yml"
    print_status "Next steps:"
    echo "1. Go to Cloudflare Zero Trust dashboard"
    echo "2. Create a tunnel and get the token"
    echo "3. Replace 'your_tunnel_token_here' in docker-compose-cloudflare.yml"
    echo "4. Run: docker-compose -f docker-compose-cloudflare.yml up -d"
}

# Port forwarding setup
setup_port_forwarding() {
    print_warning "Port forwarding exposes your server directly to the internet!"
    print_status "Setting up port forwarding configuration..."
    
    echo
    print_status "Router Configuration Required:"
    echo "1. Access your router admin panel"
    echo "2. Go to Port Forwarding or Virtual Server"
    echo "3. Add rule:"
    echo "   - External Port: 8080"
    echo "   - Internal IP: $LOCAL_IP"
    echo "   - Internal Port: 8080"
    echo "   - Protocol: TCP"
    echo
    echo "Access URL: http://$PUBLIC_IP:8080"
    
    print_warning "Remember to enable authentication and use HTTPS in production!"
}

# VPN setup
setup_vpn() {
    print_status "Setting up VPN configuration..."
    
    print_status "VPN Options:"
    echo "1. WireGuard (Recommended)"
    echo "2. OpenVPN"
    
    read -p "Choose VPN type (1-2): " vpn_choice
    
    case $vpn_choice in
        1)
            print_status "WireGuard Setup:"
            echo "1. Install WireGuard in Unraid"
            echo "2. Generate server and client keys"
            echo "3. Configure client devices"
            echo "4. Access MCP server via local IP when connected to VPN"
            ;;
        2)
            print_status "OpenVPN Setup:"
            echo "1. Install OpenVPN in Unraid"
            echo "2. Generate certificates"
            echo "3. Configure client connections"
            echo "4. Access MCP server via local IP when connected to VPN"
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

# SSH tunnel setup
setup_ssh_tunnel() {
    print_status "Setting up SSH tunnel configuration..."
    
    echo
    print_status "SSH Tunnel Commands:"
    echo
    echo "Local tunnel (from your local machine):"
    echo "ssh -L 8080:localhost:8080 user@$LOCAL_IP"
    echo "Then access: http://localhost:8080"
    echo
    echo "Remote tunnel (from remote machine):"
    echo "ssh -R 8080:localhost:8080 user@$LOCAL_IP"
    echo "Then access: http://$LOCAL_IP:8080"
    
    print_status "Note: SSH tunnel is good for development/testing, not production"
}

# Run main function
main "$@" 