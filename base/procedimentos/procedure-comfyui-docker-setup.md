# PROCEDURE: ComfyUI Docker CUDA Setup

**TRIGGER:** Setting up a local ComfyUI image generation environment on a machine with an NVIDIA GPU
**DOMAIN:** ai-image-generation / deployment
**PRE-CONDITIONS:**
- Docker and Docker Compose installed
- NVIDIA GPU with CUDA support available
- Sufficient disk space (500 GB+ for full model set)
- No requirement for cloud API — full local control desired

---

## STEPS

1. Clone repository → `git clone https://github.com/akitaonrails/ComfyUI-Docker-CUDA-preloaded.git && cd ComfyUI-Docker-CUDA-preloaded`
2. Build the Docker image → `docker compose build` (downloads base Ubuntu 24 image, installs Python 3.12, pip packages into `/venv`)
3. Edit `models.conf` before first run → remove sections for model categories not needed to reduce initial download from ~500 GB
4. Start the stack without daemon flag → `docker compose up` (NOT `docker compose up -d`) — keep terminal visible to monitor extension errors and model download progress
5. Wait for `init_models.sh` to execute → it reads `models.conf`, downloads each URL to its corresponding `models/<section>` subdirectory, skips already-downloaded files on subsequent restarts
6. Wait for `init_extensions.sh` to execute → it clones `extensions.conf` repos into `custom_nodes/`, runs `pip install -r requirements.txt` only for extensions whose last commit hash changed since previous run
7. Open browser at `http://localhost:8188` → ComfyUI web interface loads with all nodes available

**ON_FAILURE[step-6 Python dependency conflict]:**
```bash
docker compose down
docker volume rm comfyui-venv
rm ./custom_nodes/.last_commits/*.commit
docker compose up
```
VENV is rebuilt from scratch with Python 3.12; all extensions reinstall their dependencies cleanly.

**ON_FAILURE[step-6 extension crash without error message]:**
Navigate to `./custom_nodes/`, delete the offending extension directory manually, restart container.

**ON_FAILURE[step-7 node shows red border during workflow run]:**
Node is missing a required model file. Read the node name, search Google for the `.safetensors` or `.pth` filename, download manually and place in the correct `models/<subdirectory>`.

---

## DONE WHEN
- Browser loads ComfyUI at `localhost:8188` without errors
- All nodes in a loaded workflow show no red borders before running
- Console shows no `ModuleNotFoundError` or missing file warnings for desired model categories
- Running a workflow queues a job and processes to completion with green node borders

## SOURCE
https://akitaonrails.com/2025/04/20/gerando-imagens-com-i-a-ate-estilo-ghibli-com-docker-e-cuda/
