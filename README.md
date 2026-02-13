
This project is a fully Dockerized application composed of multiple containers: `backend`, `ollama`, `postgresql`, and `streamlit`.

- **Backend**: Built with [FastAPI](https://fastapi.tiangolo.com/) to handle API requests.
- **PostgreSQL**: Uses the official Docker image with the [`pgvector`](https://github.com/pgvector/pgvector) extension for vector database support.
- **Ollama**: Runs CPU-only language models for NLP tasks.
- **Streamlit**: Provides a web-based frontend to interact with the system.

---
## Note

- Ollama is configured for CPU-only execution.

- Always ensure your custom models are registered in the Ollama container if you replace the default models.

- PostgreSQL includes the pgvector extension for vector similarity operations

---

## Installation & Setup

1. **Download Language Models**

   Use the provided script to download language models:

   ```bash
   ./install-llms.sh
   ```

    By default, the following models are downloaded:

    - **Qwen3-0.6B-GGUF**
    - **paraphrase-multilingual-MiniLM-L12-v2**

    After downloading, the Qwen3-0.6B-GGUF model is added to the Ollama model list via:
    
    ```bash
    ollama list
    ```

    Note: If you use custom models, make sure to update the entrypoint.sh script of the Ollama container accordingly.

1. **Run the Project**

    From the root directory, execute:
    ```bash
    make run
    ```

    This will start all containers.

    Access the Application

    Once running, open your browser and navigate to:

    ```arduino
    http://localhost:8501
    ```

    You can now interact with the system via the Streamlit interface
