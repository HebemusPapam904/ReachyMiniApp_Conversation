# ReachyMiniApp

Ce dépôt contient :

- **[`conversation_relay/`](conversation_relay/)** — une app Reachy Mini de conversation (voix + LLM, forkée
  depuis [`reachy_mini_conversation_app`](https://github.com/pollen-robotics/reachy_mini_conversation_app))
  qui relaie chaque échange de conversation terminé (utilisateur + assistant) vers un webhook HTTP externe,
  pour pouvoir brancher la conversation du robot sur un autre système, dans le format de ton choix.
- **[`webhook_viewer.py`](webhook_viewer.py)** — un petit serveur web local sans dépendance qui affiche ce
  que le relais lui envoie. Pratique pour tester le pipeline sans récepteur réel.

Ça fonctionne aussi bien avec un Reachy Mini **simulé** (aucun matériel requis) qu'avec un **vrai** Reachy
Mini (Lite ou Wireless), sur Windows, macOS ou Linux.

---

## 1. Prérequis

- **Python 3.12+**
- **git**
- **[uv](https://docs.astral.sh/uv/)** (recommandé) ou `pip`

Installer uv si tu ne l'as pas :

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## 2. Cloner et préparer l'environnement

```bash
git clone https://github.com/HebemusPapam904/ReachyMiniApp_Conversation.git
cd ReachyMiniApp_Conversation

uv venv .venv
```

Activer l'environnement virtuel :

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Installer le SDK Reachy Mini et l'app de conversation (en mode éditable, pour que les modifications de code
prennent effet immédiatement) :

```bash
uv pip install reachy-mini
uv pip install -e conversation_relay
```

Si tu comptes utiliser le **simulateur**, installe aussi l'extra MuJoCo :

```bash
uv pip install "reachy-mini[mujoco]"
```

---

## 3. Configurer

```bash
cd conversation_relay
cp .env.example .env
```

Éditer `.env` :

| Variable | Rôle |
|---|---|
| `HF_TOKEN` | Optionnel. Token gratuit sur [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens). Pas obligatoire pour le backend gratuit hébergé par défaut, mais améliore la fiabilité. |
| `RELAY_WEBHOOK_URL` | Où sont envoyés les échanges de conversation terminés, ex. `http://127.0.0.1:8686/ShariiingClient/sendNote` pour tester en local avec `webhook_viewer.py`, ou l'URL de ton vrai récepteur. |

> **Aucune clé OpenAI n'est nécessaire.** L'app utilise par défaut le backend temps réel gratuit hébergé par
> Hugging Face (`HF_REALTIME_CONNECTION_MODE=deployed`). Pour pointer vers ton propre backend temps réel à
> la place (ex. [speech-to-speech](https://github.com/huggingface/speech-to-speech) tournant en local) :
> ```env
> HF_REALTIME_CONNECTION_MODE=local
> HF_REALTIME_WS_URL=ws://127.0.0.1:8765/v1/realtime
> ```

`.env` est ignoré par git — chaque machine sur laquelle tu déploies a besoin de sa propre copie.

---

## 4. (Optionnel) Lancer le viewer de webhook

Pour observer les messages relayés en local sans mettre en place un vrai récepteur :

```bash
# depuis la racine du dépôt, avec le venv activé
python webhook_viewer.py
```

Ouvrir **http://127.0.0.1:8686/** dans un navigateur. Pointe `RELAY_WEBHOOK_URL` vers cette adresse
(utilise l'IP locale de la machine plutôt que `127.0.0.1` si le robot/daemon tourne sur une machine
différente de celle du viewer).

---

## 5. Lancer : Reachy Mini simulé

Fonctionne sur n'importe quelle machine, aucun matériel requis. Tout tourne sur `localhost`.

1. Démarrer le daemon simulé (ouvre une fenêtre de visualisation 3D) :

   ```bash
   reachy-mini-daemon --sim
   ```

   Sur macOS, utiliser `mjpython -m reachy_mini.daemon.app.main --sim` à la place.

2. Dans un **second terminal** (même venv), ouvrir le dashboard :

   **http://127.0.0.1:8000/**

   `conversation_relay` apparaît dans la liste des apps installées → clique **Start**.

   Ou via l'API REST :
   ```bash
   curl -X POST http://localhost:8000/api/apps/start-app/conversation_relay
   ```

3. Parle dans le micro de ton PC — la simulation route l'audio réel via le micro/haut-parleurs système, pas
   seulement la vue 3D.

Les logs de l'app s'affichent directement dans le terminal qui fait tourner le daemon.

---

## 6. Lancer : vrai Reachy Mini

### Reachy Mini Lite (connecté en USB à cette machine)

Comme la simulation, sans `--sim` :

```bash
reachy-mini-daemon
```

Puis démarre l'app depuis le dashboard (`http://127.0.0.1:8000/`) ou l'API REST, comme ci-dessus.

### Reachy Mini Wireless (machine séparée sur le réseau)

Le robot Wireless fait tourner son propre daemon sur son calculateur embarqué — tu déploies l'app *vers*
lui plutôt que de la lancer en local.

1. **Copier l'app sur le robot :**

   ```bash
   scp -r conversation_relay pollen@reachy-mini.local:/tmp/conversation_relay
   scp conversation_relay/.env pollen@reachy-mini.local:/tmp/conversation_relay/.env
   ```

   Remplace `reachy-mini.local` par l'IP du robot si `.local` ne se résout pas sur ton réseau.

2. **L'installer dans le venv partagé des apps du robot :**

   ```bash
   ssh pollen@reachy-mini.local "/venvs/apps_venv/bin/pip install /tmp/conversation_relay"
   ```

3. **Démarrer l'app** — depuis le dashboard sur `http://reachy-mini.local:8000/`, ou :

   ```bash
   curl -X POST http://reachy-mini.local:8000/api/apps/start-app/conversation_relay
   ```

4. **Logs :**

   ```bash
   ssh pollen@reachy-mini.local
   sudo journalctl -u reachy-mini-daemon -f
   ```

5. **Après une modification de code**, refais les étapes 1–2, puis redémarre l'app (pas besoin de
   redémarrer tout le daemon).

Assure-toi que `RELAY_WEBHOOK_URL` dans le `.env` copié sur le robot pointe vers une machine joignable
depuis le réseau du robot (pas `127.0.0.1` sur ton laptop) — par exemple lance `webhook_viewer.py` sur une
machine du même réseau local et utilise son IP.

---

## 7. Changer la voix / la personnalité

Ouvre l'interface web de l'app :
- Simulation / Lite (local) : `http://localhost:7860`
- Wireless : icône réglages sur le dashboard, ou `http://reachy-mini.local:7860`

Le panneau **Voice** permet de choisir une voix en direct, sans redémarrage. Pour changer le comportement
de l'assistant, édite
[`conversation_relay/profiles/_conversation_relay_locked_profile/instructions.txt`](conversation_relay/profiles/_conversation_relay_locked_profile/instructions.txt)
et `tools.txt` dans le même dossier.

---

## Dépannage

| Symptôme | Solution |
|---|---|
| "An app is already running" | `curl -X POST http://<host>:8000/api/apps/stop-current-app` |
| Daemon dans un état bloqué | `sudo systemctl restart reachy-mini-daemon` (Wireless), ou redémarrer le processus `reachy-mini-daemon` (Lite/simu) |
| L'app ne prend pas en compte les changements de code | Redémarrer l'app ; si déployée manuellement sur Wireless, vider aussi les `__pycache__` |
| Rien n'arrive au webhook | Vérifier que `RELAY_WEBHOOK_URL` dans `.env` est joignable depuis l'endroit où l'app tourne réellement (pas `127.0.0.1` si le robot/daemon est sur une autre machine) |

Plus de détails dans [`conversation_relay/README_OLD.md`](conversation_relay/README_OLD.md) (doc originale
de l'app de conversation) et la [doc du SDK Reachy Mini](https://github.com/pollen-robotics/reachy_mini).
