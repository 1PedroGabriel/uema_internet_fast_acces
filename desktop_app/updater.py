"""
Verificação de atualizações via API pública do GitHub Releases.

Permite que usuários saibam quando há correções de segurança ou melhorias,
sem precisar monitorar o repositório manualmente. A checagem é apenas de
leitura (GET na API) e não baixa nem instala nada automaticamente.
"""
import json
import os
import re
import sys
import requests
from logger import setup_logger

logger = setup_logger()

GITHUB_REPO = "1PedroGabriel/uema_internet_fast_acces"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases/latest"


def _parse_version(tag):
    """Extrai tupla numérica de uma tag como 'v1.2.3' -> (1, 2, 3)."""
    match = re.findall(r'\d+', tag or '')
    return tuple(int(n) for n in match[:3]) if match else (0,)


def get_current_version():
    """
    Lê a versão do arquivo version_info.json gravado ao lado do executável
    (gerado no CI a partir da tag). Em desenvolvimento, cai no fallback 1.0.0.
    """
    try:
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base, 'version_info.json'), 'r', encoding='utf-8') as f:
            return _parse_version(json.load(f).get('version', ''))
    except Exception:
        pass
    return (1, 0, 0)  # fallback de desenvolvimento


def check_for_update(current=None):
    """
    Consulta o release mais recente no GitHub.
    Retorna dict {available: bool, tag: str, url: str, notes: str} ou None em caso de erro.
    """
    current = current or get_current_version()
    try:
        resp = requests.get(RELEASES_API, timeout=8, headers={
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'UEMA-FastAccess-UpdateChecker'
        })
        if resp.status_code != 200:
            logger.debug(f"Checagem de atualização: HTTP {resp.status_code}")
            return None

        data = resp.json()
        latest_tag = data.get('tag_name', '')
        latest = _parse_version(latest_tag)

        return {
            'available': latest > current,
            'tag': latest_tag,
            'url': data.get('html_url', RELEASES_PAGE),
            'notes': (data.get('body') or '')[:500],
            'current': '.'.join(str(n) for n in current)
        }
    except Exception as e:
        logger.debug(f"Falha ao checar atualização: {e}")
        return None
