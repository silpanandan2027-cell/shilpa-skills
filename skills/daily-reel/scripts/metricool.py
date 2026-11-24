#!/usr/bin/env python3
"""Steps 4-6: Metricool Trial Reel drafts.

    python3 metricool.py profiles                         # list brands and their blogId
    python3 metricool.py upload FILE                      # upload to Metricool, prints the file URL
    python3 metricool.py draft --video V --cover C --caption caption.txt --when 2026-11-25T19:00:00
    python3 metricool.py get POST_ID                      # the post as Metricool stores it
    python3 metricool.py publish POST_ID [--when ...]     # only after the user says "post"
    python3 metricool.py status POST_ID                   # PENDING / PUBLISHED + public URL

Settings (userId, blogId, timezone) come from content/reel-config.json. The token comes
from METRICOOL_TOKEN; in cloud sessions the proxy adds the saved X-Mc-Auth header for
app.metricool.com, so the placeholder below is replaced on the way out.

A draft is always saved with draft=true, autoPublish=false and shareTrialAutomatically=false
(the Trial Reel is NOT shared to followers automatically). Nothing here posts unless
`publish` is run.
"""
import argparse, base64, datetime as dt, hashlib, json, mimetypes, os, pathlib, sys
import requests

ROOT = pathlib.Path(os.environ.get("REEL_HOME", ".")).resolve()  # the shilpa-skills repo
CFG = json.loads((ROOT / "content" / "reel-config.json").read_text())
API = "https://app.metricool.com/api"
H = {"X-Mc-Auth": os.environ.get("METRICOOL_TOKEN", "proxy_injected"), "Content-Type": "application/json"}
Q = {"userId": str(CFG["metricool"]["userId"]), "blogId": str(CFG["metricool"]["blogId"])}
PART = 10 * 1024 * 1024
TRIAL_TYPE = CFG["metricool"].get("trial_type", "TRIAL_REEL")


def call(method, path, **kw):
    params = {**Q, **kw.pop("params", {})}
    r = requests.request(method, API + path, headers=H, params=params, timeout=120, **kw)
    if r.status_code >= 300:
        sys.exit(f"Metricool {method} {path} -> {r.status_code}: {r.text[:600]}")
    return r.json() if r.text else {}


def data(j):
    return j.get("data", j) if isinstance(j, dict) else j


def upload(path):
    p = pathlib.Path(path)
    raw = p.read_bytes()
    ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    parts = []
    for i in range(0, len(raw), PART):
        chunk = raw[i:i + PART]
        parts.append({"size": len(chunk), "startByte": i, "endByte": i + len(chunk),
                      "hash": base64.b64encode(hashlib.sha256(chunk).digest()).decode()})
    if len(raw) < 5 * 1024 * 1024:  # S3 simple upload: one part
        parts = [{"size": len(raw), "startByte": 0, "endByte": len(raw),
                  "hash": base64.b64encode(hashlib.sha256(raw).digest()).decode()}]
    tx = data(call("PUT", "/v2/media/s3/upload-transactions",
                   json={"resourceType": "planner", "contentType": ctype,
                         "fileExtension": p.suffix.lstrip("."), "parts": parts}))
    if tx.get("uploadType", "").upper() == "MULTIPART" or tx.get("parts"):
        done = []
        for part in tx["parts"]:
            chunk = raw[part["startByte"]:part["endByte"]]
            h = base64.b64encode(hashlib.sha256(chunk).digest()).decode()
            r = requests.put(part["presignedUrl"], data=chunk, headers={"x-amz-checksum-sha256": h}, timeout=600)
            if r.status_code >= 300:
                r = requests.put(part["presignedUrl"], data=chunk, timeout=600)
            if r.status_code >= 300:
                sys.exit(f"S3 part {part['partNumber']} failed {r.status_code}: {r.text[:300]}")
            done.append({"partNumber": part["partNumber"], "etag": r.headers.get("ETag")})
        fin = call("PATCH", "/v2/media/s3/upload-transactions",
                   json={"multipart": {"uploadId": tx["uploadId"], "key": tx["key"], "parts": done}})
    else:
        r = requests.put(tx["presignedUrl"], data=raw,
                         headers={"Content-Type": ctype, "x-amz-checksum-sha256": parts[0]["hash"]}, timeout=600)
        if r.status_code >= 300:
            r = requests.put(tx["presignedUrl"], data=raw, headers={"Content-Type": ctype}, timeout=600)
        if r.status_code >= 300:
            sys.exit(f"S3 upload failed {r.status_code}: {r.text[:300]}")
        url = tx.get("fileUrl") or tx["presignedUrl"].split("?")[0]
        fin = call("PATCH", "/v2/media/s3/upload-transactions", json={"simple": {"fileUrl": url}})
    fin = data(fin)
    return fin.get("convertedFileUrl") or fin["fileUrl"]


