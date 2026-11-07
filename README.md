# La Police Municipale : site de révision

Site statique (HTML, CSS, JavaScript) publié avec GitHub Pages : https://altar037-ux.github.io/

Site de révision non officiel. Les textes de référence sont ceux de Légifrance.

## Structure

| Fichier ou dossier | Rôle |
|---|---|
| `index.html` | Page principale : toutes les rubriques (accueil, Apprendre, S’entraîner, Explorer, Mes outils, mentions légales) |
| `style.css` | Styles de la page principale |
| `app.js` | Logique de la page principale : navigation, quiz, recherche, notes, favoris |
| `data/communes.js` | Données des communes et des effectifs (chargé seulement pour la carte et la recherche de commune) |
| `vendor/leaflet.js` | Bibliothèque de carte Leaflet 1.9.4 (chargée seulement sur la rubrique Carte) |
| `fonts/` | Polices Atkinson Hyperlegible et Bricolage Grotesque (licence SIL OFL 1.1) |
| `images/` | Illustrations et images du site (`hero-ville.svg` pour l’accueil) |
| `concours-gardien-brigadier/`, `pouvoirs-police-maire/` | Pages autonomes, une par sujet |
| `nouveautes/` | Historique des mises à jour, lié depuis le pied de page |
| `revision-police-municipale/` | Ancienne adresse, redirige vers l’accueil |
| `sitemap.xml`, `robots.txt` | Pour les moteurs de recherche |
| `scripts/verifier_site.py` | Vérification automatique du site (voir plus bas) |
| `.github/workflows/verifier-site.yml` | Lance la vérification chaque lundi à 06 h UTC |

## Mettre à jour le contenu

1. Modifier la rubrique concernée dans `index.html` (ou la page autonome correspondante).
2. Mettre à jour la date « Mis à jour le … » dans le pied de page de `index.html`.
3. Ajouter une entrée datée dans `nouveautes/index.html`.
4. Mettre à jour `<lastmod>` dans `sitemap.xml` pour les pages modifiées.
5. Vérifier sur téléphone (largeur 390 px) : pas de défilement horizontal, rubriques lisibles.

## Publier

Le site est publié depuis la branche `main`. Un commit sur `main` est en ligne après une à deux minutes. Pas besoin d’étape de compilation.

## Vérification automatique

```
python3 scripts/verifier_site.py
python3 scripts/verifier_site.py --json rapport.json
```

Le script contrôle les données des communes (année la plus récente), les pages du sitemap, les dates à revoir et les liens externes. Le workflow GitHub Actions le lance chaque semaine. Consulter son rapport dans l’onglet **Actions** du dépôt. Un lien signalé comme « non testé » n’est pas forcément cassé : cela peut être une erreur de connexion temporaire.

## Règles pour les photos

- Chaque photo doit avoir une source et une licence qui autorisent la publication (licence libre ou photo propre).
- Ajouter une légende visible sous la photo, et le crédit dans la rubrique « Crédits photos » des mentions légales.
- Ne jamais publier une image filigranée, ni retirer un filigrane.

## Référencement

- Google Search Console : sitemap à soumettre pour le domaine `altar037-ux.github.io`. Le fichier de vérification `googledb80f1c3098b3f11.html` est à la racine.
- Bing Webmaster Tools : même démarche, facultative.

## Échéances à surveiller

- Chaque année : conditions et calendrier des concours de gardien-brigadier (CNFPT, centres de gestion).
- Chaque année : effectifs par commune, à comparer avec la dernière édition du jeu data.gouv « Police municipale : effectifs par commune ».
- À chaque changement de texte de loi : vérifier les liens Légifrance cités.
