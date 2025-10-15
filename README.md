![Kafkatui Logo](./docs/kafkatui.png)

# Kafkatui
A **terminal user interface (TUI)** for exploring and monitoring **Apache Kafka** clusters — built with [Textual](https://github.com/Textualize/textual).

---

## Overview
**Kafkatui** lets you navigate topics, inspect partitions, and read messages directly from the terminal — without external dashboards or web UIs.

It’s fast, keyboard-driven, and ideal for quick debugging or development environments.

---

## Features
- Filter topics dynamically  
- View topic information (partitions, offsets, message count)  
- Inspect the latest messages per topic  
- Optional auto-refresh for messages  
- Pretty-print JSON payloads in a modal  
- Support for **SASL/SSL** authentication (optional)

---

## Installation

### Clone & Run
```bash
git clone https://github.com/youruser/kafkatui.git
cd kafkatui
pip install -r requirements.txt
python app.py
```

### Run with Docker
```bash
docker build -t kafkatui .
docker run -it --rm kafkatui
```

## Usage
```bash
python app.py --bootstrap <broker:port> [options]
```

### Common flags

| Flag | Description | Default |
|------|--------------|----------|
| `--bootstrap` | Kafka bootstrap server(s) | `127.0.0.1:9094` |
| `--security-protocol` | Connection type (`PLAINTEXT`, `SASL_PLAINTEXT`, `SASL_SSL`, `SSL`) | `PLAINTEXT` |
| `--sasl-mechanism` | SASL mechanism (`PLAIN`, `SCRAM-SHA-256`, `SCRAM-SHA-512`, etc.) | _optional_ |
| `--username` | SASL username | _optional_ |
| `--password` | SASL password | _optional_ |
| `--ssl-cafile` | Path to CA cert file | _optional_ |
| `--ssl-certfile` | Path to client cert | _optional_ |
| `--ssl-keyfile` | Path to client key | _optional_ |

#### Examples
```bash
# Plaintext local cluster
python app.py --bootstrap 127.0.0.1:9094

# SASL/PLAIN authentication
python app.py --bootstrap broker.example.com:9092 \
  --security-protocol SASL_PLAINTEXT \
  --sasl-mechanism PLAIN \
  --username admin --password secret

# SASL/SSL with SCRAM-SHA-512
python app.py --bootstrap broker.example.com:9093 \
  --security-protocol SASL_SSL \
  --sasl-mechanism SCRAM-SHA-512 \
  --username alice --password s3cr3t \
  --ssl-cafile ./ca.pem
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `/` | Focus the search bar |
| `r` | Reload topic list |
| `a` | Toggle auto-refresh for messages |
| `Enter` | Open the selected message in a modal view |
| `Esc` | Clear search or close modal |
| `q` | Quit the application |

### Basic navigation
1. Use the **arrow keys** ↑ / ↓ to move through the topic list.  
2. Press **Enter** to open a topic and view its partitions and messages.  
3. Navigate through the message list and press **Enter** again to inspect one in detail.  
4. While viewing a message, press **Esc** or **q** to close the modal.  
5. Toggle **auto-refresh** with `a` to keep messages updating in real time.

## Tech Stack

- **Python 3.11+**
- **[Textual](https://textual.textualize.io/)** — modern TUI framework for building terminal apps  
- **[Kafka-Python](https://github.com/dpkp/kafka-python)** — Python client for Apache Kafka  
- **[Rich](https://github.com/Textualize/rich)** — syntax highlighting and JSON rendering  
- **Docker** — optional containerized runtime for quick setup

---

## Notice

Kafkatui is currently **under active development**.  
Expect rough edges — features may change frequently, and bugs may exist.  

Feedback, ideas, and contributions are highly appreciated!  
Feel free to open issues or pull requests on the repository.


## License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](./LICENSE) file for details.  

© 2025 — [Leonel Gareis](https://github.com/leoneldgg)