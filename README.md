# 🌐 Domain Manager

## Overview
The **Domain Manager** is a tool designed to manage domain records automatically based on Docker container events, such as create and destroy. The tool supports different DNS providers, including **Cloudflare** and **OVH**, leveraging their APIs to dynamically create or remove subdomains.

## ✨ Features
- 📡 Monitors Docker container events.
- 🔄 Automatically creates and removes subdomains based on container lifecycle.
- 🌍 Supports Cloudflare and OVH as DNS providers.
- 🛠️ Logging for tracking and debugging.
- ⚙️ Configurable through environment variables.

## 📋 Prerequisites
- Docker installed and running.
- Python 3.6 or higher.
- Appropriate credentials for the supported DNS provider (Cloudflare or OVH).

## 📥 Installation
### Using Docker
1. **Create a `.env` file** with the following environment variables:
   ```
   DNM_ENV=development
   DNM_DOCKER_BASE_URL=unix://var/run/docker.sock
   DNM_DOMAIN_NAME=yourdomain.com
   DNM_TARGET=targetdomain.com  # Typically matched with DNM_DOMAIN_NAME
   DNM_PROVIDER=OVH  # Or CLOUDFLARE
   DNM_OVH_APPLICATION_KEY=your_ovh_application_key
   DNM_OVH_APPLICATION_SECRET=your_ovh_application_secret
   DNM_OVH_CONSUMER_KEY=your_ovh_consumer_key
   DNM_CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
   ```
2. **Build and run** the Docker container using `docker-compose`:
   ```sh
   docker-compose up --build
   ```

### Manual Installation
1. **Clone the repository**:
   ```sh
   git clone https://github.com/arasemco/DomainManager.git
   cd DomainManager
   ```

2. **Install the required Python packages**:
   ```sh
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** with the appropriate environment variables as mentioned in the Docker setup.

4. **Run the application**:
   ```sh
   python -m src.main
   ```

## ⚙️ Configuration
### Environment Variables
The application is configured using environment variables defined in a `.env` file located in the project's root directory:

- **`DNM_ENV`**: Environment setting (`development`, `production`).
- **`DNM_DOCKER_BASE_URL`**: Docker socket URL (default: `unix://var/run/docker.sock`).
- **`DNM_DOMAIN_NAME`**: The base domain name for subdomains.
- **`DNM_TARGET`**: Target domain or IP.
- **`DNM_PROVIDER`**: DNS provider (`OVH`, `CLOUDFLARE`).
- **`DNM_OVH_APPLICATION_KEY`**: OVH application key.
- **`DNM_OVH_APPLICATION_SECRET`**: OVH application secret.
- **`DNM_OVH_CONSUMER_KEY`**: OVH consumer key.
- **`DNM_CLOUDFLARE_API_TOKEN`**: Cloudflare API token.

## 🌍 Supported DNS Providers
### Cloudflare
- **`DNM_CLOUDFLARE_API_TOKEN`**: Your Cloudflare API token.

### OVH
- **`DNM_OVH_APPLICATION_KEY`**: Your OVH application key.
- **`DNM_OVH_APPLICATION_SECRET`**: Your OVH application secret.
- **`DNM_OVH_CONSUMER_KEY`**: Your OVH consumer key.

## 📂 Project Structure
- **`listener.py`**: Contains the `DockerEventListener` class responsible for listening to Docker events and triggering domain management actions.
- **`base.py`**: Defines the base `DomainManager` class which provides a generic interface for domain-related actions.
- **`cloudflare_handler.py`**: Implements `CloudflareDomainManager` with methods specific to Cloudflare's API.
- **`ovh_handler.py`**: Implements `OVHDomainManager` with methods specific to OVH's API.
- **`logger.py`**: Configures logging for the application.
- **`main.py`**: Entry point for the application that initializes the `DockerEventListener` and starts listening for events.

## 📜 Logging
Logs are generated and stored in both the console and a file named `domain_manager.log`. The logging level is set to `INFO` but can be adjusted as needed within `logger.py`.

## 📝 License
This project is licensed under the **Freeware** license.

## 👤 Author
- **Aram SEMO**
  - Email: [aram.semo@asemo.pro](mailto:aram.semo@asemo.pro)
  - GitHub: [arasemco](https://github.com/arasemco)

## 🤝 Contributing
Feel free to submit issues or pull requests to contribute to the project. Contributions are always welcome! ✨