## Domain Manager

### Overview

The Domain Manager is a Python-based system designed to automatically manage subdomains via multiple DNS providers, such as OVH and Cloudflare. The project listens to container events and adds or removes subdomains accordingly, based on specific labels attached to the container.

### Features

- **Supports Multiple DNS Providers**: Compatible with OVH and Cloudflare, providing flexibility for managing subdomains.
- **Automatic Subdomain Management**: Automatically adds or removes subdomains based on container events, making management easy and efficient.
- **Environment-based Configuration**: Easily manage provider credentials, domain details, and container configuration using environment variables.

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/arasemco/DomainManager.git
   cd domain-manager
   ```

2. Install the required dependencies:

   ```bash
   pip install .
   ```

3. Create an `.env` file at the project root to configure environment variables:

   ```env
   DNM_PROVIDER=OVH  # Available options: OVH, CLOUDFLARE
   DNM_OVH_APPLICATION_KEY=<your_ovh_application_key>
   DNM_OVH_APPLICATION_SECRET=<your_ovh_application_secret>
   DNM_OVH_CONSUMER_KEY=<your_ovh_consumer_key>
   DNM_CLOUDFLARE_API_TOKEN=<your_cloudflare_api_token>
   DNM_DOMAIN_NAME=<your_domain_name>
   DNM_TARGET=<your_target>
   DNM_DOCKER_BASE_URL=unix://var/run/docker.sock
   ```

### Usage

1. Ensure that Docker is running.

2. Start the Domain Manager by running the main Python script:

   ```bash
   python main.py
   ```

   The system will listen to container events and automatically add or remove subdomains based on container labels when they are created (create event) or removed (destroy event).

3. Alternatively, you can use Docker Compose to run the Domain Manager:

   ```bash
   docker compose up --build
   ```

### Event Labels

To manage subdomains via Docker containers, include the following label on your container. If you are using Traefik, it will utilize this label, otherwise add the label to create a subdomain for your Apache/Nginx/etc:

- `traefik.http.routers.web.rule`: Specifies the hostname rule for Traefik. The format should be ``Host(`subdomain.domain.com`)``.

Supported actions:

- **create**: Add a subdomain for the container.
- **destroy**: Remove the subdomain.
- **future**: The start action will verify if the subdomain exists, and if not, it will add it.

### Extending Providers

You can add new DNS providers by creating a new class in `src.providers` package that extends `SubdomainProvider` and implements the required abstract methods, along with a few tests to ensure functionality.

### License

This project is open-source.

### Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to enhance the Domain Manager.

### Contact

**Author**: Aram SEMO  
**Email**: [aram.semo@asemo.pro](mailto:aram.semo@asemo.pro)  
**Helper**: OpenAI ChatGPT
