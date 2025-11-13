# GitSense: The Autonomous Developer's Co-pilot

**GitSense** is not just a chatbot. It's an autonomous, multi-agent AI system designed for complex software development tasks. It writes code, reads files, runs tests in a secure sandbox, and *autonomously self-corrects* its own work until the tests pass.

Built on a hybrid cloud/local architecture, it functions both online (leveraging powerful cloud models) and completely offline (using local SLMs).

---

## Core Features

* **Hybrid Agent Architecture:** Dynamically routes tasks between a fast, local SLM (`Ollama`) for simple tasks and a "pro-level" LMM (`GPT-4o/Claude 3.5`) for complex reasoning.
* **Cyclical Self-Correction:** Uses **LangGraph** to create a stateful orchestrator. If the generated code fails a test, the orchestrator automatically re-routes the task (along with the error log) back to the coding agent for another attempt.
* **Secure Sandboxed Execution:** A "CI/CD Bot" that uses **Docker Compose** to spin up entire environments (e.g., code + RabbitMQ) and executes tests via the **GitHub Actions API**. This ensures code is tested safely and realistically, with zero risk to the host.
* **Hybrid RAG (Online/Offline):** Features a dual RAG system. In the cloud, it uses **Azure AI Search** for massive context. Offline, it seamlessly switches to a local **ChromaDB** instance, enabling `coder_agent_low_cost` to function without internet.
* **Reliable Tooling (MCP + Instructor):** All agent tools are defined using the **Model Context Protocol (MCP)** standard. All outputs are converted to reliable, structured data (**Instructor**) for predictable logic.

---

## System Architecture

The system is built on a "separation of concerns" model: a central **Orchestrator** (the `master_agent`) manages the flow, while specialized **Agents** (the "brains") and **Tools** (the "hands") execute the tasks.



### 1. The Orchestrator (`master_agent`)

* **Technology:** **LangGraph**
* **Role:** This is *not* an LLM. It's a "hardcoded" (reliable) state machine that directs the flow of work. It is the "brain" of the self-correction loop and holds the application state (e.g., `iterations_remaining`).

### 2. The Agents (The "Brains")

* **`router_agent`:**
    * **Model:** Local SLM (Ollama `phi-3`).
    * **Role:** The "GPS." Its only job is to analyze the user's prompt and output a structured JSON (via `Instructor`) telling the `master_agent` which agent to call next (e.g., `{"route": "coder_expert"}`).
* **`coder_agent_expert`:**
    * **Model:** Cloud LMM (Azure `GPT-4o`).
    * **Role:** The "Pro Developer." Handles complex logic, multimodal inputs (sees error screenshots), and the primary code generation/correction cycle.
* **`coder_agent_low_cost`:**
    * **Model:** Local SLM (Ollama `phi-3` or `Llama-3-8B`).
    * **Role:** The "Offline Developer." Handles simple requests or operates when no internet is detected. Uses the local `ChromaDB` for RAG.
* **`metrics_agent`:**
    * **Model:** Any (e.g., `GPT-3.5-Turbo`).
    * **Role:** The "Analyst." Uses the `get_github_metrics` tool and `Instructor` to return perfectly formatted JSON about a repository's health.

---

## Core Tech Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Orchestration** | **LangGraph** | The core `master_agent` state machine for cyclical logic. |
| **Tool Standard** | **Model Context Protocol (MCP)** | Defines the "API" for all tools the agents can use. |
| **Models (Local)** | **Ollama** (`Phi-3`, `Llama 3`) | Powers the `router_agent` and `coder_agent_low_cost`. |
| **Models (Cloud)** | **Azure OpenAI** / **Amazon Bedrock** | Powers the `coder_agent_expert` with GPT-4o / Claude 3.5. |
| **RAG (Local)** | **ChromaDB** | Vector store for offline RAG. |
| **RAG (Cloud)** | **Azure AI Search** | Scalable, persistent vector store for online RAG. |
| **Backend** | **FastAPI** | Serves the entire application as a robust API. |
| **Sandboxing** | **Docker / Docker Compose** | Defines the *environment* for code testing (e.g., app + RabbitMQ). |
| **Execution** | **GitHub Actions API** | The *executor* that securely runs the Docker Compose sandbox. |
| **Deployment** | **Azure Container Apps** | Hosts the main FastAPI application. |
| **Security** | **Azure Key Vault** | Securely manages all API keys (Azure, GitHub, etc.). |

---

## How it Works: The Self-Correction Loop

