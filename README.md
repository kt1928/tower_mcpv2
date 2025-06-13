# Unraid MCP Server

An advanced Model Context Protocol (MCP) server designed specifically for Unraid system management. This server provides AI-powered tools for comprehensive system monitoring, Docker management, Plex integration, intelligent log analysis, and automated maintenance.

## 🚀 Features

### System Diagnostics
- **Real-time monitoring**: CPU, memory, disk usage, and temperatures
- **SMART disk health**: Comprehensive drive health analysis with predictive failure detection
- **Network status**: Interface monitoring and performance statistics
- **Process management**: Detailed process information and resource usage
- **Health checks**: Automated system health assessment with recommendations

### Docker Management
- **Container lifecycle**: Start, stop, restart, and update containers
- **Resource monitoring**: Real-time container resource usage and performance metrics
- **Image management**: Cleanup, optimization, and update notifications
- **Compose support**: Multi-container application management
- **Health monitoring**: Container health status and dependency tracking

### Plex Integration
- **Media analysis**: Library statistics and optimization recommendations
- **Performance monitoring**: Transcoding performance and resource usage
- **User activity**: Session tracking and usage analytics
- **Maintenance automation**: Library refresh, metadata updates, and cleanup
- **Storage optimization**: Media file organization and space utilization

### Log Analysis
- **Intelligent parsing**: Real-time log analysis with pattern recognition
- **Error detection**: Automated error classification and severity assessment
- **Alert generation**: Proactive notifications for critical issues
- **Trend analysis**: Historical pattern analysis and prediction
- **Multi-source correlation**: Cross-system log correlation for root cause analysis

### Maintenance & Automation
- **Automated cleanup**: Log rotation, cache cleanup, and orphaned file removal
- **Update management**: System and application update notifications
- **Backup verification**: Automated backup integrity checks
- **Performance optimization**: System tuning recommendations
- **Scheduled tasks**: Customizable maintenance schedules

## 📋 Requirements

- **Unraid 6.10+** (recommended 6.12+)
- **Docker** (included with Unraid)
- **Python 3.8+** (containerized)
- **2GB RAM** minimum (4GB recommended)
- **1GB disk space** for application data

## 🛠 Installation

### Method 1: Unraid Community Applications (Recommended)

1. Open Unraid web interface
2. Go to **Apps** tab
3. Search for "Unraid MCP Server"
4. Click **Install**
5. Configure settings as needed
6. Click **Apply**

### Method 2: Manual Docker Installation

1. **Download the template**:
   ```bash
   wget https://raw.githubusercontent.com/kt1928/tower_mcpv2/main/unraid-template.xml
   ```

2. **Add to Unraid**:
   - Go to Docker tab in Unraid
   - Click "Add Container"
   - Set Template URL and apply

### Method 3: Docker Compose (Development)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kt1928/tower_mcpv2.git
   cd tower_mcpv2
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

3. **Start the server**:
   ```bash
   docker-compose up -d
   ```

### Method 4: Direct Docker Pull

```bash
docker pull kappy1928/tower_mcpv2:latest
docker run -d \
  --name unraid-mcp-server \
  --restart=unless-stopped \
  -p 9090:9090 \
  -v /var/log:/host/var/log:ro \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/unraid-mcp-server:/app/data \
  kappy1928/tower_mcpv2:latest
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `PLEX_URL` | - | Plex server URL (e.g., `http://plex:32400`) |
| `PLEX_TOKEN` | - | Plex authentication token |
| `ENABLE_SYSTEM_DIAGNOSTICS` | `true` | Enable system monitoring tools |
| `ENABLE_DOCKER_MANAGEMENT` | `true` | Enable Docker container management |
| `ENABLE_PLEX_INTEGRATION` | `true` | Enable Plex server integration |
| `ENABLE_LOG_ANALYSIS` | `true` | Enable log parsing and analysis |
| `ENABLE_MAINTENANCE` | `true` | Enable automated maintenance tools |
| `API_KEY` | - | API authentication key (optional) |
| `HEALTH_CHECK_INTERVAL` | `60` | Health check interval in seconds |

### Volume Mappings

The container requires several volume mappings for proper functionality:

#### Required Mappings
- `/var/log:/host/var/log:ro` - System logs
- `/proc:/host/proc:ro` - Process information
- `/sys:/host/sys:ro` - System information
- `/var/run/docker.sock:/var/run/docker.sock` - Docker management
- `/mnt/user/appdata/unraid-mcp-server:/app/data` - Persistent data

#### Optional Mappings
- `/mnt/user:/host/mnt/user:ro` - User shares access
- `/boot:/host/boot:ro` - Unraid configuration
- `/var/lib/docker:/host/var/lib/docker:ro` - Docker data

## 🔧 Usage

### With Claude AI

