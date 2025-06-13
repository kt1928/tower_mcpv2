# MCP Server Setup Guide

This guide explains how to set up and use the Unraid MCP Server with Claude Desktop and other MCP clients.

## 🔧 **What is MCP?**

The **Model Context Protocol (MCP)** is a standard protocol that allows AI assistants like Claude to interact with external tools and data sources. Our Unraid MCP Server provides AI-powered tools for comprehensive system management.

## 🚀 **Server Modes**

The server can run in three modes:

### **1. MCP-Only Mode (Recommended for Claude Desktop)**
- Runs only the MCP protocol via stdio
- Best for direct integration with Claude Desktop
- No HTTP interface

### **2. HTTP-Only Mode (Legacy)**
- Runs only the HTTP API interface
- Good for web-based access and health checks
- Not compatible with MCP clients

### **3. Dual Mode (Default)**
- Runs both MCP protocol and HTTP interface
- Best of both worlds
- HTTP interface on port 9090 for health checks

## 📋 **Installation**

### **Method 1: Docker (Recommended)**

```bash
# Pull the latest image
docker pull kappy1928/tower_mcpv2:latest

# Run in dual mode (MCP + HTTP)
docker run -d \
  --name unraid-mcp-server \
  --restart=unless-stopped \
  -p 9090:9090 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/log:/host/var/log:ro \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /mnt/user/appdata/unraid-mcp-server:/app/data \
  kappy1928/tower_mcpv2:latest
```

### **Method 2: Docker Compose**

```yaml
version: '3.8'
services:
  unraid-mcp-server:
    image: kappy1928/tower_mcpv2:latest
    container_name: unraid-mcp-server
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/log:/host/var/log:ro
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - ./data:/app/data
    environment:
      - LOG_LEVEL=INFO
      - ENABLE_AUTH=false
```

### **Method 3: Source Code**

```bash
# Clone the repository
git clone https://github.com/kt1928/tower_mcpv2.git
cd tower_mcpv2

# Install dependencies
pip install -r requirements

# Run in dual mode
python src/dual_server.py

# Or run MCP-only mode
python src/main.py
```

## 🎯 **Claude Desktop Configuration**

