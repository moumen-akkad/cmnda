import os
import json
import urllib.parse
import requests
import base64

 
# BaSyx Python SDK
from basyx.aas.model import aas, submodel as smm, base
from basyx.aas.adapter.json import json_serialization
 
# -----------------------
# Config (override via env)
# -----------------------
BASE_URL = os.getenv("BASYX_BASE_URL", "http://localhost:8081")  # AAS Environment base URL
AAS_REPO = os.getenv("BASYX_AAS_REPO", BASE_URL)                 # or separate AAS repo base
SM_REPO  = os.getenv("BASYX_SM_REPO",  BASE_URL)                 # or separate SM repo base
 
# The HTTP endpoint that will *execute* the delegated operation.
# For a quick test, point it to a tiny echo service you control, e.g. http://localhost:5001/op
DELEGATE_URL = os.getenv("DELEGATE_URL", "http://localhost:5001/op")
 
# Identifiers (keep them URL-safe; avoid '#', spaces, etc.)
AAS_ID  = os.getenv("AAS_ID", "urn:example:aas:demo:1")
AAS_ID_SHORT = os.getenv("AAS_ID_SHORT", "DemoAAS")
SM_ID   = os.getenv("SM_ID", "urn:example:sm:ops:1")
SM_ID_SHORT = os.getenv("SM_ID_SHORT", "Ops")
OP_ID_SHORT = os.getenv("OP_ID_SHORT", "hello")  # minimal op (no in/out variables)
 
# -----------------------
# Build AAS + Submodel
# -----------------------
 
# 1) Minimal Operation (no input/output) + delegation qualifier
delegation = base.Qualifier(
    type_="invocationDelegation",   # required key for BaSyx operation delegation
    value_type=str,                 # xs:string
    value=DELEGATE_URL
)
op = smm.Operation(
    id_short=OP_ID_SHORT,
    qualifier=(delegation,)         # attach the delegation qualifier
    # no input_variable / output_variable / in_output_variable -> "simplest" op
)
 
# 2) Minimal Submodel that contains the operation
submod = smm.Submodel(
    id_=SM_ID,
    id_short=SM_ID_SHORT,
    submodel_element=(op,)
)
 
# 3) Minimal AAS that will reference the submodel
asset_info = aas.AssetInformation(global_asset_id="urn:example:asset:demo:1")
shell = aas.AssetAdministrationShell(
    id_=AAS_ID,
    id_short=AAS_ID_SHORT,
    asset_information=asset_info
)
 
def b64url_id(identifier: str) -> str:
    """BaSyx v2 expects Base64URL (no '=') for identifier path params."""
    return base64.urlsafe_b64encode(identifier.encode("utf-8")).decode("ascii").rstrip("=")

# -----------------------
# Serialize for REST
# -----------------------
def to_json(obj) -> dict:
    """Serialize a single Identifiable to JSON (stripped) as BaSyx expects."""
    # The SDK helper encodes whole object stores; here we encode a single object via dumps+loads
    s = json.dumps(obj, cls=json_serialization.StrippedAASToJsonEncoder)
    return json.loads(s)
 
sm_json  = to_json(submod)
aas_json = to_json(shell)
 
# -----------------------
# Upload helpers
# -----------------------
def ensure_ok(resp: requests.Response, expected=(200,201,204)):
    if resp.status_code not in expected:
        raise RuntimeError(f"{resp.request.method} {resp.request.url} -> "
                           f"{resp.status_code} {resp.text}")
 
def url_join(base, *parts):
    return "/".join([base.rstrip("/")] + [p.strip("/") for p in parts])
 
def url_encode_id(identifier: str) -> str:
    # DotAAS Part 2 path parameter is URL-encoded
    return urllib.parse.quote(identifier, safe="")
 
# -----------------------
# 1) Create Submodel
# -----------------------
print(f"POST Submodel to {SM_REPO}/submodels ...")
r = requests.post(url_join(SM_REPO, "submodels"),
                  json=sm_json,
                  headers={"Content-Type": "application/json"})
ensure_ok(r, expected=(201,200))
print("Submodel created/updated.")
 
# -----------------------
# 2) Create AAS (Shell)
# -----------------------
print(f"POST AAS to {AAS_REPO}/shells ...")
r = requests.post(url_join(AAS_REPO, "shells"),
                  json=aas_json,
                  headers={"Content-Type": "application/json"})
ensure_ok(r, expected=(201,200))
print("AAS created/updated.")
 
# -----------------------
# 3) Link Submodel to AAS
#    POST /shells/{aasId}/submodel-refs with a submodel reference object
# -----------------------
# Build a ModelReference to the Submodel as the REST API expects (stripped form).
# In stripped JSON, a Reference looks like:
# {"type":"ModelReference","keys":[{"type":"Submodel","value":"<submodelId>"}]}
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
# Some BaSyx versions return 201, others 200; if already linked, 409/400 may appear
if r.status_code == 409:
    print("Submodel already linked to AAS.")
else:
    ensure_ok(r, expected=(201,200))
    print("Submodel linked to AAS.")
 
print("\nDone.\n")
print(f"AAS ID: {AAS_ID}")
print(f"Submodel ID: {SM_ID}")
print(f"Operation idShort: {OP_ID_SHORT}")
print(f"Delegation target: {DELEGATE_URL}")
 
# Tip to invoke (manually):
# POST {BASE_URL}/submodels/{urlEncodedSubmodelId}/submodel-elements/{OP_ID_SHORT}/invoke
# with body []  (since the op has no parameters)