# gen_checksums.py
import hashlib, sys, pathlib

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

p = pathlib.Path(sys.argv[1])  # 파일 또는 디렉터리
out = p / "checksums.sha256.txt" if p.is_dir() else p.with_suffix(p.suffix + ".sha256.txt")

lines = []
if p.is_dir():
    for f in sorted(p.iterdir()):
        if f.is_file():
            lines.append(f"{sha256_of(f)}  {f.name}")
else:
    lines.append(f"{sha256_of(p)}  {p.name}")

out.write_text("\n".join(lines), encoding="utf-8")
print("Saved:", out)