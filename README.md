# 🌐 Domain Manager

**Domain Manager** is a tool designed to automatically manage domains on OVH based on Docker container events. 🐳 It listens to Docker events and creates or removes subdomains accordingly, making it easier to automate the handling of domains for your containers.

## ✨ Features
- 🔄 Automatic creation and deletion of subdomains based on Docker container lifecycle events.
- 🌍 Support for OVH domain provider.
- ⚙️ Customizable settings using environment variables.

## 📋 Requirements
- 🐍 Python 3.9+
- 🐳 Docker
- 🔑 OVH API credentials

## 📥 Installation
Clone the repository and install the dependencies:

```sh
$ git clone https://github.com/arasemco/DomainManager.git
$ cd DomainManager
$ pip install .
```

Alternatively, you can use `setup.py` to install:

```sh
$ python setup.py install
```

## 🌱 Environment Variables
The following environment variables are used to configure the domain manager:

- **🌐 DOMAIN_NAME**: The main domain name to manage subdomains under.
- **🎯 TARGET**: The target IP address or hostname for the subdomains (defaults to `DOMAIN_NAME` if not set).
- **🛠️ PROVIDER**: The domain provider (`OVH`).
- **🔑 APPLICATION_KEY** (for OVH): Your OVH application key.
- **🗝️ APPLICATION_SECRET** (for OVH): Your OVH application secret.
- **🔓 CONSUMER_KEY** (for OVH): Your OVH consumer key.

## 🚀 Usage
To start listening for Docker events and manage domains accordingly, run the following command:

```sh
$ ovh-domain-manager
```

The tool will listen for Docker events such as container creation and destruction, and manage the associated subdomains automatically.

## 🛠️ Configuration
The tool uses `python-dotenv` to load environment variables from a `.env` file. You can create a `.env` file in the root directory of your project to specify your environment variables.

Example `.env` file:

```
DOMAIN_NAME=example.com
TARGET=192.168.1.100
PROVIDER=OVH
APPLICATION_KEY=your_ovh_application_key
APPLICATION_SECRET=your_ovh_application_secret
CONSUMER_KEY=your_ovh_consumer_key
```

## 📜 License
This project is licensed as Freeware.

## 👤 Author
Developed by **Aram SEMO**. For any inquiries, you can reach me at [📧 aram.semo@asemo.pro](mailto:aram.semo@asemo.pro).

## 🤝 Contributing
Feel free to submit issues or pull requests to contribute to the project. Contributions are always welcome! ✨
