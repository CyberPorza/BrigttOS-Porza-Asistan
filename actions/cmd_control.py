import subprocess
import sys
import json
import re
from pathlib import Path
import shlex

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]

def _get_platform() -> str:
    if sys.platform == "win32":  return "windows"
    if sys.platform == "darwin": return "macos"
    return "linux"

# CyberPorza'nın sık kullandığı, onaya gerek duymadan çalışabilecek zararsız/sabit komutlar
WIN_COMMAND_MAP = [
    (["disk space", "disk usage", "storage"], "wmic logicaldisk get caption,freespace,size /format:list" if _get_platform() == "windows" else "df -h"),
    (["running processes", "list processes", "tasklist"], "tasklist /fo table" if _get_platform() == "windows" else "top -b -n 1"),
    (["ip address", "my ip", "ipconfig"], "ipconfig /all" if _get_platform() == "windows" else "ifconfig"),
    (["ping google", "check internet"], "ping -n 4 google.com" if _get_platform() == "windows" else "ping -c 4 google.com")
]

def _find_hardcoded(task: str) -> str | None:
    task_lower = task.lower()
    for keywords, command in WIN_COMMAND_MAP:
        if command and any(kw in task_lower for kw in keywords):
            return command
    return None

# Kesinlikle engellenmesi gereken ölümcül komutlar (Ne olursa olsun çalışmaz)
BLOCKED_PATTERNS = [
    r"\brm\s+-rf\b", r"\brmdir\s+/s\b", r"\bdel\s+/[fqs]",
    r"\bformat\b", r"\bdiskpart\b", r"\bfdisk\b",
    r"\breg\s+(delete|add)\b", r"\bbcdedit\b",
]
_BLOCKED_RE = re.compile("|".join(BLOCKED_PATTERNS), re.IGNORECASE)

def _is_safe(command: str) -> tuple[bool, str]:
    match = _BLOCKED_RE.search(command)
    if match:
        return False, f"Blocked pattern: '{match.group()}'"
    return True, "OK"

def _ask_gemini(task: str) -> str:
    try:
        import google.generativeai as genai
        genai.configure(api_key=_get_api_key())
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        prompt = (
            f"Convert this request to a single command for {_get_platform()}.\n"
            f"Output ONLY the command. No explanation, no markdown.\n"
            f"If unsafe or impossible, output: UNSAFE\n\n"
            f"Request: {task}\n\nCommand:"
        )
        response = model.generate_content(prompt)
        command  = response.text.strip().strip("`").strip()
        if command.startswith("```"):
            lines   = command.split("\n")
            command = "\n".join(lines[1:-1]).strip()
        return command
    except Exception as e:
        return f"ERROR: {e}"

def _run_silent(command: str, timeout: int = 20) -> str:
    try:
        platform = _get_platform()
        # Zafiyeti önlemek için komutu parçalıyoruz
        cmd_args = shlex.split(command) 
        
        if platform == "windows":
            result = subprocess.run(
                ["cmd", "/c"] + cmd_args,
                capture_output=True, text=True,
                encoding="cp1252", errors="replace",
                timeout=timeout, cwd=str(Path.home())
            )
        else:
            result = subprocess.run(
                cmd_args,
                capture_output=True, text=True,
                errors="replace", timeout=timeout,
                cwd=str(Path.home())
            )

        output = result.stdout.strip()
        error  = result.stderr.strip()
        if output:  return output[:2000]
        if error:   return f"[stderr]: {error[:500]}"
        return "Komut çıktısı yok."

    except subprocess.TimeoutExpired:
        return f"Komut zaman aşımına uğradı ({timeout}s)."
    except Exception as e:
        return f"Çalıştırma hatası: {e}"

def cmd_control(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None
) -> str:
    task    = (parameters or {}).get("task", "").strip()
    command = (parameters or {}).get("command", "").strip()

    if not task and not command:
        return "Ne yapmak istediğinizi belirtin."

    if not command:
        command = _find_hardcoded(task)
        if command:
            if player: player.write_log(f"SYS: Sabit komut bulundu: {command[:50]}")
        else:
            if player: player.write_log(f"SYS: '{task}' için komut üretiliyor...")
            command = _ask_gemini(task)
            
            if command == "UNSAFE":
                return "Bu işlem için güvenli bir komut üretemiyorum."
            if command.startswith("ERROR:"):
                return f"Komut üretilemedi: {command}"

    # Ölümcül komut kontrolü
    safe, reason = _is_safe(command)
    if not safe:
        return f"Güvenlik ihlali engellendi: {reason}"

    # === ONAY MEKANİZMASI (APPROVAL WALL) ===
    # Yapay zekanın ürettiği komutu çalıştırmadan önce log ekranına yaz ve dur.
    if player:
        player.write_log(f"CYBER_OPS: Üretilen Komut -> {command}")
        player.write_log("CYBER_OPS: Lütfen onaylamak için komutu terminale kopyalayın veya kendiniz çalıştırın.")
    
    # Not: Gerçek bir 'E/H' bekleme döngüsü asenkron yapıyı kilitleyebilir. 
    # En güvenli yöntem, asistanın sadece komutu "yazması" ve çalıştırmayı sana bırakmasıdır.
    return f"Komut üretildi ve log paneline yazıldı: {command}. Güvenlik gereği doğrudan çalıştırılmadı."