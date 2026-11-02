"""Check 2's runner: a time limit, a memory limit and no network, as far as an unprivileged process can.

This is best effort and not a security boundary. On Windows without admin rights there's no network
namespace, so "no network" is enforced inside the Python process by an audit hook, on top of a static
check on the source. It stops a model-written program from wandering off by accident. It won't stop a
program written by someone trying to escape, so only run drafts from this pipeline.
"""
import ast
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .config import SANDBOX_MEMORY_MB, SANDBOX_SECONDS

BOOT = Path(__file__).with_name("sandbox_boot.py")
# The sandbox imports sympy and numpy before the program starts. On a busy machine that alone takes many
# seconds, and it shouldn't count against the program's own limit.
STARTUP_ALLOWANCE = 30
ALLOWED_IMPORTS = {"sympy", "mpmath", "numpy", "math", "cmath", "fractions", "decimal", "itertools", "functools", "collections",
                   "heapq", "bisect", "operator", "statistics", "string", "re", "numbers", "typing", "dataclasses", "sys"}
BANNED_NAMES = {"exec", "eval", "compile", "open", "__import__", "input", "globals", "locals", "vars", "getattr", "setattr", "delattr", "breakpoint", "memoryview"}
NUMERIC_CASTS = {"print", "int", "str", "float", "Fraction", "Rational", "Integer", "abs", "round"}


def static_check(source):
    """Returns (reason, hard_coded). A reason means the program breaks the rules and must not run."""
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"syntax error: {e.msg} (line {e.lineno})", False
    computes = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    return f"import of {a.name} is not allowed", False
        elif isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                return f"import from {node.module} is not allowed", False
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            return f"{node.id} is not allowed", False
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return f"attribute {node.attr} is not allowed", False
        elif isinstance(node, (ast.For, ast.While, ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            computes = True
        elif isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            if name not in NUMERIC_CASTS:
                computes = True
    return None, not computes


def prints_literal(source, answer):
    """True if a print() is handed the answer as a bare literal, whatever decoys run around it."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "print":
            for a in node.args:
                if isinstance(a, ast.Constant) and str(a.value).strip() == str(answer).strip():
                    return True
    return False


@dataclass
class Run:
    ok: bool
    stdout: str = ""
    error: str = ""


def _limit_windows(proc):
    """Puts the child in a job with a memory limit, one process, and kill-on-close."""
    import ctypes
    from ctypes import wintypes as w

    class Basic(ctypes.Structure):
        _fields_ = [("a", ctypes.c_int64), ("b", ctypes.c_int64), ("LimitFlags", w.DWORD), ("MinWS", ctypes.c_size_t), ("MaxWS", ctypes.c_size_t),
                    ("ActiveProcessLimit", w.DWORD), ("Affinity", ctypes.c_size_t), ("Priority", w.DWORD), ("Sched", w.DWORD)]

    class Extended(ctypes.Structure):
        _fields_ = [("Basic", Basic), ("Io", ctypes.c_uint64 * 6), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcess", ctypes.c_size_t), ("PeakJob", ctypes.c_size_t)]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateJobObjectW.restype = w.HANDLE
    k32.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    k32.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    k32.CloseHandle.argtypes = [w.HANDLE]
    job = k32.CreateJobObjectW(None, None)
    info = Extended()
    info.Basic.LimitFlags = 0x2000 | 0x0100 | 0x0008  # kill on close, process memory, active process
    info.Basic.ActiveProcessLimit = 1
    info.ProcessMemoryLimit = SANDBOX_MEMORY_MB * 1024 * 1024
    k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
    k32.AssignProcessToJobObject(job, int(proc._handle))
    return lambda: k32.CloseHandle(job)


def _limit_posix():
    import resource
    mem = SANDBOX_MEMORY_MB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))


def run_program(source, seconds=None):
    seconds = SANDBOX_SECONDS if seconds is None else seconds
    with tempfile.TemporaryDirectory(prefix="cevian-sandbox-") as cwd:
        prog = Path(cwd) / "check_program.py"
        prog.write_text(source, encoding="utf-8")
        env = {k: os.environ[k] for k in ("SYSTEMROOT", "PATH", "TEMP", "TMP") if k in os.environ}
        env["PYTHONIOENCODING"] = "utf-8"
        kw = {} if os.name == "nt" else {"preexec_fn": _limit_posix}
        proc = subprocess.Popen([sys.executable, "-I", "-B", str(BOOT), str(prog)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.DEVNULL, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace", **kw)
        close_job = _limit_windows(proc) if os.name == "nt" else (lambda: None)
        try:
            out, err = proc.communicate(timeout=seconds + STARTUP_ALLOWANCE)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            return Run(False, error=f"timed out after {seconds:g}s")
        finally:
            close_job()
    if proc.returncode != 0:
        return Run(False, stdout=out[-2000:], error=err.strip().splitlines()[-1][:300] if err.strip() else f"exit code {proc.returncode}")
    return Run(True, stdout=out[-2000:])
