# Post-Quantum Secure E-Voting System

A PyQt5-based administrative interface for running and visualizing the [Hyperion voting protocol](https://github.com/hyperion-voting/hyperion) with post-quantum cryptography considerations.

## Overview

This project provides a graphical user interface for:
- **Running the Hyperion Protocol**: Execute the complete voting protocol
- **Viewing Results**: Display tallying results in an easy-to-read table
- **Understanding PQC Migration**: Reference table mapping classical to post-quantum cryptographic components

## Features

- One-click Hyperion protocol execution
- Bulletin board visualization
- Post-quantum cryptography mapping reference
- FastAPI backend for protocol coordination

## Prerequisites

- **Operating System**: Linux (tested on Fedora/Ubuntu) or macOS
- **Python**: Python 3.8 or higher
- **Git**: For cloning the Hyperion repository

## Setup

### 1. Run Setup Script

The setup script will automatically:
- Clone the Hyperion voting protocol repository
- Create a Python virtual environment (`.venv/`)
- Install all required dependencies (PyQt5, Hyperion requirements)
- Install the threshold cryptography library

```bash
chmod +x setup.sh
./setup.sh
```

## License

This project is for research and educational purposes. Refer to the [Hyperion project license](https://github.com/hyperion-voting/hyperion) for the underlying protocol.

---

**⚠️ Note**: This is a demonstration GUI for the Hyperion protocol. The protocol simulates voters internally. This interface is designed for understanding and analyzing the cryptographic operations involved in receipt-free e-voting systems.

