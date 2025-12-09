# modules/file_utils.py
# -*- coding: utf-8 -*-
"""
File utils extraídos do OficialDeep5.3.py
Mantém IO functions exatamente como no código principal.
"""

import os
import json
import pickle
import tempfile
import shutil

# ------------------------
# Save JSON 
# ------------------------
def save_json(path, data, indent=4):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        print(f"[save_json] Erro salvando {path}: {e}")
        return False

# ------------------------
# Load JSON
# ------------------------
def load_json(path, default=None):
    try:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[load_json] Erro lendo {path}: {e}")
        return default

# ------------------------
# Save Pickle (with atomic save)
# ------------------------
def save_pickle(path, obj):
    try:
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
        shutil.move(tmp, path)
        return True
    except Exception as e:
        print(f"[save_pickle] Erro salvando {path}: {e}")
        return False

# ------------------------
# Load Pickle
# ------------------------
def load_pickle(path, default=None):
    try:
        if not os.path.exists(path):
            return default
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"[load_pickle] Erro lendo {path}: {e}")
        return default

# ------------------------
# Atomic Save for any file
# ------------------------
def atomic_save(path, data_bytes):
    """
    Salva bytes atomica e seguramente.
    """
    try:
        d = os.path.dirname(path)
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d)
        os.close(fd)

        with open(tmp, "wb") as f:
            f.write(data_bytes)

        shutil.move(tmp, path)
        return True

    except Exception as e:
        print(f"[atomic_save] Erro salvando {path}: {e}")
        return False


__all__ = [
    "save_json", "load_json",
    "save_pickle", "load_pickle",
    "atomic_save"
]
