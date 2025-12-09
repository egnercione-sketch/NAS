# modules/utils_fix.py
"""
Arquivo temporário para resolver problemas de importação.
Contém todas as funções necessárias para outros módulos.
"""
import os
import pickle
import json
import tempfile
from datetime import datetime

# ============================================================================
# FUNÇÕES DE CACHE
# ============================================================================

def atomic_save(path, obj_bytes):
    """Salva arquivo atomicamente"""
    dirpath = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(fd, "wb") as f: f.write(obj_bytes)
        os.replace(tmp, path); return True
    except Exception:
        try:
            if os.path.exists(tmp): os.remove(tmp)
        except Exception: pass
        return False

def save_pickle(path, obj):
    """Salva objeto em arquivo pickle"""
    try:
        data = pickle.dumps(obj)
        return atomic_save(path, data)
    except Exception:
        return False

def load_pickle(path):
    """Carrega objeto de arquivo pickle"""
    try:
        if not os.path.exists(path): return None
        with open(path, "rb") as f: return pickle.load(f)
    except Exception:
        return None

def save_json(path, obj):
    """Salva objeto em arquivo JSON"""
    try:
        data = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        return atomic_save(path, data)
    except Exception:
        return False

def load_json(path):
    """Carrega objeto de arquivo JSON"""
    try:
        if not os.path.exists(path): return None
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except Exception:
        return None

# ============================================================================
# CLASSES UTILITÁRIAS
# ============================================================================

class SafetyUtils:
    @staticmethod
    def safe_get(data, keys, default=None):
        try:
            if isinstance(keys, str):
                keys = [keys]
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, list) and isinstance(key, int) and 0 <= key < len(current):
                    current = current[key]
                else:
                    return default
            return current if current is not None else default
        except:
            return default
    
    @staticmethod
    def safe_float(value, default=0.0):
        try:
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                cleaned = ''.join(c for c in value if c.isdigit() or c in '.-')
                return float(cleaned) if cleaned else default
            return float(value)
        except:
            return default

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def safe_get(dictionary, key, default=None):
    """Acesso seguro a dicionários com fallback"""
    return dictionary.get(key, default)

def normalize_name(n: str) -> str:
    """Normaliza nomes para comparação"""
    import re
    import unicodedata
    
    if not n: return ""
    n = str(n).lower()
    n = n.replace(".", " ").replace(",", " ").replace("-", " ")
    n = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", n)
    n = unicodedata.normalize("NFKD", n).encode("ascii","ignore").decode("ascii")
    return " ".join(n.split())

def safe_abs_spread(val):
    """Valor absoluto seguro"""
    if val is None: return 0.0
    try: return abs(float(val))
    except Exception: return 0.0

def _status_is_out_or_questionable(status: str) -> bool:
    """Verifica se status é out ou questionable"""
    s = (status or "").lower()
    return ("out" in s) or ("questionable" in s) or ("injur" in s) or ("ir" in s)