def when(s):
    return s or (dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:00")


def draft(a):
    video = a.video if a.video.startswith("http") else upload(a.video)
    cover = a.cover if (not a.cover or a.cover.startswith("http")) else upload(a.cover)
    body = {
        "text": pathlib.Path(a.caption).read_text(encoding="utf-8").strip(),
        "providers": [{"network": "instagram"}],
        "publicationDate": {"dateTime": when(a.when), "timezone": CFG["timezone"]},
        "media": [video],
        "draft": True,
        "autoPublish": False,
        "instagramData": {"type": TRIAL_TYPE, "shareTrialAutomatically": False, "autoPublish": False},
    }
    if cover:
        body["videoThumbnailUrl"] = cover
    if a.first_comment:
        body["firstCommentText"] = a.first_comment
    post = data(call("POST", "/v2/scheduler/posts", json=body))
    print(json.dumps({"id": post.get("id"), "uuid": post.get("uuid"), "video": video, "cover": cover,
                      "instagramData": post.get("instagramData"), "draft": post.get("draft")}, indent=1))


def get(pid):
    return data(call("GET", f"/v2/scheduler/posts/{pid}"))


def publish(a):
    post = get(a.id)
    post["draft"] = False
    post["autoPublish"] = True
    post.setdefault("instagramData", {})
    post["instagramData"].update({"autoPublish": True, "shareTrialAutomatically": False})
    t = a.when or (dt.datetime.now() + dt.timedelta(minutes=3)).strftime("%Y-%m-%dT%H:%M:00")
    post["publicationDate"] = {"dateTime": t, "timezone": CFG["timezone"]}
    res = data(call("PUT", f"/v2/scheduler/posts/{a.id}", json=post))
    print(json.dumps({"id": a.id, "publicationDate": res.get("publicationDate"), "providers": res.get("providers")}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("profiles")
    u = sub.add_parser("upload"); u.add_argument("file")
    d = sub.add_parser("draft")
    d.add_argument("--video", required=True); d.add_argument("--cover")
    d.add_argument("--caption", required=True); d.add_argument("--when")
    d.add_argument("--first-comment")
    g = sub.add_parser("get"); g.add_argument("id")
    p = sub.add_parser("publish"); p.add_argument("id"); p.add_argument("--when")
    s = sub.add_parser("status"); s.add_argument("id")
    a = ap.parse_args()
    if a.cmd == "profiles":
        r = requests.get(API + "/admin/simpleProfiles", headers=H, params={"userId": Q["userId"]}, timeout=60)
        print(r.status_code, json.dumps([{k: x.get(k) for k in ("id", "label", "instagram")} for x in data(r.json())]
                                         if r.ok else r.text[:500], indent=1))
    elif a.cmd == "upload":
        print(upload(a.file))
    elif a.cmd == "draft":
        draft(a)
    elif a.cmd == "get":
        print(json.dumps(get(a.id), indent=1, ensure_ascii=False))
    elif a.cmd == "publish":
        publish(a)
    elif a.cmd == "status":
        post = get(a.id)
        print(json.dumps({"draft": post.get("draft"), "providers": post.get("providers")}, indent=1))


if __name__ == "__main__":
    main()
