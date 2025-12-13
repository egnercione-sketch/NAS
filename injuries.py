# injuries.py — OFF RADAR v44.1
# Módulo híbrido de lesões (ESPN JSON-first + cache + normalização)
import os
import json
import time
from datetime import datetime, timedelta
import requests

# Ajuste conforme seu projeto
BASE_DIR = os.path.dirname(__file__)
CACHE_DIR = os.path.join(BASE_DIR, "..", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

INJURIES_CACHE_FILE = os.path.join(CACHE_DIR, "injuries_cache_v44.json")
CACHE_TTL_HOURS = 3
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Usa o mesmo normalizador do seu pipeline
def normalize_name(n: str) -> str:
    import re, unicodedata
    if not n:
        return ""
    n = str(n).lower()
    n = n.replace(".", " ").replace(",", " ").replace("-", " ")
    n = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", n)
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode("ascii")
    n = " ".join(n.split())
    return n

def save_json(path, obj):
    try:
        data = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        with open(path, "wb") as f:
            f.write(data)
        return True
    except Exception:
        return False

def load_json(path):
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

class InjuryMonitor:
    """
    InjuryMonitor v44.1
    - Fonte principal: ESPN roster JSON (sem scraping HTML)
    - Cache consolidado por time
    - Normalização de nomes para casar com L5
    - APIs:
        - fetch_injuries_for_team(team_abbr)
        - fetch_all_injuries_for_games(games)
        - is_player_out(player_name, team_abbr)
        - get_team_injuries(team_abbr)
        - get_all_injuries()
    """

    def __init__(self, cache_file: str = INJURIES_CACHE_FILE, ttl_hours: int = CACHE_TTL_HOURS):
        self.cache_file = cache_file
        self.ttl_hours = ttl_hours
        self.cache = load_json(self.cache_file) or {
            "last_updated": None,
            "teams": {},        # {"GSW": [{"name":..., "status":..., "details":..., "date":...}], ...}
            "source": "ESPN",
            "version": "v44.1"
        }

    # ESPN roster endpoint (usa o mesmo template que seu pipeline v44)
    def _espn_roster_url(self, team_abbr: str) -> str:
        return f"https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_abbr}/roster"

    def _fetch_team_roster_raw(self, team_abbr: str) -> dict:
        try:
            r = requests.get(self._espn_roster_url(team_abbr), headers=HEADERS, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return {}

    def _parse_injuries_from_roster(self, roster_json: dict) -> list:
        injuries = []
        athletes = roster_json.get("athletes") or roster_json.get("entries") or roster_json.get("players") or []
        for athlete in athletes:
            # ESPN estrutura típica
            name = athlete.get("displayName") or athlete.get("fullName") or athlete.get("name")
            status_obj = athlete.get("status") or athlete.get("injuryStatus")
            # Detalhes reais de lesão costumam estar em 'injuries'
            inj_list = athlete.get("injuries", [])

            # Se há 'injuries', colher entrada detalhada
            if inj_list:
                for inj in inj_list:
                    injuries.append({
                        "name": name or "",
                        "status": inj.get("status", status_obj.get("name") if isinstance(status_obj, dict) else "Active"),
                        "details": inj.get("description", ""),  # pode não existir
                        "date": inj.get("date", "")
                    })
            else:
                # Sem 'injuries' → registrar status genérico (Active) para consistência
                status_name = status_obj.get("name") if isinstance(status_obj, dict) else (status_obj or "Active")
                injuries.append({
                    "name": name or "",
                    "status": status_name or "Active",
                    "details": "",
                    "date": ""
                })
        return injuries

    def _is_cache_fresh(self) -> bool:
        lu = self.cache.get("last_updated")
        if not lu:
            return False
        try:
            last_dt = datetime.fromisoformat(lu)
            return datetime.now() - last_dt < timedelta(hours=self.ttl_hours)
        except Exception:
            return False

    def save_cache(self):
        self.cache["last_updated"] = datetime.now().isoformat()
        save_json(self.cache_file, self.cache)

    def fetch_injuries_for_team(self, team_abbr: str) -> list:
        """
        Busca e atualiza as lesões de um time. Sempre normaliza o nome.
        Retorna lista de dicts: [{"name", "name_norm", "status", "details", "date"}...]
        """
        raw = self._fetch_team_roster_raw(team_abbr)
        if not raw:
            # fallback para cache existente
            return self.cache.get("teams", {}).get(team_abbr, [])

        parsed = self._parse_injuries_from_roster(raw)

        # Normalização + filtragem básica
        normalized = []
        for item in parsed:
            name = item.get("name", "")
            status = (item.get("status") or "").strip()
            details = (item.get("details") or "").strip()
            date = item.get("date") or ""

            normalized.append({
                "name": name,
                "name_norm": normalize_name(name),
                "status": status,         # "Out", "Questionable", "Active", ...
                "details": details,
                "date": date
            })

        # Atualiza cache
        if "teams" not in self.cache:
            self.cache["teams"] = {}
        self.cache["teams"][team_abbr] = normalized
        self.save_cache()
        return normalized

    def fetch_all_injuries_for_games(self, games: list) -> dict:
        """
        Recebe lista de jogos (scoreboard v44) e atualiza lesões de todos os times envolvidos.
        Retorna map {"ABBR": [injuries...], ...}
        """
        teams = set()
        for g in games or []:
            away = g.get("away")
            home = g.get("home")
            if away: teams.add(away)
            if home: teams.add(home)

        result = {}
        for abbr in teams:
            result[abbr] = self.fetch_injuries_for_team(abbr)
            time.sleep(0.4)  # rate-limit leve, evita bloqueio

        return result

    def get_team_injuries(self, team_abbr: str) -> list:
        """
        Retorna lista de lesões do time do cache, atualizando se cache não está fresco.
        """
        if not self._is_cache_fresh():
            # tenta atualizar este time antes de retornar
            self.fetch_injuries_for_team(team_abbr)
        return self.cache.get("teams", {}).get(team_abbr, [])

    def get_all_injuries(self) -> dict:
        """
        Retorna o cache completo. Se não fresco, retorna mesmo assim (design: não travar UI).
        """
        return self.cache.get("teams", {})

    def is_player_out(self, player_name: str, team_abbr: str) -> bool:
        """
        Checa se jogador está "Out" (ou equivalente) no time.
        Usa nome normalizado para comparação.
        """
        name_norm = normalize_name(player_name)
        team_list = self.get_team_injuries(team_abbr)
        for item in team_list:
            if item.get("name_norm") == name_norm:
                status = (item.get("status") or "").lower()
                if "out" in status:  # Out, Out indefinitely, Out (rest), etc.
                    return True
                if "questionable" in status:  # você pode tratar como "não elegível"
                    return True
        return False