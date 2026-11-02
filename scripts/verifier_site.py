#!/usr/bin/env python3
"""Vérifie que La Police Municipale est à jour.

Contrôles :
  1. Liens externes : statut HTTP de chaque lien (Légifrance, service-public, etc.).
     Un 403/429 de Légifrance est signalé « à vérifier à la main » : le site bloque souvent les robots.
  2. Dates affichées : « Mis à jour le … » / « Dernière mise à jour : … » trop anciennes ou dans le futur.
  3. Données communes (data/communes.js) : année la plus récente des chiffres d'effectifs.
  4. Sitemap : chaque page listée répond bien.

Usage (depuis la racine du dépôt) :
  python3 scripts/verifier_site.py              # tout vérifier
  python3 scripts/verifier_site.py --no-liens   # sans les liens (rapide, hors ligne)
  python3 scripts/verifier_site.py --json rapport.json

Le script ne modifie rien. Il renvoie le code 1 s'il trouve un problème.
Aucune donnée personnelle n'est envoyée : seules les URL publiques du site sont interrogées.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

RACINE = pathlib.Path(__file__).resolve().parent.parent
INDEX = RACINE / "index.html"
COMMUNES = RACINE / "data" / "communes.js"
SITEMAP = RACINE / "sitemap.xml"
UA = "Mozilla/5.0 (verifier-site La Police Municipale)"
MOIS = {m: i for i, m in enumerate(
    ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
     "septembre", "octobre", "novembre", "décembre"], start=1)}
SEUIL_DATE_MOIS = 12  # une date « mise à jour » de plus de 12 mois est signalée
SEUIL_DONNEES_ANS = 2  # des effectifs de plus de 2 ans sont signalés


def statut_url(url, timeout=15):
    """Renvoie (code HTTP, message). Essaie HEAD puis GET si le serveur refuse HEAD."""
    for methode in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=methode, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, "ok"
        except urllib.error.HTTPError as e:
            if methode == "HEAD":
                continue  # certains serveurs refusent HEAD : on retente en GET
            return e.code, e.reason
        except Exception as e:  # réseau, TLS, délai
            if methode == "HEAD":
                continue
            return None, type(e).__name__
    return None, "inconnu"


def liens_externes(html):
    urls = set(re.findall(r'https?://[^\s"\'<>)]+', html))
    garder = []
    for u in sorted(urls):
        if "{" in u or "localhost" in u or "127.0.0.1" in u:
            continue  # modèles de tuiles, adresses locales
        if u.endswith("LEGIARTI") or u.endswith("destination=") or u.endswith("=2"):
            continue  # débuts d'URL construites par le code, pas des liens fixes
        if u.startswith("http://www.w3.org") or u.startswith("https://schema.org"):
            continue  # identifiants de namespace, pas des liens à suivre
        garder.append(u)
    return garder


def verifier_liens(urls):
    """Renvoie (liens cassés, liens à vérifier à la main, liens non testés à cause du réseau)."""
    cassés, a_verifier, reseau = [], [], []
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        for u, (code, msg) in zip(urls, pool.map(statut_url, urls)):
            if code is not None and 200 <= code < 400:
                continue
            ligne = {"url": u, "code": code, "message": msg}
            if code is None:
                # Erreur de connexion : pas une preuve que le lien est cassé.
                # Légifrance bloque souvent les robots : à vérifier à la main.
                (a_verifier if "legifrance" in u else reseau).append(ligne)
            elif code in (401, 403, 429) and "legifrance" in u:
                a_verifier.append(ligne)
            else:
                cassés.append(ligne)
    return cassés, a_verifier, reseau


def verifier_dates(html):
    aujourd_hui = dt.date.today()
    problemes = []
    motif = re.compile(r"(?:Mis à jour le|Dernière mise à jour\s*:)\s*(\d{1,2})\s+([a-zéû]+)\s+(\d{4})", re.I)
    for m in motif.finditer(html):
        jour, mois_txt, annee = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        if mois_txt not in MOIS:
            continue
        d = dt.date(annee, MOIS[mois_txt], jour)
        age_mois = (aujourd_hui.year - d.year) * 12 + (aujourd_hui.month - d.month)
        if d > aujourd_hui:
            problemes.append({"date": str(d), "message": "date dans le futur"})
        elif age_mois > SEUIL_DATE_MOIS:
            problemes.append({"date": str(d), "message": f"il y a {age_mois} mois : à revoir"})
    return problemes


def verifier_donnees():
    if not COMMUNES.exists():
        return [{"message": "data/communes.js introuvable"}]
    texte = COMMUNES.read_text(encoding="utf-8", errors="replace")
    annees = [int(a) for a in re.findall(r"\b(20[0-3]\d)\b", texte)]
    if not annees:
        return [{"message": "aucune année trouvée dans les données communes"}]
    recente = max(annees)
    age = aujourd_hui_annee() - recente
    if age > SEUIL_DONNEES_ANS:
        return [{"message": f"année la plus récente des données : {recente} ; mettre à jour"}]
    return []


def aujourd_hui_annee():
    return dt.date.today().year


def verifier_sitemap():
    if not SITEMAP.exists():
        return [], []
    urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", SITEMAP.read_text(encoding="utf-8"))
    cassés, _, reseau = verifier_liens(urls)
    return cassés, reseau


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--no-liens", action="store_true", help="ne pas tester les liens (hors ligne)")
    p.add_argument("--json", metavar="FICHIER", help="écrire le rapport en JSON")
    args = p.parse_args()

    html = INDEX.read_text(encoding="utf-8")
    rapport = {"date": str(dt.date.today()), "liens_cassés": [], "liens_à_vérifier": [],
               "liens_non_testés_réseau": [], "dates": [], "données": [], "sitemap_cassé": []}

    if not args.no_liens:
        rapport["liens_cassés"], rapport["liens_à_vérifier"], rapport["liens_non_testés_réseau"] = \
            verifier_liens(liens_externes(html))
        rapport["sitemap_cassé"], _ = verifier_sitemap()
    rapport["dates"] = verifier_dates(html)
    rapport["données"] = verifier_donnees()

    print(f"Vérification du {rapport['date']}")
    sections = [
        ("Liens cassés (erreur HTTP)", rapport["liens_cassés"],
         lambda x: f"{x['code']} {x['message']} : {x['url']}"),
        ("Liens à vérifier à la main (Légifrance bloque souvent les robots)", rapport["liens_à_vérifier"],
         lambda x: f"{x['code'] or 'réseau'} {x['message']} : {x['url']}"),
        ("Liens non testés (erreur de connexion, pas une preuve de panne)", rapport["liens_non_testés_réseau"],
         lambda x: f"{x['message']} : {x['url']}"),
        ("Pages du sitemap en erreur", rapport["sitemap_cassé"], lambda x: f"{x['code']} : {x['url']}"),
        ("Dates à revoir", rapport["dates"], lambda x: f"{x['date']} – {x['message']}"),
        ("Données", rapport["données"], lambda x: x["message"]),
    ]
    for titre, items, fmt in sections:
        print(f"\n{titre} : {len(items)}")
        for it in items[:200]:
            print("  - " + fmt(it))
    if args.no_liens:
        print("\n(liens non testés : option --no-liens)")

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nRapport JSON : {args.json}")

    bloquant = rapport["liens_cassés"] or rapport["sitemap_cassé"] or rapport["dates"] or rapport["données"]
    return 1 if bloquant else 0


if __name__ == "__main__":
    sys.exit(main())
