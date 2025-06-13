# Plex Integration Setup Guide

This guide explains how to configure Plex integration with your Unraid MCP Server.

## 🔑 Getting Your Plex Token

### Method 1: Using Plex Web Interface
1. Go to [Plex Web](https://app.plex.tv/web/app)
2. Sign in to your Plex account
3. Go to **Settings** → **Account**
4. Look for **X-Plex-Token** in the URL or use browser developer tools
5. Copy the token value

### Method 2: Using Plex Media Server
1. Open your Plex Media Server web interface
2. Go to **Settings** → **Account**
3. Find your **X-Plex-Token** in the account information

### Method 3: Using Plex API (Advanced)
```bash
# Get token from Plex login
curl -X POST "https://plex.tv/users/sign_in.json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user[login]=your_username&user[password]=your_password"
```

## 🐳 Docker Configuration Methods

### Method 1: Environment File (Recommended)

1. **Copy the template:**
   ```bash
   cp env.template .env
   ```

2. **Edit the .env file:**
   ```bash
   nano .env
   ```

3. **Add your Plex configuration:**
   ```env
   PLEX_URL=http://your-plex-server:32400
   PLEX_TOKEN=your_plex_token_here
   ```

4. **Start the container:**
   ```bash
   docker-compose up -d
   ```

### Method 2: Direct Environment Variables

```bash
docker run -d \
  --name unraid-mcp-server \
  -p 8080:8080 \
  -e PLEX_URL=http://your-plex-server:32400 \
  -e PLEX_TOKEN=your_plex_token_here \
  -v /var/run/docker.sock:/var/run/docker.sock \
  kappy1928/tower_mcpv2:latest
```

### Method 3: Docker Compose with Inline Variables

```yaml
version: '3.8'
services:
  unraid-mcp-server:
    image: kappy1928/tower_mcpv2:latest
    environment:
      - PLEX_URL=http://your-plex-server:32400
      - PLEX_TOKEN=your_plex_token_here
    ports:
      - "8080:8080"
```

## 🔧 Plex URL Configuration

### Local Plex Server
```env
PLEX_URL=http://192.168.1.100:32400
```

### Plex Server on Same Network
```env
PLEX_URL=http://plex-server.local:32400
```

### Remote Plex Server (with port forwarding)
```env
PLEX_URL=http://your-domain.com:32400
```

### Plex Server with Custom Port
```env
PLEX_URL=http://your-plex-server:32401
```

## 🔒 Security Best Practices

### 1. Use Environment Files
- Never commit `.env` files to version control
- Add `.env` to your `.gitignore` file
- Use different tokens for different environments

### 2. Token Security
- Keep your Plex token secure and private
- Rotate tokens periodically
- Use the minimum required permissions

### 3. Network Security
- Use HTTPS for remote connections
- Configure firewall rules appropriately
- Consider using VPN for remote access

## 🧪 Testing Plex Connection

### 1. Check Container Logs
```bash
docker logs unraid-mcp-server
```

### 2. Test Plex API Directly
```bash
curl -H "X-Plex-Token: your_token" \
  "http://your-plex-server:32400/library/sections"
```

### 3. Use the Health Check Endpoint
```bash
curl http://localhost:8080/health
```

## 🚨 Troubleshooting

### Common Issues

1. **"Plex token not found"**
   - Verify the token is correct
   - Check that the environment variable is set
   - Restart the container after changing environment

2. **"Cannot connect to Plex server"**
   - Verify the PLEX_URL is correct
   - Check network connectivity
   - Ensure Plex server is running

3. **"Permission denied"**
   - Verify the token has appropriate permissions
   - Check Plex server settings

### Debug Mode
Enable debug logging by setting:
```env
LOG_LEVEL=DEBUG
```

## 📋 Example Configuration

### Complete .env Example
```env
# Plex Integration
PLEX_URL=http://192.168.1.100:32400
PLEX_TOKEN=your_plex_token_here

# Security
API_KEY=your_api_key_here
ENABLE_AUTH=true

# Basic Settings
LOG_LEVEL=INFO
TZ=America/New_York
UNRAID_HOST=unraid.local

# Performance
MAX_WORKERS=4
CACHE_TTL=300
```

### Docker Run Example
```bash
docker run -d \
  --name unraid-mcp-server \
  --restart unless-stopped \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/log:/host/var/log:ro \
  -e PLEX_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your_plex_token_here \
  -e LOG_LEVEL=INFO \
  kappy1928/tower_mcpv2:latest
```

## 🔄 Updating Configuration

To update your Plex configuration:

1. **Stop the container:**
   ```bash
   docker-compose down
   ```

2. **Update the .env file**

3. **Restart the container:**
   ```bash
   docker-compose up -d
   ```

4. **Verify the changes:**
   ```bash
   docker logs unraid-mcp-server
   ``` 