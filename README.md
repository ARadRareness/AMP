# AMP - Agent Management Platform

AMP is a comprehensive solution for managing and orchestrating AI agents, designed to streamline interactions and enhance productivity.

## Features

- **GGUF Model Support**: Utilize Llama.cpp for efficient inference with GGUF models
- **Multi-Conversation Server**: Flask-based server handling multiple simultaneous conversations
- **Management Interface**: Gradio-powered interface for system management and control

## Getting Started

### 1. Clone this repository
```
git clone https://github.com/ARadRareness/AMP.git
```

### 2. (Optionally) Create a conda environment.
```
conda create -n amp
```

### 3. (Optionally) Activate the environment.
```
conda activate amp
```

### 4. Install requirements
For Windows using CUDA, install the following requirements
```
python -m pip install torch torchvision torchaudio --index-url http://download.pytorch.org/whl/cu118 --trusted-host download.pytorch.org
python -m pip install https://github.com/jllllll/bitsandbytes-windows-webui/releases/download/wheels/bitsandbytes-0.41.1-py3-none-win_amd64.whl
```

Then run the following command to install the rest of the requirements
```
pip install -r requirements.txt
```


## Running

Make sure you first download a gguf-model ([Meta-Llama-3-8B-Instruct-GGUF is recommended](https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF)) and put it in the models folder. You will also need to put a llama.cpp-server binary in the bin folder. After that run the server using one of the following commands:

```bash
python server.py
python3 server.py
```