# External Access Guide for Unraid MCP Server

This guide covers various methods to make your MCP server accessible from outside your network.

## 🔒 **Security Warning**

⚠️ **IMPORTANT**: Before exposing your MCP server externally, ensure you have:
- Strong authentication enabled
- HTTPS/TLS encryption
- Proper firewall rules
- Regular security updates

## 🌐 **Method 1: Reverse Proxy with Nginx (Recommended)**

### **Step 1: Install Nginx Proxy Manager in Unraid**
1. Go to **Apps** → **Community Applications**
2. Search for "Nginx Proxy Manager"
3. Install and configure with your domain

### **Step 2: Configure Domain**
1. Point your domain to your public IP address
2. Set up DNS A record: `mcp.yourdomain.com` → `your_public_ip`

### **Step 3: Add Proxy Host**
In Nginx Proxy Manager:
- **Domain**: `mcp.yourdomain.com`
- **Scheme**: `http`
- **Forward Hostname/IP**: `192.168.1.x` (your Unraid IP)
- **Forward Port**: `8080`
- **Enable SSL**: Yes (Let's Encrypt)
- **Force SSL**: Yes
- **HTTP/2 Support**: Yes

### **Step 4: Configure MCP Server for HTTPS**
Update your `.env` file:
```env
ENABLE_AUTH=true
API_KEY=your_secure_api_key_here
LOG_LEVEL=INFO
```

## 🔧 **Method 2: Cloudflare Tunnel (Most Secure)**

### **Step 1: Install Cloudflare Tunnel**
1. Go to **Apps** → **Community Applications**
2. Search for "Cloudflare Tunnel"
3. Install and configure

### **Step 2: Configure Tunnel**
```yaml
# docker-compose.yml for Cloudflare Tunnel
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
    environment:
      - ENABLE_AUTH=true
      - API_KEY=your_secure_api_key_here
    networks:
      - cloudflare_net

networks:
  cloudflare_net:
    driver: bridge
```

### **Step 3: Set up Cloudflare Dashboard**
1. Go to [Cloudflare Zero Trust](https://dash.cloudflare.com/)
2. Create a tunnel
3. Add your domain: `mcp.yourdomain.com`
4. Point to `http://unraid-mcp-server:8080`

## 🌍 **Method 3: Port Forwarding (Basic)**

### **Step 1: Configure Router**
1. Access your router admin panel
2. Go to **Port Forwarding** or **Virtual Server**
3. Add rule:
   - **External Port**: `8080` (or custom port)
   - **Internal IP**: Your Unraid server IP
   - **Internal Port**: `8080`
   - **Protocol**: TCP

### **Step 2: Get Public IP**
```bash
# Check your public IP
curl ifconfig.me
```

### **Step 3: Access via Public IP**
```
http://your_public_ip:8080
```

⚠️ **Warning**: This method exposes your server directly to the internet without encryption.

## 🚀 **Method 4: VPN Access (Most Secure)**

### **Option A: WireGuard VPN**
1. Install WireGuard in Unraid
2. Configure client devices
3. Access MCP server via local IP when connected to VPN

### **Option B: OpenVPN**
1. Install OpenVPN in Unraid
2. Generate certificates
3. Configure client connections

## 🔐 **Method 5: SSH Tunnel (Development/Testing)**

### **Local SSH Tunnel**
```bash
# Create SSH tunnel to your Unraid server
ssh -L 8080:localhost:8080 user@your_unraid_ip

# Then access locally
http://localhost:8080
```

### **Remote SSH Tunnel**
```bash
# From remote machine
ssh -R 8080:localhost:8080 user@your_unraid_ip
```

## 🛡️ **Security Configuration**

### **Enable Authentication**
Update your `.env` file:
```env
ENABLE_AUTH=true
API_KEY=your_very_secure_api_key_here
LOG_LEVEL=INFO
```

### **Generate Secure API Key**
```bash
# Generate a secure random API key
openssl rand -base64 32
```

### **Configure Firewall Rules**
```bash
# Allow only specific IPs (if using port forwarding)
iptables -A INPUT -p tcp --dport 8080 -s trusted_ip -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP
```

## 📱 **Method 6: Mobile App Access**

### **Using PWA (Progressive Web App)**
1. Access your MCP server via HTTPS
2. Add to home screen on mobile devices
3. Works like a native app

### **Mobile Browser Access**
- Works with any of the above methods
- Responsive design for mobile devices

## 🔄 **Method 7: Dynamic DNS (For Changing IPs)**

### **Step 1: Set up Dynamic DNS**
1. Choose a provider (No-IP, DuckDNS, etc.)
2. Configure your router with DDNS settings
3. Update DNS records automatically

### **Step 2: Configure MCP Server**
```env
# Use your dynamic DNS hostname
UNRAID_HOST=mcp.yourdomain.com
```

## 📊 **Method Comparison**

| Method | Security | Ease | Cost | Recommended For |
|--------|----------|------|------|-----------------|
| Cloudflare Tunnel | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Free | Production |
| Reverse Proxy | ⭐⭐⭐⭐ | ⭐⭐⭐ | Domain cost | Production |
| VPN | ⭐⭐⭐⭐⭐ | ⭐⭐ | Free | Personal use |
| Port Forwarding | ⭐⭐ | ⭐⭐⭐⭐⭐ | Free | Testing |
| SSH Tunnel | ⭐⭐⭐⭐ | ⭐⭐ | Free | Development |

## 🚨 **Troubleshooting**

### **Common Issues**

1. **"Connection refused"**
   - Check if MCP server is running
   - Verify port configuration
   - Check firewall settings

2. **"SSL/TLS errors"**
   - Ensure SSL certificates are valid
   - Check domain configuration
   - Verify proxy settings

3. **"Authentication failed"**
   - Verify API key is correct
   - Check authentication headers
   - Ensure HTTPS is enabled

### **Testing External Access**
```bash
# Test from external network
curl -H "Authorization: Bearer your_api_key" \
  https://mcp.yourdomain.com/health

# Test with authentication
curl -H "X-API-Key: your_api_key" \
  https://mcp.yourdomain.com/api/status
```

## 📋 **Quick Setup Checklist**

### **For Production Use:**
- [ ] Enable authentication in `.env`
- [ ] Generate secure API key
- [ ] Set up HTTPS (SSL/TLS)
- [ ] Configure reverse proxy or Cloudflare Tunnel
- [ ] Set up monitoring and logging
- [ ] Test external access
- [ ] Configure backup and recovery

### **For Development/Testing:**
- [ ] Use SSH tunnel or VPN
- [ ] Enable basic authentication
- [ ] Test local access first
- [ ] Monitor logs for issues

## 🔧 **Advanced Configuration**

### **Load Balancing**
```yaml
# Multiple MCP server instances
version: '3.8'
services:
  mcp-server-1:
    image: kappy1928/tower_mcpv2:latest
    environment:
      - API_KEY=key1
    ports:
      - "8081:8080"

  mcp-server-2:
    image: kappy1928/tower_mcpv2:latest
    environment:
      - API_KEY=key2
    ports:
      - "8082:8080"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### **Monitoring and Alerts**
```yaml
# Add monitoring
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

## 📞 **Support**

If you encounter issues:
1. Check the logs: `docker logs unraid-mcp-server`
2. Verify network connectivity
3. Test with curl commands
4. Review security configuration
5. Check Unraid community forums 