# Port Change: 8080 → 9090

## 🔄 **Change Summary**

The MCP server has been updated to use **port 9090** instead of port 8080 to avoid conflicts with other services.

## 📋 **Updated Files**

### **Configuration Files**
- `docker-compose.yml` - Port mapping updated to 9090:9090
- `env.example` - MCP_PORT changed to 9090
- `unraid-template.xml` - WebUI and port configurations updated

### **Documentation**
- `README.md` - All port references updated to 9090
- `scripts/setup_external_access.sh` - All port checks and configurations updated

## 🚀 **Quick Migration**

### **For Existing Users**

1. **Stop the current container:**
   ```bash
   docker-compose down
   ```

2. **Update your .env file:**
   ```env
   MCP_PORT=9090
   ```

3. **Restart with new configuration:**
   ```bash
   docker-compose up -d
   ```

4. **Test the new port:**
   ```bash
   curl http://localhost:9090/health
   ```

### **For New Installations**

The new port 9090 is now the default. No additional configuration needed.

## 🔧 **External Access Updates**

If you have external access configured, update your configurations:

### **Nginx Proxy Manager**
- Update proxy host to forward to port 9090
- Update SSL certificate if needed

### **Cloudflare Tunnel**
- Update tunnel configuration to point to port 9090
- No changes needed to external domain

### **Port Forwarding**
- Update router port forwarding rule:
  - External Port: 9090
  - Internal Port: 9090

### **SSH Tunnels**
- Update tunnel commands:
  ```bash
  # Local tunnel
  ssh -L 9090:localhost:9090 user@your_unraid_ip
  
  # Remote tunnel
  ssh -R 9090:localhost:9090 user@your_unraid_ip
  ```

## 📊 **Why Port 9090?**

- **Less common**: Port 9090 is less likely to conflict with other services
- **Monitoring standard**: Commonly used for monitoring tools (Prometheus, etc.)
- **Security**: Reduces risk of accidental exposure to common ports
- **Future-proof**: Avoids conflicts with popular development tools

## ✅ **Verification**

After the change, verify everything works:

1. **Local access:**
   ```bash
   curl http://localhost:9090/health
   ```

2. **External access:**
   ```bash
   curl http://your-domain.com/health
   ```

3. **Check logs:**
   ```bash
   docker logs unraid-mcp-server
   ```

## 🆘 **Troubleshooting**

If you encounter issues:

1. **Port still in use:**
   ```bash
   # Check what's using port 9090
   netstat -tulpn | grep 9090
   ```

2. **Container won't start:**
   ```bash
   # Check container logs
   docker logs unraid-mcp-server
   ```

3. **External access broken:**
   - Verify port forwarding/router configuration
   - Check proxy/reverse proxy settings
   - Test with different port if needed

## 📞 **Support**

If you need help with the migration:
1. Check the logs: `docker logs unraid-mcp-server`
2. Verify network connectivity
3. Review external access configuration
4. Check Unraid community forums 