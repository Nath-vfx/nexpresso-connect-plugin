# Nexpresso — champs et comportements par collection

Référence à lire avant toute écriture. Les tools visibles dépendent des scopes OAuth du jeton : un tool absent = scope manquant, à signaler à l'utilisateur.

## Posts

Tools : `posts_list`, `posts_get`, `posts_create`, `posts_update`, `posts_delete`.

| Champ | Contrainte |
|---|---|
| `title` | requis, ≤ 500 |
| `slug` | requis, ≤ 550, `^[a-z0-9-]+$` |
| `content` | requis, **HTML** (l'éditeur du dashboard est TipTap : le markdown brut s'afficherait littéralement) |
| `excerpt` | ≤ 1000 |
| `status` | `draft` \| `published` \| `archived`, défaut `draft` |
| `published_at` | rempli automatiquement au passage en `published` si vide |
| `author` | id utilisateur ; par défaut celui du jeton en HTTP |
| `categories[]`, `tags[]` | ids, slugs **ou** noms ; création automatique si absents (scopes `categories:write` / `tags:write`) — passer la taxonomie dans le même appel que `posts_create`, pas via `categories_create` séparé |
| `seo_title` | ≤ 160 |
| `seo_description` | ≤ 300 |
| `cover_image` | id d'un enregistrement `media` |

Expand disponible : `author.avatar_media,cover_image,categories,tags`. Tri par défaut : `-created`.

## Projects

`projects_list|get|create|update|delete`.

| Champ | Contrainte |
|---|---|
| `title` | requis |
| `slug` | requis, `^[a-z0-9-]+$` |
| `description` | requis, ≤ 500 |
| `link` | requis, `^https?://`, ≤ 2000 |
| `status` | `draft` \| `published` \| `archived`, défaut `draft` |
| `published_at` | auto au passage en `published` |
| `author` | id utilisateur |
| `cover_image` | id média |

## Reviews

`reviews_list|get|create|update|delete`.

| Champ | Contrainte |
|---|---|
| `author_name` | requis, ≤ 200 |
| `author_url` | vide ou `^https?://` |
| `author_avatar` | id média |
| `rating` | entier 1–5, requis |
| `text` | requis, ≤ 5000 |
| `language` | défaut `fr` |
| `reviewed_at` | requis |
| `response` | ≤ 5000 |
| `responded_at` | date |
| `status` | `draft` \| `published` \| `archived`, défaut `draft` |
| `featured` | booléen |

Tri par défaut : `-reviewed_at`.

## FAQs

`faqs_list|get|create|update|delete`. **Pas de `status`.**

| Champ | Contrainte |
|---|---|
| `question` | requis, ≤ 500 |
| `answer` | requis, ≤ 5000 |
| `sort_order` | entier ≥ 0 |

Tri par défaut : `sort_order`.

## Categories / Tags

- **Categories** (`categories_list|get|create|update|delete`) : `name` (≤ 100), `slug` (≤ 120), `description` (≤ 500), `cover_image` (id média).
- **Tags** (`tags_list|get|create|update|delete`) : `name`, `slug`.

## Media

`media_list`, `media_get`, `media_create`, `media_update`, `media_delete`, `media_upload_ticket`.

| Champ | Contrainte |
|---|---|
| `title` | ≤ 300 |
| `alt_text` | requis à l'édition, ≤ 500 |
| `caption` | ≤ 500 |
| `description` | ≤ 3000 |
| source | `source_url` **ou** `file_base64` + `filename` — exactement une des deux |

`media_upload_ticket` renvoie une commande `curl` : TTL 5 minutes, usage unique.

## Settings

Singleton : `settings_get`, `settings_update`.

| Champ | Contrainte |
|---|---|
| `site_name` | requis, ≤ 200 |
| `site_description` | ≤ 500 |
| `site_logo`, `site_favicon` | ids média |
| `twitter_url`, `github_url`, `facebook_url`, `instagram_url`, `linkedin_url` | vide ou `^https?://` |

## Users

`users_list`, `users_get` uniquement — **lecture seule**, exige le scope `users:read` et un rôle admin. Aucun tool d'écriture users n'existe : ne pas promettre de modification d'utilisateur.

## Comportements transverses

- `published_at` est auto-rempli au passage en `published` quand le champ est vide : ne pas le remplir à la main.
- Les `*_update` sont des **PATCH** : n'envoyer que les champs modifiés. Un champ omis n'est pas écrasé ; un champ envoyé vide l'écrase.
- `cover_image` / `site_logo` / `site_favicon` / `author_avatar` = **id d'un enregistrement `media`** ; chaîne vide ou `null` pour retirer. Jamais une URL.
- Les tools exposés dépendent des scopes OAuth du jeton.
- Ne jamais contourner le MCP (PocketBase admin, `curl` sur l'API PocketBase, `bun -e`, Server Actions) : si le MCP est indisponible ou le token expiré, le dire et s'arrêter.
