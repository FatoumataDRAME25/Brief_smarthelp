# SmartHelp — Micro-service de Support Client Multimodal (Audio & Vision)

> Documentation technique complète du projet, rédigée pour permettre à toute personne 
> (même sans connaître le projet) de comprendre, installer et faire fonctionner l'API.

---

## Sommaire

1. [Présentation du projet](#1-présentation-du-projet)
2. [Architecture du projet](#2-architecture-du-projet)
3. [Prérequis système](#3-prérequis-système)
4. [Installation et lancement](#4-installation-et-lancement)
5. [Utilisation de l'API](#5-utilisation-de-lapi)
6. [Détails techniques par brique](#6-détails-techniques-par-brique)
7. [Limites connues et pistes d'amélioration](#7-limites-connues-et-pistes-damélioration)
8. [Git Flow et gestion de projet](#8-git-flow-et-gestion-de-projet)
9. [Auteur / Contexte pédagogique](#9-auteur--contexte-pédagogique)

---

## 1. Présentation du projet

### Contexte

Dans une entreprise e-commerce, le service client reçoit quotidiennement des réclamations
via des applications de messagerie, souvent sous forme de messages vocaux ou de photos de
produits endommagés. Le traitement manuel de ces réclamations (écoute des vocaux, analyse
des photos, recherche dans les CGV) prend un temps précieux à l'équipe support.

**SmartHelp** est un micro-service backend qui automatise cette première analyse : il reçoit
une réclamation (audio et/ou image et/ou texte), l'analyse grâce à des modèles d'intelligence
artificielle, interroge une base de connaissances interne (FAQ/CGV), et retourne un diagnostic
structuré permettant d'aiguiller instantanément le dossier.

### Fonctionnalités principales

- **Transcription automatique** des messages vocaux (ASR via Whisper)
- **Analyse visuelle** des photos de produits (classification via ViT)
- **Recherche sémantique** dans la base de règles internes (RAG via ChromaDB)
- **Diagnostic structuré** : statut proposé (Remboursable, À vérifier, Refusé, etc.) basé
  sur une règle interne identifiée automatiquement
- **API robuste** : validation des entrées, gestion propre des erreurs, nettoyage garanti
  des fichiers temporaires

---

## 2. Architecture du projet

### Arborescence

```
smarthelp/
├── main.py                      # Point d'entrée : crée l'app FastAPI et rattache les routes
├── requirements.txt             # Dépendances Python du projet
├── .gitignore
│
├── app/
│   ├── routes/
│   │   └── support_ticket.py    # Endpoint POST /support-ticket : orchestre tous les services
│   │
│   ├── services/
│   │   ├── asr_service.py       # Transcription audio (Whisper)
│   │   ├── vision_service.py    # Analyse d'image (ViT)
│   │   └── rag_service.py       # Recherche vectorielle dans la base de connaissances
│   │
│   ├── schemas/
│   │   └── ticket_schema.py     # Modèles Pydantic (TicketResponse, StatutTicket)
│   │
│   └── core/                    # (réservé pour config future si le projet grandit)
│
├── data/
│   └── faq_cgv.txt              # Base de connaissances interne (règles de support)
│
└── temp/                        # Dossier de travail pour les fichiers temporaires
                                  # (rempli et vidé automatiquement à chaque requête)
```

### Principe de séparation des responsabilités

Chaque dossier a **une seule raison de changer** :

- `routes/` : reçoit les requêtes HTTP, orchestre les appels, ne contient **aucune logique
  métier IA**
- `services/` : contient la logique technique/IA pure (un fichier = un service = une
  responsabilité), sans jamais décider d'un statut final
- `schemas/` : définit la forme exacte des données échangées (validation + documentation
  Swagger automatique)
- `data/` : contient les données métier (règles de l'entreprise), séparées du code

Cette séparation permet, entre autres, de tester chaque service **individuellement** avant
de les assembler dans la route principale (voir section 6), et de limiter les conflits Git
en cas de travail à plusieurs.

### Choix techniques justifiés

| Choix | Justification |
|---|---|
| **FastAPI** | Framework moderne, génère automatiquement la documentation Swagger (`/docs`), gère nativement l'upload de fichiers via `multipart/form-data` |
| **`multipart/form-data`** | Seul format HTTP capable de transporter dans une même requête un mélange de champs texte et de fichiers binaires (audio/image), contrairement à `application/json` qui ne gère que du texte |
| **Whisper (`openai/whisper-small`)** | Modèle ASR open-source, léger, intégrable localement via `transformers` |
| **ViT (`google/vit-base-patch16-224`)** | Modèle de classification d'image généraliste, utilisé faute de modèle spécialisé "détection de dommages produit" disponible librement (voir section 7 — Limites) |
| **LangChain + ChromaDB** | Permettent une recherche par similarité sémantique (embeddings) plutôt qu'une recherche par mots-clés classique, indispensable pour comprendre des reformulations client ("cassé" ≈ "endommagé") |
| **`sentence-transformers/all-mpnet-base-v2`** | Modèle d'embeddings choisi après comparaison avec `all-MiniLM-L6-v2` : plus précis sur nos cas de test (voir section 6.3), au prix d'un temps de chargement légèrement supérieur — compromis jugé pertinent vu l'impact métier d'une mauvaise classification |
| **`@lru_cache(maxsize=1)`** | Implémente le pattern Singleton : chaque modèle IA (Whisper, ViT, embeddings RAG) est chargé une seule fois en mémoire au premier appel, puis réutilisé pour toutes les requêtes suivantes — évite de saturer la RAM et de ralentir chaque requête |

---

## 3. Prérequis système

### Logiciels requis

- **Python 3.12** (ou version compatible)
- **ffmpeg** — prérequis **système**, indépendant de Python, indispensable pour que
  `transformers`/Whisper puisse décoder les fichiers audio. Sans lui, toute requête
  contenant un audio échoue avec l'erreur :
  `ValueError: ffmpeg was not found but is required to load audio files`

Installation sur Ubuntu/Debian :
```bash
sudo apt update
sudo apt install ffmpeg
```

### Dépendances Python

Voir `requirements.txt` à la racine du projet. Principales bibliothèques :

- `fastapi`, `uvicorn`, `python-multipart` — API et serveur
- `transformers`, `torch`, `pillow` — modèles IA (ASR, Vision)
- `langchain-community`, `langchain-text-splitters`, `langchain-huggingface`,
  `langchain-chroma`, `chromadb`, `sentence-transformers` — RAG

---

## 4. Installation et lancement

```bash
# 1. Cloner le dépôt
git clone https://github.com/FatoumataDRAME25/Brief_smarthelp.git
cd Brief_smarthelp

# 2. Créer et activer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Installer ffmpeg (prérequis système, voir section 3)
sudo apt install ffmpeg

# 4. Installer les dépendances Python
pip install -r requirements.txt

# 5. Lancer le serveur (mode développement, rechargement automatique)
uvicorn main:app --reload
```

### Accéder à l'API

Une fois le serveur lancé, ouvrir dans un navigateur :

```
http://127.0.0.1:8000/docs
```

Cette interface Swagger permet de tester l'endpoint `POST /support-ticket` directement,
sans outil externe.

> ⚠️ Au tout premier appel de chaque service (ASR, Vision, RAG), les modèles IA sont
> téléchargés depuis HuggingFace (plusieurs centaines de Mo au total). Ce téléchargement
> ne se produit qu'une seule fois grâce au cache local de `transformers`/`sentence-transformers`.

---

## 5. Utilisation de l'API

### Endpoint

```
POST /support-ticket
Content-Type: multipart/form-data
```

### Paramètres (tous optionnels, mais au moins un requis)

| Paramètre | Type | Description |
|---|---|---|
| `audio_file` | fichier (`.mp3`, `.wav`) | Message vocal du client |
| `image_file` | fichier (`.png`, `.jpg`) | Photo du produit |
| `texte` | texte | Description écrite optionnelle |

Si aucun des trois n'est fourni, l'API retourne une erreur `400 Bad Request` avec un
message explicite.

### Exemple de réponse (200 OK)

```json
{
  "transcription": "mon sac est arrivé cassé",
  "diagnostic_image": null,
  "regle_appliquee": "- Règle 1.1 (Casse / Dommage visible) : Si le client signale un produit cassé, fissuré ou endommagé, et fournit une photo probante de l'article dans un délai de 48 heures suivant la réception, le dossier est éligible à un remboursement intégral ou à un renvoi gratuit. Statut associé : \"Remboursable\".",
  "statut_propose": "Remboursable"
}
```

### Statuts possibles (`statut_propose`)

Basés sur la base de connaissances interne (`data/faq_cgv.txt`) :

`Remboursable`, `À vérifier`, `Échange gratuit`, `Expédition de pièce`,
`Non remboursable - Retard mineur`, `Dédommagement 10%`, `Remboursable - Colis perdu`,
`Refusé`, `En attente de justificatifs`

### Codes d'erreur

| Code | Cas | Exemple |
|---|---|---|
| `400` | Requête vide (aucun champ rempli) | Aucun audio, image ou texte fourni |
| `422` | Fichier fourni mais invalide/corrompu | Fichier `.mp3` en réalité illisible par ffmpeg |

---

## 6. Détails techniques par brique

### 6.1 Service ASR (`app/services/asr_service.py`)

- Charge `openai/whisper-small` via `@lru_cache(maxsize=1)` (Singleton)
- Fonction `transcribe_audio(filepath) -> str` : transcrit un fichier audio en texte
- Dépend de `ffmpeg` (installé au niveau système, pas Python) pour décoder les formats audio

### 6.2 Service Vision (`app/services/vision_service.py`)

- Charge `google/vit-base-patch16-224` via `@lru_cache(maxsize=1)`
- Fonction `analyze_image(filepath) -> str` : retourne le label le plus probable **et** son
  score de confiance (ex: `"backpack (confiance: 0.87)"`)
- Le score est conservé (et non filtré ici) car il constitue une information utile pour la
  suite du traitement : un score très bas signale une image peu exploitable, indépendamment
  du label proposé (voir section 7)

### 6.3 Service RAG (`app/services/rag_service.py`)

Le RAG fonctionne en 3 étapes :

1. **Découpage** : le fichier `faq_cgv.txt` est découpé manuellement en Python (et non via
   `CharacterTextSplitter` de LangChain), en séparant le texte à chaque occurrence de
   `"\n- Règle"`. Ce choix a été fait après avoir constaté que le splitter automatique de
   LangChain pouvait, selon la taille des règles, regrouper plusieurs règles dans un même
   chunk ou isoler un chunk d'en-tête sans contenu exploitable.
2. **Indexation** : chaque règle isolée est transformée en vecteur (embedding) via
   `sentence-transformers/all-mpnet-base-v2`, puis stockée dans ChromaDB — une seule fois
   au démarrage, grâce à `@lru_cache(maxsize=1)`.
3. **Recherche** : `search_knowledge_base(query)` récupère les 3 règles les plus proches
   sémantiquement de la question (`k=3`), puis retourne la première qui contient
   effectivement la mention `"Statut associé"` (garde-fou contre un chunk non exploitable).
   Si aucune des 3 n'est valide, un message de secours est retourné plutôt qu'un texte
   incohérent.

> Il s'agit ici d'un RAG de type *recherche pure* (retrieval), sans étape de génération par
> un LLM : le texte de la règle trouvée est retourné tel quel, conformément à la demande du
> brief ("récupérer la politique applicable").

### 6.4 Route principale (`app/routes/support_ticket.py`)

1. Valide qu'au moins un champ (audio, image, texte) est fourni (sinon `400`)
2. Sauvegarde temporairement les fichiers reçus dans `temp/` (via `shutil.copyfileobj`,
   copie par flux pour ne pas saturer la RAM sur de gros fichiers)
3. Appelle les services ASR/Vision si les fichiers correspondants sont présents, chacun
   entouré d'un `try/except` renvoyant une erreur `422` claire en cas de fichier invalide
4. Combine transcription, diagnostic image et texte saisi en une seule requête pour le RAG
5. Extrait automatiquement le statut final en recherchant, parmi les valeurs de
   `StatutTicket`, celle présente dans le texte de la règle retournée
6. Dans un bloc `finally`, supprime systématiquement les fichiers temporaires créés — que
   la requête ait réussi ou échoué

---

## 7. Limites connues et pistes d'amélioration

### RAG — précision sur les phrases courtes/ambiguës

Le RAG compare le sens global d'une phrase à des règles parfois longues. Sur des phrases
très courtes et sans contexte temporel (ex: "mon produit est cassé", sans mention de délai),
le RAG peut ne pas distinguer certaines règles proches en sens (ex: Règle 1.1 "cassé récent"
vs Règle 1.2 "cassé après 48h") si l'information de délai n'est pas explicitement fournie
par le client. Piste d'amélioration : demander explicitement la date de réception dans la
requête API.

### Vision — modèle généraliste, pas spécialisé

`google/vit-base-patch16-224` est un modèle entraîné sur ImageNet (1000 catégories
génériques d'objets), pas sur un dataset de "produits endommagés". Il peut donc identifier
un objet (ex: "sac à dos") sans jamais évaluer son état (cassé ou non). Le score de
confiance renvoyé indique la fiabilité de la reconnaissance de l'objet, pas l'état du
produit. Piste d'amélioration réaliste : fine-tuner un modèle sur un dataset de produits
endommagés/intacts, ou combiner ce diagnostic avec la transcription et le RAG plutôt que
de s'appuyer sur lui seul.

### ASR — dépendance à la qualité de l'audio

La qualité de la transcription dépend fortement de la qualité de l'enregistrement vocal
d'origine. Des audios synthétiques ou de mauvaise qualité peuvent produire des
transcriptions peu fiables, ce qui impacte ensuite la précision du RAG.

---

## 8. Git Flow et gestion de projet

### Stratégie de branches

Le projet suit une stratégie Git Flow simplifiée :

- `main` : version stable, jamais de commit direct
- `develop` : branche d'intégration de toutes les fonctionnalités
- `feature/xxx` : une branche par fonctionnalité, créée depuis `develop`, fusionnée via
  Pull Request après revue, puis supprimée

Chaque fonctionnalité (SETUP, SCHEMA, ASR, VISION, RAG, API, CORE) a été développée sur sa
propre branche, testée individuellement, puis intégrée à `develop` via Pull Request.

### Tableau Kanban

Le suivi des tâches (Backlog / In Progress / Review / Done) est disponible sur le tableau
Trello du projet : *(lien à insérer ici)*

---

## 9. Auteur / Contexte pédagogique

Projet réalisé par **Fatoumata DRAME**, dans le cadre du brief **SmartHelp** (formation
Développeur Web et Web Mobile).

Dépôt GitHub : https://github.com/FatoumataDRAME25/Brief_smarthelp