import json, pathlib, io, sys

BASE = pathlib.Path(r"C:\Users\<用户名>\.workbuddy\projects")
OUT = pathlib.Path(r"<实验根目录>\ab-cycle4-effectiveness\transcripts")
OUT.mkdir(parents=True, exist_ok=True)

SESSIONS = {
    "B1": "c-Users-<用户名>-Desktop-A4-Skills_None-A4-Skills_None1",
    "B2": "c-Users-<用户名>-Desktop-A4-Skills_None-A4-Skills_None2",
    "B3": "c-Users-<用户名>-Desktop-A4-Skills_None-A4-Skills_None3",
    "A1": "c-Users-<用户名>-Desktop-A4-Skills_Yes-A4-Skills_Yes_1",
    "A2": "c-Users-<用户名>-Desktop-A4-Skills_Yes-A4-Skills_Yes_2",
    "A3": "c-Users-<用户名>-Desktop-A4-Skills_Yes-A4-Skills_Yes_3",
}

def blocks_text(content):
    """Return (texts, tool_uses, tool_results) from a content field."""
    texts, tus, trs = [], [], []
    if isinstance(content, str):
        return [content], [], []
    if isinstance(content, list):
        for b in content:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t in ("text", "input_text", "output_text"):
                texts.append(b.get("text", ""))
            elif t in ("tool_use", "tool_call"):
                name = b.get("name", "?")
                inp = json.dumps(b.get("input", b.get("arguments", {})), ensure_ascii=False)[:200]
                tus.append(f"{name}({inp})")
            elif t in ("tool_result", "tool_output"):
                c = b.get("content", b.get("output", ""))
                if isinstance(c, list):
                    c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
                trs.append(str(c)[:200])
    return texts, tus, trs

for tag, proj in SESSIONS.items():
    files = sorted(BASE.joinpath(proj).glob("*.jsonl"))
    if not files:
        print(f"{tag}: NO JSONL"); continue
    src = files[0]
    out_path = OUT / f"{tag}-dump.txt"
    with io.open(out_path, "w", encoding="utf-8") as w:
        n_user = n_asst = 0
        for i, line in enumerate(src.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            try:
                rec = json.loads(line)
            except Exception:
                continue
            msg = rec.get("message") or rec
            role = msg.get("role") or rec.get("type", "?")
            rtype = rec.get("type", "")
            if rtype == "reasoning":
                rc = rec.get("rawContent") or []
                rt = " ".join(x.get("text", "") for x in rc if isinstance(x, dict))
                if rt.strip():
                    w.write(f"\n[{i}] REASONING({role}): {rt[:400]}\n")
                continue
            texts, tus, trs = blocks_text(msg.get("content"))
            joined = "\n".join(x for x in texts if x.strip())
            if role == "user":
                n_user += 1
                w.write(f"\n[{i}] USER: {joined[:600]}\n")
                if trs:
                    w.write(f"    (tool_result x{len(trs)}: {trs[0][:120]})\n")
            elif role == "assistant":
                n_asst += 1
                w.write(f"\n[{i}] ASSISTANT:\n")
                if joined:
                    w.write(joined[:900] + ("\n...[截断]" if len(joined) > 900 else "") + "\n")
                if tus:
                    for t in tus:
                        w.write(f"    TOOL> {t}\n")
        w.write(f"\n=== SUMMARY {tag}: user_msgs={n_user} asst_msgs={n_asst} src={src.name} size={src.stat().st_size}\n")
    print(f"{tag}: dumped -> {out_path} (user={n_user}, asst={n_asst})")
