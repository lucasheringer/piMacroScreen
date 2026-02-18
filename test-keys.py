python3 - <<'PY' >/dev/hidg0
import sys, time
mods = [1,2,4,8,16,32,64,128]
for m in mods:
    print(f"testing 0x{m:02x}", file=sys.stderr)
    sys.stdout.buffer.write(bytes([1, m, 0, 0x04, 0,0,0,0,0])); sys.stdout.buffer.flush()
    time.sleep(0.25)
    sys.stdout.buffer.write(bytes([1, 0, 0, 0,0,0,0,0,0])); sys.stdout.buffer.flush()
    time.sleep(2)
PY

python3 - <<'PY' >/dev/hidg0
import sys, time
sys.stdout.buffer.write(bytes([1, 0x0A, 0, 0x10, 0, 0, 0, 0, 0])); sys.stdout.buffer.flush()
time.sleep(0.25)
sys.stdout.buffer.write(bytes([1, 0, 0, 0,0,0,0,0,0])); sys.stdout.buffer.flush()
time.sleep(2)
PY