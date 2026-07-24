# Plan — conversation_relay

## Compréhension du besoin

App Reachy Mini qui intercepte la conversation vocale entre l'utilisateur et le LLM
(app de conversation officielle, forkée depuis `reachy_mini_conversation_app`) et
redistribue chaque message sur le réseau local, dans un format configurable.

Décisions déjà actées (via questions posées) :

- **Canal réseau** : Webhook HTTP POST vers une URL configurable.
- **Robot** : Reachy Mini Wireless (CM4 embarqué, réseau WiFi limité).
- **Contenu intercepté** : messages finaux uniquement (pas les deltas de streaming
  partiels), pour le tour utilisateur ET le tour assistant.
- **Publication** : app locale pour l'instant, pas de publication Hugging Face.

## Point d'intégration identifié dans le code

Le fork forme une base saine : la logique de streaming réaltime expose déjà un hook
d'observation de transcript, sans qu'aucune modification du cœur de l'app soit
nécessaire.

- [`src/conversation_relay/conversation_handler.py:49`](src/conversation_relay/conversation_handler.py) —
  `ConversationHandler.set_transcript_observer(observer: Callable[[str, str, bool], None])`
  attache un callback `(role, text, final)`.
- [`src/conversation_relay/huggingface_realtime.py:849,858`](src/conversation_relay/huggingface_realtime.py) —
  émet `_emit_transcript("user", transcript, True)` et
  `_emit_transcript("assistant", event.transcript or "", True)` — donc **déjà
  `final=True` uniquement**, aucun filtrage à ajouter.
- [`src/conversation_relay/console.py:145-160`](src/conversation_relay/console.py) —
  `LocalStream._attach_observers_to_handler()` appelle actuellement
  `set_transcript_observer(self._dispatch_transcript)`, qui pousse vers l'UI web
  locale via JSON-RPC (`conversation.transcript`). Un seul observer est
  supporté à la fois (pas de liste), donc **il faut étendre `_dispatch_transcript`**
  plutôt que le remplacer, pour garder l'UI existante fonctionnelle.

## Approche technique proposée

1. Nouveau module `src/conversation_relay/relay.py` :
   - Fonction `send_transcript_webhook(role: str, text: str, final: bool) -> None`.
   - Lit l'URL cible depuis `RELAY_WEBHOOK_URL` (variable d'env, comme le reste de la
     config dans `config.py`).
   - Envoie une requête HTTP POST **asynchrone non-bloquante** (fire-and-forget via
     `asyncio.create_task` + `httpx.AsyncClient`, timeout court ~3s) pour ne jamais
     ralentir la boucle de conversation temps réel — critique sur le CM4 du modèle
     Wireless.
   - Payload JSON par défaut : `{"role": "...", "text": "...", "timestamp": "...", "final": true}`
     (à ajuster selon tes réponses ci-dessous).
   - Échec réseau = log en `debug`/`warning` et on continue (jamais d'exception qui
     remonte dans la boucle de conversation).
2. Dans `console.py`, `_dispatch_transcript` appelle en plus
   `relay.send_transcript_webhook(role, text, final)` après le push JSON-RPC existant.
3. Ajouter `RELAY_WEBHOOK_URL` (et options éventuelles) dans `.env.example` avec
   commentaire.
4. Garder le profil verrouillé `_conversation_relay_locked_profile` tel que généré
   (`profiles/_conversation_relay_locked_profile/instructions.txt` et `tools.txt`),
   à personnaliser une fois le relais validé.

## Questions avant de coder

**Q1. URL du webhook cible ?**
> Réponse : `http://IP:8686/ShariiingClient/sendNote` (remplacer `IP` par l'hôte réel).

**Q2. Format exact du payload JSON attendu par le récepteur ?**
> Réponse : le format par défaut convient — `{"role", "text", "final", "timestamp"}`.

**Q3. Un ou deux webhooks ?**
> Réponse : un seul webhook, `role` distingue user/assistant.

**Q4. Authentification / sécurité sur le webhook ?**
> Réponse : aucune.

**Q5. Comportement en cas d'échec réseau ?**
> Réponse : pas de retry — logguer et continuer.

## Statut : implémenté

- [`src/conversation_relay/relay.py`](src/conversation_relay/relay.py) — `send_transcript_webhook()`,
  POST asynchrone fire-and-forget, timeout 3s, aucune retry, échec = log `warning`.
- [`src/conversation_relay/console.py`](src/conversation_relay/console.py) — `_dispatch_transcript`
  appelle `send_transcript_webhook` en plus du push JSON-RPC existant (UI toujours fonctionnelle).
- `.env.example` et `.env` — `RELAY_WEBHOOK_URL="http://IP:8686/ShariiingClient/sendNote"`
  (remplacer `IP` par l'adresse réelle du récepteur Shariiing avant de lancer l'app).
