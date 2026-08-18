---
name: nexpresso
description: >
  Pilotage du CMS Nexpresso (headless CMS de l'utilisateur, piloté par son serveur MCP :
  tools posts_*, projects_*, reviews_*, faqs_*, categories_*, tags_*, media_*,
  settings_*). Utilise ce skill dès qu'il s'agit de lire, rédiger, corriger, publier
  ou dépublier du contenu du CMS : « écris un article sur … », « publie ce post »,
  « passe ce projet en ligne », « mets à jour la FAQ », « ajoute cet avis client »,
  « change le logo du site », « liste mes brouillons », « quels articles sont publiés ».
  Le skill impose deux règles : tout contenu produit est d'abord créé en brouillon puis
  relu et validé, et l'utilisateur choisit lui-même entre garder le brouillon ou publier.
  Ne pas utiliser pour modifier le code du dépôt Nexpresso (c'est du développement
  applicatif, pas du pilotage de contenu).
---

# Nexpresso — pilotage du CMS par MCP

## Règles inviolables

**1. Rien n'est publié sans validation.** Tout contenu produit est créé en `status: "draft"`, relu par toi via la checklist ci-dessous, puis présenté à l'utilisateur (récapitulatif des champs). Seul un accord explicite de l'utilisateur déclenche le passage en `published`.

**2. Toujours demander ce que l'utilisateur veut du contenu produit.** À la fin de chaque production, poser la question avec `AskUserQuestion`, deux options : « Garder en brouillon » / « Publier maintenant ». Ne jamais deviner, ne jamais publier « par défaut ».

Un hook du plugin force de toute façon un prompt de confirmation sur `status: "published"` et sur tout `*_delete` : si ce prompt apparaît sans qu'on ait posé la question, c'est une règle enfreinte.

## Étape 0 — accès MCP

Avant toute chose, vérifier que les tools `mcp__…nexpresso…__*_list` sont exposés.

S'ils sont absents (serveur non branché, token OAuth expiré, scope manquant) : **le dire à l'utilisateur et s'arrêter**.

Interdits explicites, alignés sur l'`AGENTS.md` du dépôt Nexpresso :

- pas d'accès PocketBase admin ;
- pas de `curl` sur l'API PocketBase ;
- pas de `bun -e` ni d'exécution de script du dépôt ;
- pas d'écriture en base par un autre chemin que le MCP.

Un tool d'écriture manquant = **scope OAuth manquant**, à signaler à l'utilisateur — jamais une invitation à contourner.

## Cycle de travail

| Étape | Action |
|---|---|
| 1. Contexte | `settings_get` si le ton/nom du site compte ; `categories_list` / `tags_list` avant d'inventer une taxonomie ; `posts_list` avec `filter` pour vérifier qu'un slug n'existe pas déjà |
| 2. Production | rédiger le contenu ; `content` en **HTML** (`<h2>`, `<p>`, `<ul>`, `<a>`) — jamais de markdown |
| 3. Création | un seul appel `*_create` avec `status: "draft"` (jamais `published` à la création), `categories` / `tags` passés en slugs ou noms dans le même appel |
| 4. Relecture | `*_get` sur l'id créé, puis dérouler la checklist de validation |
| 5. Récapitulatif | présenter à l'utilisateur : titre, slug, extrait, catégories/tags, média de couverture, SEO, statut actuel |
| 6. Décision | `AskUserQuestion` : « Garder en brouillon » / « Publier maintenant » |
| 7. Publication | seulement si l'utilisateur a choisi de publier : `*_update` avec `status: "published"` (laisser `published_at` vide, il est rempli automatiquement) ; confirmer le prompt de permission |

## Checklist de validation

À dérouler à l'étape 4, **avant** tout récapitulatif.

| Vérification | Comment |
|---|---|
| Champs requis non vides | post : `title`, `slug`, `content` ; projet : `title`, `slug`, `description`, `link` ; avis : `author_name`, `rating` 1–5, `text`, `reviewed_at` ; FAQ : `question`, `answer`, `sort_order` |
| Slug conforme et libre | `^[a-z0-9-]+$` ; `posts_list` avec `filter: 'slug="mon-slug"'` doit ne rien renvoyer d'autre que l'enregistrement courant |
| `content` en HTML | pas de `#`, `**`, `- ` bruts dans le rendu |
| Longueurs | `excerpt` ≤ 1000, `seo_title` ≤ 160, `seo_description` ≤ 300, `description` de projet ≤ 500 |
| SEO renseigné | `seo_title` et `seo_description` remplis (sinon le proposer à l'utilisateur avant publication) |
| Couverture | `cover_image` = **id média** existant, jamais une URL |
| Médias | `alt_text` non vide sur chaque média créé (accessibilité + SEO, non négociable) |
| Taxonomie | `categories_list` / `tags_list` après création : aucun doublon créé par la résolution automatique |

## Médias

- **Fichier local** : `media_upload_ticket`, puis exécuter le `curl` renvoyé — `curl -sS -F "file=@/chemin" -F "title=…" "<upload_url>"`. TTL 5 minutes, usage unique.
- **Image distante** : `media_create` avec `source_url`.
- **`file_base64`** : dernier recours seulement (coûteux en tokens).

Réutiliser l'`id` du média créé comme `cover_image` / `site_logo` / `site_favicon` / `author_avatar`.

## Champs et comportements

Lire `${CLAUDE_PLUGIN_ROOT}/skills/nexpresso/reference.md` **avant** toute écriture : catalogue des champs par collection, limites de longueur et comportements transverses (PATCH partiel, `published_at` automatique, ids média).