This is the project's "showoff" feature.

1.  **Ask:** User submits a complex task: "This code for RabbitMQ is broken. Fix it."
2.  **Route:** `router_agent` (SLM) classifies the task as `"complex"` and `"code"`.
3.  **Dispatch:** `master_agent` (LangGraph) receives the route and passes the state to `coder_agent_expert`.
4.  **Generate:** `coder_agent_expert` uses its `RAG_tool` to get context and generates a fix (`fixed_code.py`, `test_code.py`, `docker-compose.yml`).
5.  **Test:** `master_agent` (LangGraph) receives the code and transitions to the `test_code_tool` node.
6.  **Sandbox:** The `test_code_tool` *doesn't* run the code. It makes an API call to **GitHub Actions**, passing all files.
7.  **CI/CD:** A GitHub Actions runner spins up, runs `docker compose up`, executes `pytest`, and the test *fails*.
8.  **Evaluate:** The GitHub job finishes, returning the `stderr` log to the `test_code_tool`.
9.  **Correct (The Loop):** `master_agent` (LangGraph) receives the error log. It checks its state: `error_log is not None` and `iterations_remaining > 0`. It **decrements the counter** and transitions *back* to the `coder_agent_expert` node, this time passing the *original prompt + the new error log*.
10. **Succeed:** The `coder_agent_expert` now sees its mistake ("Ah, I forgot to wait for the queue"). It generates a new fix. The loop repeats until the `test_code_tool` returns an empty error log.
11. **Respond:** `master_agent` transitions to the "FIN" node and returns the final, *validated* code to the user.

---

## Getting Started (Local / Offline Mode)

This setup runs the entire system locally using the `coder_agent_low_cost` and `ChromaDB`.

1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/your-username/gitsense.git](https://github.com/your-username/gitsense.git)
    cd gitsense
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install & Run Ollama:**
    * [Download Ollama](https://ollama.com/)
    * Pull the models:
        ```bash
        ollama pull phi-3
        ollama pull llama-3-8b
        ```
4.  **Run the local RAG ingestion:**
    * (You will build a script to "feed" files to ChromaDB here)
    ```bash
    python ingest_local_rag.py --source /path/to/docs
    ```
5.  **Run the application:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

---

## Deployment (Cloud / Pro Mode)

This deploys the full-power, hybrid application to Microsoft Azure.

1.  **Provision Azure Resources:**
    * Create an **Azure OpenAI** service and deploy `gpt-4o`.
    * Create an **Azure AI Search** service for the cloud RAG.
    * Create an **Azure Key Vault** to store your secrets.
2.  **Configure GitHub:**
    * Create a GitHub App or Personal Access Token (PAT) with `actions:write` permissions.
    * Store this token in your **Azure Key Vault**.
3.  **Deploy the App:**
    * Containerize the FastAPI application using the provided `Dockerfile`.
    * Push the container to Azure Container Registry (ACR).
    * Deploy the container to **Azure Container Apps**.
    * In the Container App's configuration, securely inject the secrets from **Key Vault** as environment variables.

---

## TFG Roadmap & Future Work

This project serves as the foundation (Phase 1) for a TFG focused on high-performance ML systems (Phase 2).

### Phase 1: Architectural Foundation (This README)

* [ ] Build `master_agent` (LangGraph) with state management.
* [ ] Build `router_agent` with `Instructor`.
* [ ] Implement hybrid RAG (`ChromaDB` / `Azure AI Search`).
* [ ] Build `test_code_tool` with GitHub Actions API integration.
* [ ] Deploy the full stack to Azure Container Apps.

### Phase 2: TFG - Inference Optimization

The goal of the TFG is to **replace the generic `coder_agent_low_cost` with a custom, ultra-optimized inference engine.**

* [ ] **Fine-Tune:** Fine-tune an SLM (e.g., `Phi-3-medium`) on a massive dataset of "code bug -> code fix" examples.
* [ ] **Kernel-Level Optimization:** Identify the key bottleneck in the fine-tuned model (e.g., attention mechanism) and write a **custom GPU kernel using Triton** to accelerate it.
* [ ] **Optimized Serving:** Serve the custom model using a high-performance server like **NVIDIA Triton Inference Server**.
* [ ] **Benchmark:** Conclude the TFG by benchmarking the new, optimized agent against the generic `GPT-4o` agent.
    * **Hypothesis:** The custom agent will be 15x faster and 90% cheaper at 95% of the `GPT-4o`'s accuracy *for this specific task*.

---