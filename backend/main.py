from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import uuid
import time
import os

app = FastAPI()

# ---------------- CORS (Required for React) ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------

# In-memory audit log
audit_log = []

MAX_STORES = 5

# Resolve project paths safely
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
HELM_CHART_PATH = os.path.join(PROJECT_ROOT, "helm", "store")
VALUES_LOCAL_PATH = os.path.join(HELM_CHART_PATH, "values-local.yaml")


@app.get("/")
def root():
    return {"message": "Store Provisioning Platform Running"}


@app.post("/stores")
def create_store():
    # ---- Max store guardrail ----
    ns_list = subprocess.run(
        ["kubectl", "get", "ns", "-o", "jsonpath={.items[*].metadata.name}"],
        capture_output=True,
        text=True
    )

    existing_stores = [
        ns for ns in ns_list.stdout.split() if ns.startswith("store-")
    ]

    if len(existing_stores) >= MAX_STORES:
        raise HTTPException(status_code=400, detail="Max store limit reached")

    store_id = f"store-{uuid.uuid4().hex[:6]}"
    host = f"{store_id}.localhost"

    # ---- Idempotency check ----
    ns_check = subprocess.run(
        ["kubectl", "get", "ns", store_id],
        capture_output=True,
        text=True
    )

    if ns_check.returncode == 0:
        return {
            "store_id": store_id,
            "status": "Already Exists",
            "url": f"http://{host}"
        }

    # ---- Helm install ----
    helm_cmd = [
        "helm", "install", store_id,
        HELM_CHART_PATH,
        "--namespace", store_id,
        "--create-namespace",
        "-f", VALUES_LOCAL_PATH,
        "--set", f"wordpress.ingress.hostname={host}"
    ]

    result = subprocess.run(
        helm_cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=result.stderr
        )

    # ---- Readiness polling ----
    for _ in range(24):
        pod_result = subprocess.run(
            ["kubectl", "get", "pods", "-n", store_id],
            capture_output=True,
            text=True
        )

        if "1/1" in pod_result.stdout:
            audit_log.append(f"Created {store_id}")
            return {
                "store_id": store_id,
                "status": "Ready",
                "url": f"http://{host}"
            }

        time.sleep(5)

    return {
        "store_id": store_id,
        "status": "Provisioning (timeout)",
        "url": f"http://{host}"
    }


@app.get("/stores")
def list_stores():
    result = subprocess.run(
        ["kubectl", "get", "ns", "-o", "jsonpath={.items[*].metadata.name}"],
        capture_output=True,
        text=True
    )

    namespaces = result.stdout.split()
    stores = []

    for ns in namespaces:
        if ns.startswith("store-"):
            pod_check = subprocess.run(
                ["kubectl", "get", "pods", "-n", ns],
                capture_output=True,
                text=True
            )

            status = "Provisioning"
            if "1/1" in pod_check.stdout:
                status = "Ready"

            stores.append({
                "store_id": ns,
                "status": status,
                "url": f"http://{ns}.localhost"
            })

    return {"stores": stores}


@app.delete("/stores/{store_id}")
def delete_store(store_id: str):
    subprocess.run(["helm", "uninstall", store_id, "-n", store_id])
    subprocess.run(["kubectl", "delete", "namespace", store_id])

    audit_log.append(f"Deleted {store_id}")
    return {"deleted": store_id}


@app.get("/audit")
def get_audit():
    return {"events": audit_log}