1. **Install Claude Desktop or use Claude.ai**
2. **Configure MCP client** to connect to your server:
   ```json
   {
     "mcpServers": {
       "unraid": {
         "command": "curl",
         "args": ["http://your-unraid-ip:9090/mcp"]
       }
     }
   }
   ```

3. **Start using AI commands**:
   - "Check my server's health status"
   - "Show me Docker containers using the most resources"
   - "Analyze recent error logs"
   - "Optimize my Plex library"
   - "Schedule maintenance tasks"

### Available Tools

#### System Diagnostics
- `get_system_overview` - Comprehensive system status
- `get_disk_health` - SMART disk health analysis
- `get_temperature_status` - Temperature monitoring
- `get_network_status` - Network interface status
- `get_process_info` - Process information and resource usage
- `check_system_health` - Overall health assessment

#### Docker Management
- `list_containers` - List all containers with status
- `manage_container` - Start, stop, restart containers
- `get_container_stats` - Resource usage statistics
- `get_container_logs` - Container log analysis
- `cleanup_docker` - Remove unused images and volumes
- `update_containers` - Check for and apply updates

#### Plex Integration
- `get_plex_status` - Plex server status and performance
- `analyze_plex_library` - Library statistics and optimization
- `get_plex_sessions` - Active streaming sessions
- `optimize_plex_database` - Database maintenance
- `scan_plex_libraries` - Trigger library scans

#### Log Analysis
- `analyze_system_logs` - Parse and analyze system logs
- `search_logs` - Search logs for specific patterns
- `get_error_summary` - Summary of recent errors
- `monitor_log_patterns` - Real-time log monitoring
- `generate_log_report` - Comprehensive log analysis report

#### Maintenance
- `run_cleanup` - System cleanup and optimization
- `check_updates` - Available system updates
- `verify_backups` - Backup integrity verification
- `schedule_maintenance` - Schedule automated tasks
- `optimize_system` - Performance optimization recommendations

## 🔒 Security

### Authentication
- Optional API key authentication
- Rate limiting and request validation
- Secure credential storage
- Minimal privilege execution

### Container Security
- Non-root user execution
- Read-only filesystem where possible
- Capability dropping
- Security scanning with Trivy

### Network Security
- Internal network isolation
- Configurable port exposure
- TLS support (optional)
- Request logging and monitoring

## 📊 Monitoring & Health

### Health Checks
The server includes comprehensive health monitoring:
- HTTP endpoint health checks
- Process monitoring
- Resource utilization tracking
- Error rate monitoring
- Performance metrics

### Logging
- Structured JSON logging
- Log rotation and retention
- Multiple log levels
- Error tracking and alerting

### Metrics
- Prometheus metrics export
- Grafana dashboard templates
- Performance monitoring
- Resource usage tracking

## 🔧 Development

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kt1928/tower_mcpv2.git
   cd tower_mcpv2
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements
   ```

3. **Run locally**:
   ```bash
   python src/main.py
   ```

### Building Docker Image

```bash
docker build -t kappy1928/tower_mcpv2:latest .
```

### Running Tests

```bash
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 📚 API Documentation

Complete API documentation is available at:
- **OpenAPI Docs**: `http://your-server:8080/docs`
- **ReDoc**: `http://your-server:8080/redoc`
- **Health Endpoint**: `http://your-server:8080/health`

## 🐛 Troubleshooting

### Common Issues

1. **Container won't start**:
   - Check volume mappings
   - Verify Docker socket permissions
   - Review container logs: `docker logs unraid-mcp-server`

2. **Permission denied errors**:
   - Ensure proper user/group permissions
   - Check volume mount permissions
   - Verify Docker group membership

3. **Plex integration not working**:
   - Verify Plex URL and token
   - Check network connectivity
   - Ensure Plex server is accessible

4. **High resource usage**:
   - Adjust monitoring intervals
   - Disable unnecessary tools
   - Review log levels

### Getting Help

- **GitHub Issues**: [Report bugs and request features](https://github.com/kt1928/tower_mcpv2/issues)
- **Unraid Forums**: [Community support](https://forums.unraid.net/)
- **Discord**: [Real-time chat support](https://discord.gg/unraid)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Unraid Team** - For the amazing NAS platform
- **MCP Community** - For the Model Context Protocol
- **Claude AI** - For AI assistant integration
- **Docker Community** - For containerization tools
- **Open Source Contributors** - For the various libraries and tools used

## 🗺 Roadmap

### Version 1.1
- [ ] Web-based configuration interface
- [ ] Advanced alerting and notifications
- [ ] Custom dashboard creation
- [ ] Plugin system for extensions

### Version 1.2
- [ ] Machine learning for predictive analytics
- [ ] Advanced automation workflows
- [ ] Multi-server support
- [ ] Enhanced security features

### Version 2.0
- [ ] Complete UI rewrite
- [ ] Advanced AI integration
- [ ] Cloud synchronization
- [ ] Enterprise features

---

**Made with ❤️ for the Unraid community**