### **Step 1: Install Claude Desktop**
1. Download Claude Desktop from [Anthropic](https://claude.ai/download)
2. Install and launch Claude Desktop

### **Step 2: Configure MCP Server**
1. Open Claude Desktop
2. Go to **Settings** → **MCP Servers**
3. Click **Add Server**
4. Configure the server:

```json
{
  "name": "Unraid MCP Server",
  "command": "docker",
  "args": [
    "exec",
    "-i",
    "unraid-mcp-server",
    "python",
    "/app/src/main.py"
  ],
  "env": {}
}
```

### **Step 3: Alternative Configuration (Direct)**
If you want to run the server directly:

```json
{
  "name": "Unraid MCP Server",
  "command": "python",
  "args": [
    "/path/to/tower_mcpv2/src/main.py"
  ],
  "env": {
    "LOG_LEVEL": "INFO"
  }
}
```

### **Step 4: Test Connection**
1. Save the configuration
2. Restart Claude Desktop
3. Start a new conversation
4. Try: "What tools do you have available for managing my Unraid server?"

## 🛠 **Available Tools**

Once connected, Claude will have access to these tools:

### **System Diagnostics**
- `system_diagnostics.get_system_overview` - Comprehensive system status
- `system_diagnostics.get_disk_health` - SMART disk health analysis
- `system_diagnostics.get_temperature_status` - Temperature monitoring
- `system_diagnostics.get_network_status` - Network interface status
- `system_diagnostics.check_system_health` - Overall health assessment

### **Docker Management**
- `docker_management.list_containers` - List all containers
- `docker_management.manage_container` - Start, stop, restart containers
- `docker_management.get_container_stats` - Resource usage statistics
- `docker_management.get_container_logs` - Container log analysis
- `docker_management.cleanup_docker` - Remove unused resources

### **Plex Integration**
- `plex_integration.get_plex_status` - Plex server status
- `plex_integration.analyze_plex_library` - Library statistics
- `plex_integration.get_plex_sessions` - Active streaming sessions
- `plex_integration.optimize_plex_database` - Database maintenance

### **Log Analysis**
- `log_analysis.analyze_system_logs` - Parse and analyze logs
- `log_analysis.search_logs` - Search for specific patterns
- `log_analysis.get_error_summary` - Summary of recent errors

### **Maintenance**
- `maintenance.run_cleanup` - System cleanup and optimization
- `maintenance.check_updates` - Available system updates
- `maintenance.verify_backups` - Backup integrity verification

## 💬 **Example Conversations**

### **System Health Check**
```
User: "Check the health of my Unraid server"
Claude: [Uses system_diagnostics.check_system_health]
```

### **Docker Container Management**
```
User: "Show me all running Docker containers and their resource usage"
Claude: [Uses docker_management.list_containers and get_container_stats]
```

### **Plex Library Analysis**
```
User: "Analyze my Plex library and suggest optimizations"
Claude: [Uses plex_integration.analyze_plex_library]
```

### **Log Analysis**
```
User: "Check for any errors in the system logs from the last hour"
Claude: [Uses log_analysis.analyze_system_logs]
```

## 🔧 **Configuration Options**

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MCP_PORT` | `9090` | HTTP interface port |
| `ENABLE_AUTH` | `false` | Enable API authentication |
| `PLEX_URL` | - | Plex server URL |
| `PLEX_TOKEN` | - | Plex authentication token |

### **Configuration File**
Create `.env` file for persistent configuration:

```env
# Basic Settings
LOG_LEVEL=INFO
TZ=America/New_York
UNRAID_HOST=unraid.local

# MCP Server
MCP_PORT=9090
ENABLE_AUTH=false

# Plex Integration
PLEX_URL=http://plex:32400
PLEX_TOKEN=your_plex_token_here
```

## 🧪 **Testing and Troubleshooting**

### **Test HTTP Interface**
```bash
# Test health endpoint
curl http://localhost:9090/health

# Test MCP info
curl http://localhost:9090/mcp-info

# List available tools
curl http://localhost:9090/tools
```

### **Test MCP Connection**
```bash
# Test direct MCP connection
echo '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}' | \
  docker exec -i unraid-mcp-server python /app/src/main.py
```

### **Common Issues**

1. **"Connection refused"**
   - Check if container is running: `docker ps`
   - Check logs: `docker logs unraid-mcp-server`

2. **"Tool not found"**
   - Verify tool is enabled in configuration
   - Check tool initialization in logs

3. **"Permission denied"**
   - Ensure Docker socket is accessible
   - Check file permissions for mounted volumes

4. **Claude Desktop not connecting**
   - Verify MCP server configuration
   - Check if server is running in MCP mode
   - Restart Claude Desktop after configuration changes

## 🔒 **Security Considerations**

### **Authentication**
- Enable authentication for production use
- Use strong API keys
- Restrict access to trusted networks

### **Network Security**
- Use HTTPS for external access
- Configure firewall rules
- Consider VPN access for remote management

### **Docker Security**
- Run container as non-root user
- Use read-only mounts where possible
- Regularly update container images

## 📊 **Monitoring and Logs**

### **Container Logs**
```bash
# View real-time logs
docker logs -f unraid-mcp-server

# View recent logs
docker logs --tail 100 unraid-mcp-server
```

### **Application Logs**
```bash
# View application logs
docker exec unraid-mcp-server cat /app/logs/app.log
```

### **Health Monitoring**
```bash
# Check health status
curl http://localhost:9090/health

# Get detailed status
curl http://localhost:9090/status
```

## 🔄 **Updates and Maintenance**

### **Update Container**
```bash
# Pull latest image
docker pull kappy1928/tower_mcpv2:latest

# Stop and remove old container
docker stop unraid-mcp-server
docker rm unraid-mcp-server

# Start new container
docker run -d --name unraid-mcp-server [your-options] kappy1928/tower_mcpv2:latest
```

### **Backup Configuration**
```bash
# Backup configuration
docker cp unraid-mcp-server:/app/config ./backup-config

# Restore configuration
docker cp ./backup-config unraid-mcp-server:/app/config
```

## 📞 **Support**

If you encounter issues:

1. **Check the logs**: `docker logs unraid-mcp-server`
2. **Verify configuration**: Check environment variables and .env file
3. **Test connectivity**: Use curl commands to test HTTP endpoints
4. **Check permissions**: Ensure Docker socket and volume permissions are correct
5. **Review documentation**: Check README.md and other guides
6. **Community support**: Visit Unraid community forums

## 🎉 **Getting Started**

1. **Install the server** using one of the methods above
2. **Configure Claude Desktop** with the MCP server
3. **Test the connection** by asking Claude about your server
4. **Explore the tools** available for system management
5. **Set up monitoring** and alerts for your system

The MCP server provides a powerful interface for AI-assisted Unraid system management. Enjoy the enhanced capabilities! 