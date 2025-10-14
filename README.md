![Kafkatui Logo](./docs/kafkatui.png)


## What is Kafkatui?
Kafkatui is a tui application for monitoring Apache Kafka clusters. It provides a user-friendly interface to view topics, partitions, consumer groups, and messages in real-time.

## Features
- View topics and partitions

## Installation

You can clone the repository and run it directly:
```bash
git clone
cd kafkatui
pip install -r requirements.txt
python src/app.py
```

Or use the provided Dockerfile to build and run a Docker container:
```bash
docker build -t kafkatui .
docker run -it --rm kafkatui
```

## Notice
Kafkatui is currently in early development. Features may be incomplete and bugs may be present. Feedback and contributions are welcome!