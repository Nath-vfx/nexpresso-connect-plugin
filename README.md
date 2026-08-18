# nexpresso-connect

Plugin Claude Code pour piloter le CMS **Nexpresso** via son serveur MCP : rédiger et mettre à jour posts, projets, avis, FAQ, catégories, tags, médias et réglages — sans jamais publier dans le dos de l'utilisateur.

Contenu du plugin :

- **skill `nexpresso`** — le mode d'emploi du CMS : cycle de travail, checklist de validation, catalogue des champs (`skills/nexpresso/reference.md`).
- **hook `PreToolUse`** — le garde-fou déterministe : `hooks/publish-gate.py`.

Pas d'agents, pas de commandes slash, pas de config MCP embarquée.

## Les deux règles

1. **Rien n'est publié sans validation.** Tout contenu produit est créé en `status: "draft"`, relu via la checklist du skill, puis présenté à l'utilisateur (récapitulatif des champs). Seul un accord explicite déclenche le passage en `published`.
2. **On demande toujours ce que l'utilisateur veut du contenu produit.** En fin de production, `AskUserQuestion` avec deux options : « Garder en brouillon » / « Publier maintenant ». Jamais de publication « par défaut ».

Le hook rend la règle 1 non contournable, même en auto mode.

## Prérequis : un serveur MCP Nexpresso branché

Le plugin **n'embarque pas** de configuration MCP. Il faut donc déjà avoir le serveur MCP de Nexpresso accessible depuis Claude Code, par l'une des deux voies documentées côté Nexpresso :

**(a) Connecteur distant (recommandé, OAuth)**
URL HTTPS publique de `/api/mcp` en Streamable HTTP + OAuth 2.1. `localhost` est impossible : la connexion part des serveurs Anthropic, l'instance doit être joignable depuis Internet.

**(b) Dev local (stdio)**
Dans le dépôt Nexpresso : `bun run mcp:stdio`, avec `POCKETBASE_URL`, `PB_ADMIN_EMAIL`, `PB_ADMIN_PASSWORD` dans l'environnement. À déclarer dans le `.mcp.json` du projet.

### Contrainte de nommage

La clé du serveur MCP **doit contenir « nexpresso »** (ex. `"nexpresso"`, `"nexpresso-prod"`). Le matcher du hook est une regex évaluée sur le nom complet de l'outil (`mcp__nexpresso__posts_create`) :

```
mcp__.*[Nn]expresso.*__(posts|projects|reviews|faqs|categories|tags|media|settings)_(create|update|delete)
```

Si le serveur est nommé autrement (ex. `cms`), remplacer `[Nn]expresso` par ce nom dans `hooks/hooks.json` — une ligne, rien d'autre à changer. Sinon le garde-fou ne se déclenche pas.

Les scopes OAuth du jeton déterminent les tools visibles : un tool d'écriture absent signifie un scope manquant, pas une invitation à contourner le MCP.

## Installation

```
/plugin marketplace add Nath-vfx/nexpresso-connect-plugin
/plugin install nexpresso-connect@banan-nexpresso
```

Installé en cours de session : `/reload-plugins`.

Depuis une copie locale du dépôt :

```
/plugin marketplace add /chemin/vers/nexpresso-connect-plugin
/plugin install nexpresso-connect@banan-nexpresso
```

## Comportement du hook

`hooks/publish-gate.py` s'exécute avant chaque écriture Nexpresso et retourne `permissionDecision: "ask"` dans deux cas :

- `status: "published"` dans les arguments → prompt de confirmation de mise en ligne ;
- tool `*_delete` → prompt de confirmation de suppression définitive.

Le prompt porte l'étiquette `[Plugin]`. **Refuser laisse le contenu en brouillon** (aucun appel n'est émis). Tout le reste — création de brouillon, correction d'un champ, `settings_update` sans `status` — passe en silence : le hook sort en 0 sans stdout et le flux de permission normal s'applique. Un événement illisible ne bloque jamais.

## Vérification

```
python3 hooks/test_publish_gate.py   # affiche "ok"
```

Couvre : publication → `ask`, promotion d'un brouillon → `ask`, suppression → `ask`, brouillon / PATCH partiel / event bidon → silence.
