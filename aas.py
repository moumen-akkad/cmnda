import os
import json
import base64
import requests

# -----------------------
# Config (override via env)
# -----------------------
BASE_URL = os.getenv("BASYX_BASE_URL", "http://localhost:8081")
AAS_REPO = os.getenv("BASYX_AAS_REPO", BASE_URL)
SM_REPO  = os.getenv("BASYX_SM_REPO",  BASE_URL)

DELEGATE_URL = os.getenv("DELEGATE_URL", "http://localhost:5001/op")

AAS_ID       = os.getenv("AAS_ID", "urn:example:aas:demo:1")
AAS_ID_SHORT = os.getenv("AAS_ID_SHORT", "DemoAAS")
SM_ID        = os.getenv("SM_ID", "urn:example:sm:ops:1")
SM_ID_SHORT  = os.getenv("SM_ID_SHORT", "Ops")
OP_ID_SHORT  = os.getenv("OP_ID_SHORT", "hello")

def b64url_id(identifier: str) -> str:
    return base64.urlsafe_b64encode(identifier.encode("utf-8")).decode("ascii").rstrip("=")

def url_join(base, *parts):
    return "/".join([base.rstrip("/")] + [p.strip("/") for p in parts])

def ensure_ok(resp: requests.Response, expected=(200,201,204)):
    if resp.status_code not in expected:
        raise RuntimeError(f"{resp.request.method} {resp.request.url} -> "
                           f"{resp.status_code} {resp.text}")

# -----------------------
# Minimal JSON payloads (AAS v3-style)
# -----------------------

# 1) Submodel with one delegated Operation
submodel_json = {
    "modelType": "Submodel",
    "id": SM_ID,
    "idShort": SM_ID_SHORT,
    "submodelElements": [
        {
            "modelType": "Operation",
            "idShort": OP_ID_SHORT,
            "qualifiers": [
                {
                    "type": "invocationDelegation",
                    "valueType": "xs:string",
                    "kind": "ConceptQualifier",
                    "value": DELEGATE_URL
                }
            ]
        }
    ]
}

# 2) AAS (shell)
aas_json = {
    "modelType": "AssetAdministrationShell",
    "id": AAS_ID,
    "idShort": AAS_ID_SHORT,
    "assetInformation": {
        "assetKind": "Instance",
        "globalAssetId": "urn:example:asset:demo:1"
    }
}

# -----------------------
# Upload
# -----------------------
print(f"POST Submodel to {SM_REPO}/submodels ...")
r = requests.post(url_join(SM_REPO, "submodels"),
                  json=submodel_json,
                  headers={"Content-Type": "application/json"})
ensure_ok(r, expected=(201,200))
print("Submodel created/updated.")

print(f"POST AAS to {AAS_REPO}/shells ...")
r = requests.post(url_join(AAS_REPO, "shells"),
                  json=aas_json,
                  headers={"Content-Type": "application/json"})
ensure_ok(r, expected=(201,200))
print("AAS created/updated.")

# 3) Link Submodel to AAS
submodel_ref = {
    "type": "ModelReference",
    "keys": [
        {"type": "Submodel", "value": SM_ID}
    ]
}

shell_id_enc = b64url_id(AAS_ID)
print(f"POST submodel-ref to {AAS_REPO}/shells/{shell_id_enc}/submodel-refs ...")
r = requests.post(url_join(AAS_REPO, "shells", shell_id_enc, "submodel-refs"),
                  json=submodel_ref,
                  headers={"Content-Type": "application/json"})
if r.status_code == 409:
    print("Submodel already linked to AAS.")
else:
    ensure_ok(r, expected=(201,200))
    print("Submodel linked to AAS.")

# -----------------------
# Done + manual invoke hint
# -----------------------
print("\nDone.\n")
print(f"AAS ID: {AAS_ID} -> {b64url_id(AAS_ID)}")
print(f"Submodel ID: {SM_ID} -> {b64url_id(SM_ID)}")
print(f"Operation idShort: {OP_ID_SHORT}")
print(f"Delegation target: {DELEGATE_URL}")

print("\nInvoke manually with:")
print(f"curl -s -X POST -H 'Content-Type: application/json' -d '[]' "
      f"'{BASE_URL}/submodels/{b64url_id(SM_ID)}/submodel-elements/{OP_ID_SHORT}/invoke'")
