# Gmail Real-Time Push Synchronization (Google Cloud Pub/Sub)

FlowInbox AI supports real-time email synchronization via Google Cloud Pub/Sub push notifications. This document outlines the production architecture, setup steps, and webhook integration.

## Architecture Overview

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────────────┐       ┌─────────────────┐
│ Gmail API   │ ────> │ GCP Pub/Sub     │ ────> │ FlowInbox Webhook   │ ────> │ Background Sync │
│ (Mail Box)  │       │ Topic / Sub     │       │ POST /api/v1/webhook│       │ Delta Fetch     │
└─────────────┘       └─────────────────┘       └─────────────────────┘       └─────────────────┘
```

1. **Watch Request**: FlowInbox issues `users.watch()` to Gmail API specifying a Cloud Pub/Sub topic.
2. **Push Event**: When a new email arrives or changes occur, Gmail publishes a base64-encoded message to the topic.
3. **Webhook Trigger**: GCP Pub/Sub pushes an HTTP POST payload to `/api/v1/inbox/webhook/gmail`.
4. **Delta Sync**: The backend extracts the `historyId` and syncs only affected threads without polling.

---

## Google Cloud Platform Setup

### 1. Create Pub/Sub Topic & Subscription
```bash
# Set GCP Project
gcloud config set project YOUR_GCP_PROJECT_ID

# Create Pub/Sub topic
gcloud pubsub topics create flowinbox-gmail-notifications

# Grant Gmail Service Account publish permissions
gcloud pubsub topics add-iam-policy-binding flowinbox-gmail-notifications \
    --member="serviceAccount:gmail-api-push@system.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

# Create Push Subscription pointing to your FlowInbox backend webhook
gcloud pubsub subscriptions create flowinbox-gmail-sub \
    --topic=flowinbox-gmail-notifications \
    --push-endpoint="https://your-domain.com/api/v1/inbox/webhook/gmail"
```

### 2. Configure Backend Environment
Set the following variables in `.env` / Kubernetes secrets:
```env
GMAIL_PUBSUB_TOPIC=projects/YOUR_GCP_PROJECT_ID/topics/flowinbox-gmail-notifications
GMAIL_WEBHOOK_SECRET=your-secure-webhook-token
```

---

## Backend Webhook Handler (`/api/v1/inbox/webhook/gmail`)

```python
@router.post("/webhook/gmail")
async def gmail_push_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle push notifications from Google Cloud Pub/Sub."""
    body = await request.json()
    message = body.get("message", {})
    data_b64 = message.get("data")
    
    if not data_b64:
        return {"status": "ignored"}

    decoded = json.loads(base64.b64decode(data_b64).decode("utf-8"))
    email_address = decoded.get("emailAddress")
    history_id = decoded.get("historyId")

    # Trigger background delta sync for this user
    asyncio.create_task(sync_user_delta(email_address, history_id))
    return {"status": "ok"}
```

---

## Local Development vs. Production

- **Local Development**: FlowInbox uses background polling (`~40s` periodic sync) for lightweight offline setup without requiring GCP cloud infrastructure.
- **Production**: Deploy the Pub/Sub push subscription to achieve sub-second real-time email ingestion.
