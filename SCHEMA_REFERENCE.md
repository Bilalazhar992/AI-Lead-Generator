# AI Lead Generator — Database Schema Reference (Shared Collections / Logical Isolation)

> **Multi-tenancy model:** Shared Collections (Logical Isolation).
> A single database. A single set of collections. Every document in a business-scoped
> collection carries `business_id` (the tenant key) as its **first field**.
> Application middleware appends `{ business_id }` to every query automatically.
> All indexes are compound with `business_id` as the leading key.
>
> **Why this over Collection-per-Tenant:**
> - Collection-per-tenant produces ~14 collections × N businesses. At 1 000 businesses
>   that is 14 000 collections; MongoDB performance degrades noticeably past ~10 000.
> - Schema migrations, index builds, and backups run once on 14 collections instead of
>   once per tenant.
> - Cross-tenant admin/analytics queries are simple single-collection queries.
> - The sole trade-off (logical rather than namespace-level isolation) is fully mitigated
>   by compound indexes leading with `business_id` and mandatory middleware filtering.

---

# PLATFORM COLLECTIONS
> These collections are unchanged from the original design. They were already
> shared and already reference `business_id` where needed.

---

## `users`

> **Unified auth table for all platform and business accounts.** On signup a user gets
> `role: "business_owner"`. `super_admin` is seeded at platform launch.
> `business_owner` creates `business_staff`; `super_admin` creates `platform_staff`.
> Role-specific profile details live in `user_details`.

```javascript
{
  _id: ObjectId,
  email: String,
  password_hash: String,
  first_name: String,
  last_name: String,
  role: Enum,                       // "super_admin" | "business_owner" | "business_staff" | "platform_staff"
  permissions: [Enum],
  // Predefined defaults by role:
  //   super_admin    "manage_subscriptions" | "manage_ai_templates" | "manage_businesses" | "manage_platform_users" | "view_analytics" →  (seeded)
  //   business_owner  → "manage_products" | "manage_leads" | 
  //                     "manage_team" | "manage_billing" | "view_analytics"
  //   business_staff  → selective subset assigned by business_owner at invite time
  //   platform_staff  → selective subset assigned by super_admin at invite time
  // Full permission enum set:
  //   "manage_products" | "manage_leads" | "manage_team"
  //   "manage_billing" | "view_analytics" | "manage_subscriptions"
  //   "manage_ai_templates" | "manage_platform_users" | "manage_businesses"
  is_active: Boolean,
  last_login_at: Date,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `email` (unique)

---

## `user_details`

> **Role-specific profile data.** One document per user. Fields relevant to each role
> are populated; others are omitted. `business_staff` **must** have `business_id` to
> link them to their employer.

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,                // ref → users._id (unique)

  // ── Common profile fields (all roles) ──────────────────────────────
  phone: String,
  avatar_url: String,

  language: String,               // e.g. "en"

  // ── business_owner fields ──────────────────────────────────────────
  // (populated when users.role === "business_owner")

  company_name: String,           // mirrors/seeds businesses.name on signup
  company_website: String,
  industry: String,               // e.g. "retail" | "real_estate" | "healthcare"
  business_size: String,          // e.g. "1-10" | "11-50" | "51-200"

  // ── business_staff fields ─────────────────────────────────
  business_id: ObjectId,            // ref → businesses._id
  business_slug: String,            // denormalized for fast lookups
  invited_by: ObjectId,             // ref → users._id (business_owner who sent the invite)

  // ── platform_staff fields ────────────────────────────────
  department: String,               // e.g. "support" | "billing" | "technical"

  // ── business_owner fields ────────────────────────────────
  // Business is linked on the businesses side: businesses.owner_user_id → users._id

  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `user_id` (unique)

---

## `subscription_plans`
```javascript
{
  _id: ObjectId,
  name: String,
  slug: String,
  price_monthly_pkr: Number,
  price_annual_pkr: Number,
  max_products: Number,
  max_leads_per_month: Number,
  max_ai_messages_per_month: Number,
  max_team_members: Number,
  whatsapp_enabled: Boolean,
  widget_enabled: Boolean,
  remove_branding: Boolean,
  is_active: Boolean,
  display_order: Number,
  created_by: ObjectId,             // ref → users._id
  created_at: Date
}
```
**Indexes:** `slug` (unique)

---

## `ai_templates`
```javascript
{
  _id: ObjectId,
  template_id: String,
  name: String,
  description: String,
  icon: String,
  system_prompt_template: String,
  default_tone: Enum,               // "friendly" | "professional" | "casual"
  default_personality_traits: [String],
  default_primary_goal: Enum,       // "book_meeting" | "capture_lead"
  default_greeting_message: String,
  default_fallback_message: String,
  default_meeting_cta_message: String,
  default_avoid_topics: [String],
  default_handoff_keywords: [String],
  suggested_questions: [
    {
      question_text: String,
      type: Enum,                   // "single_choice" | "text"
      options: [
        {
          label: String,
          score: Number
        }
      ],
      is_required: Boolean
    }
  ],
  created_by: ObjectId,             // ref → users._id (super_admin or platform_staff)
  is_active: Boolean,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `template_id` (unique)

---

## `businesses`
```javascript
{
  _id: ObjectId,
  slug: String,
  business_name: String,
  business_type: String,
  contact_email: String,
  contact_phone: String,
  logo_url: String,
  timezone: String,
  owner_user_id: ObjectId,
  status: Enum,                     // "active" | "suspended" | "cancelled"
  onboarding_completed: Boolean,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `slug` (unique)

---

## `subscriptions`

> **One document per business — always the currently active subscription.**
> When a plan changes the current document is first archived to `subscription_history`,
> then overwritten with the new plan details.

```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // UNIQUE — exactly one active subscription per business
  business_slug: String,            // denormalized
  plan_id: ObjectId,
  plan_slug: String,
  status: Enum,                     // "trialing" | "active" | "past_due" | "cancelled"
  billing_cycle: Enum,              // "monthly" | "annual"
  period_start: Date,
  period_end: Date,
  trial_ends_at: Date,
  payment_method: Enum,             // "stripe"
  payment_reference: String,
  // ── Usage tracking (current period only) ───────────────────
  leads_count: Number,
  ai_messages_count: Number,
  conversations_count: Number,
  leads_limit_reached: Boolean,
  messages_limit_reached: Boolean,
  // ───────────────────────────────────────────────────────────
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `business_id` (unique)

**Plan change procedure (always in this order):**
```
1. Copy current subscriptions doc fields + change_event + archived_at: now → INSERT into subscription_history
2. $set plan_id, plan_slug, status, billing_cycle, period dates, payment fields; reset usage counters to 0
3. $set updated_at: now
Run as a single atomic session — archive first, then overwrite.
```

---

## `subscription_history`

> **Append-only audit trail.** Never updated after insertion.

```javascript
{
  _id: ObjectId,
  business_id: ObjectId,
  business_slug: String,
  plan_id: ObjectId,
  plan_slug: String,
  status: Enum,                     // "trialing" | "active" | "past_due" | "cancelled" | "expired"
  billing_cycle: Enum,              // "monthly" | "annual"
  period_start: Date,
  period_end: Date,
  trial_ends_at: Date,
  payment_method: Enum,             // "stripe"
  payment_reference: String,
  change_event: Enum,               // "trial_started" | "activated" | "upgraded" | "downgraded" | "renewed" | "cancelled" | "past_due"
  // ── Usage at end of this period ────────────────────────────
  leads_count: Number,
  ai_messages_count: Number,
  conversations_count: Number,
  leads_limit_reached: Boolean,
  messages_limit_reached: Boolean,
  // ───────────────────────────────────────────────────────────
  archived_at: Date,
  created_at: Date
}
```
**Indexes:** `business_id`, `(business_id, archived_at)` (compound)

---

## `routing_rules`
```javascript
{
  _id: ObjectId,
  channel_type: Enum,               // "whatsapp" | "widget"
  channel_identifier: String,
  business_id: ObjectId,
  product_id: ObjectId,
  display_name: String,
  is_active: Boolean,
  created_at: Date
}
```
**Indexes:** `(channel_type, channel_identifier)` (compound unique)

---

# BUSINESS COLLECTIONS (Shared, Logical Isolation)

> All collections below are **shared across all tenants**.
> Every document carries `business_id` as its **first field** — this is the tenant key.
> Application middleware **must** append `{ business_id }` to every query.
> All indexes are compound with `business_id` as the leading key to guarantee
> that the query planner always scopes work to a single tenant's data.

---

## `products`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY — mandatory, indexed first
  business_slug: String,            // denormalized
  slug: String,
  name: String,
  description: String,
  website_url: String,
  status: Enum,                     // "draft" | "active" | "paused"
  created_by: ObjectId,             // ref → users._id
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `(business_id, slug)` (compound unique)

---

## `agent_configs`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  product_id: ObjectId,
  template_id: String,
  company_name: String,
  product_name: String,
  product_description: String,
  target_audience: String,
  pricing_info: String,
  tone: Enum,                       // "friendly" | "professional" | "casual"
  personality_traits: [String],
  primary_goal: Enum,               // "book_meeting" | "capture_lead" | "answer_questions"
  greeting_message: String,
  fallback_message: String,
  meeting_cta_message: String,
  avoid_topics: [String],
  never_say: [String],
  always_include: [String],
  handoff_enabled: Boolean,
  handoff_keywords: [String],
  handoff_after_messages: Number,
  handoff_message: String,
  last_preview_snapshot: String,
  last_preview_at: Date,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `(business_id, product_id)` (compound unique)

---

## `qualification_flows`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  product_id: ObjectId,
  is_enabled: Boolean,
  trigger_type: Enum,               // "after_greeting" | "when_interested" | "always"
  trigger_keywords: [String],
  questions: [
    {
      id: String,
      question_text: String,
      type: Enum,                   // "single_choice" | "multiple_choice" | "text" | "number"
      options: [
        {
          label: String,
          score: Number
        }
      ],
      text_score_default: Number,
      is_required: Boolean,
      display_order: Number
    }
  ],
  max_possible_score: Number,
  hot_threshold: Number,
  warm_threshold: Number,
  hot_lead_action: Enum,            // "book_meeting" | "notify_team" | "both"
  warm_lead_action: Enum,
  cold_lead_action: Enum,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `(business_id, product_id)` (compound unique)

---

## `calendar_configs`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  product_id: ObjectId,
  is_enabled: Boolean,
  provider: Enum,                   // "calendly" | "google_calendar"
  calendly_user_uri: String,
  calendly_event_type_uri: String,
  calendly_event_type_name: String,
  calendly_scheduling_url: String,
  calendly_access_token: String,    // encrypted at rest
  calendly_refresh_token: String,   // encrypted at rest
  calendly_token_expires_at: Date,
  calendly_webhook_uri: String,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `(business_id, product_id)` (compound unique)

---

## `whatsapp_channels`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  product_id: ObjectId,
  phone_number: String,
  phone_number_id: String,
  waba_id: String,
  display_name: String,
  profile_picture_url: String,
  about_text: String,
  access_token: String,             // encrypted at rest
  token_expires_at: Date,
  verification_status: Enum,        // "pending" | "verified" | "failed"
  webhook_verify_token: String,
  typing_delay_ms: Number,
  business_hours_enabled: Boolean,
  business_hours_timezone: String,
  business_hours: {
    monday:    { is_open: Boolean, open_time: String, close_time: String },
    tuesday:   { is_open: Boolean, open_time: String, close_time: String },
    wednesday: { is_open: Boolean, open_time: String, close_time: String },
    thursday:  { is_open: Boolean, open_time: String, close_time: String },
    friday:    { is_open: Boolean, open_time: String, close_time: String },
    saturday:  { is_open: Boolean, open_time: String, close_time: String },
    sunday:    { is_open: Boolean, open_time: String, close_time: String }
  },
  outside_hours_message: String,
  is_active: Boolean,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `(business_id, product_id)` (compound unique), `phone_number_id` (unique)

---

## `widget_channels`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  product_id: ObjectId,
  widget_id: String,
  allowed_domains: [String],
  position: Enum,                   // "bottom-right" | "bottom-left"
  primary_color: String,
  header_text: String,
  avatar_url: String,
  show_branding: Boolean,
  auto_open_enabled: Boolean,
  auto_open_delay_seconds: Number,
  proactive_enabled: Boolean,
  proactive_message: String,
  proactive_delay_seconds: Number,
  prechat_enabled: Boolean,
  prechat_fields: [
    {
      field_name: String,
      field_label: String,
      field_type: Enum,             // "text" | "email" | "tel"
      is_required: Boolean
    }
  ],
  welcome_message: String,
  offline_message: String,
  input_placeholder: String,
  is_active: Boolean,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `(business_id, product_id)` (compound unique), `widget_id` (unique)

---

## `knowledge_base`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  product_id: ObjectId,
  source_type: Enum,                // "pdf" | "faq" | "website"
  title: String,
  is_active: Boolean,
  pdf_file_url: String,
  pdf_file_name: String,
  pdf_file_size_bytes: Number,
  pdf_page_count: Number,
  faq_question: String,
  faq_answer: String,
  website_url: String,
  website_scraped_at: Date,
  extracted_text: String,
  processing_status: Enum,          // "pending" | "processing" | "completed" | "failed"
  processing_error: String,
  processed_at: Date,
  chunks_count: Number,
  embeddings_created: Boolean,
  tags: [String],
  created_by: ObjectId,             // ref → users._id
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `(business_id, product_id)`, `(business_id, source_type)`, `(business_id, processing_status)`

---

## `embeddings`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  product_id: ObjectId,
  knowledge_base_id: ObjectId,
  chunk_index: Number,
  chunk_text: String,
  embedding: [Number],              // 1536 floats (text-embedding-3-small)
  source_type: Enum,                // "pdf" | "faq" | "website"
  source_title: String,
  created_at: Date
}
```
**Indexes:**
- Atlas Vector Search on `embedding` with `{ business_id, product_id }` pre-filter
- `(business_id, product_id, knowledge_base_id)` (compound)

---

## `leads`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  product_id: ObjectId,
  first_name: String,
  last_name: String,
  email: String,
  phone: String,
  whatsapp_phone: String,
  source_channel: Enum,             // "whatsapp" | "widget"
  source_url: String,
  source_utm_source: String,
  source_utm_medium: String,
  source_utm_campaign: String,
  qualification_score: Number,
  qualification_temperature: Enum,  // "hot" | "warm" | "cold"
  qualification_completed: Boolean,
  extracted_budget: String,
  extracted_interest: String,
  extracted_timeline: String,
  stage: Enum,                      // "new" | "engaged" | "qualified" | "meeting_scheduled" | "converted" | "lost"
  total_conversations: Number,
  total_messages: Number,
  first_contact_at: Date,
  last_contact_at: Date,
  ai_summary: String,
  is_archived: Boolean,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:**
- `(business_id, product_id)` (compound)
- `(business_id, product_id, whatsapp_phone)` (compound unique, sparse)
- `(business_id, product_id, email)` (compound unique, sparse)
- `(business_id, qualification_temperature)`
- `(business_id, stage)`

---

## `lead_qualifications`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  lead_id: ObjectId,
  product_id: ObjectId,
  qualification_flow_id: ObjectId,
  responses: [
    {
      question_id: String,
      question_text: String,
      answer_raw: String,
      answer_mapped: String,
      score_earned: Number,
      answered_at: Date
    }
  ],
  total_score: Number,
  max_possible_score: Number,
  score_percentage: Number,
  temperature: Enum,                // "hot" | "warm" | "cold"
  questions_asked: Number,
  questions_total: Number,
  is_complete: Boolean,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `(business_id, lead_id)` (compound unique), `(business_id, product_id)`

---

## `conversations`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  product_id: ObjectId,
  lead_id: ObjectId,
  channel: Enum,                    // "whatsapp" | "widget"
  status: Enum,                     // "active" | "closed"
  closed_reason: Enum,              // "completed" | "timeout" | "human_takeover"
  message_count: Number,
  ai_message_count: Number,
  human_message_count: Number,
  lead_message_count: Number,
  sentiment_score: Number,
  detected_intent: Enum,            // "booking" | "inquiry" | "support" | "complaint"
  summary: String,
  human_takeover: Boolean,
  human_takeover_by: ObjectId,
  human_takeover_at: Date,
  human_takeover_reason: String,
  session_page_url: String,
  session_device: String,
  session_browser: String,
  started_at: Date,
  last_message_at: Date,
  closed_at: Date,
  created_at: Date
}
```
**Indexes:** `(business_id, product_id)`, `(business_id, lead_id)`, `(business_id, status)`, `(business_id, last_message_at)`

---

## `ai_sessions`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  conversation_id: ObjectId,
  lead_id: ObjectId,
  product_id: ObjectId,
  message_window: [
    {
      role: Enum,                   // "user" | "assistant" | "tool"
      content: String,
      tool_call_id: String,
      timestamp: Date
    }
  ],
  message_window_size: Number,
  running_summary: String,
  summary_covers_message_count: Number,
  questions_answered: [String],
  questions_remaining: [String],
  current_total_score: Number,
  qualification_complete: Boolean,
  current_goal: Enum,               // "greet" | "qualify" | "answer_faq" | "push_booking" | "completed"
  total_tokens_used: Number,
  last_turn_tokens: Number,
  handoff_triggered: Boolean,
  handoff_reason: Enum,             // "keyword_detected" | "message_count_exceeded" | "manual"
  consecutive_messages_without_conversion: Number,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `(business_id, conversation_id)` (compound unique), `(business_id, product_id)`

---

## `messages`
```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  conversation_id: ObjectId,
  sender_type: Enum,                // "lead" | "ai" | "human"
  sender_user_id: ObjectId,
  content_type: Enum,               // "text" | "image" | "document" | "audio"
  text: String,
  media_url: String,
  media_type: String,
  media_filename: String,
  ai_model: String,
  ai_tokens_prompt: Number,
  ai_tokens_completion: Number,
  ai_tokens_total: Number,
  ai_response_time_ms: Number,
  ai_used_rag: Boolean,
  ai_rag_sources: [ObjectId],
  ai_function_calls: [
    {
      function_name: String,
      arguments: Object,
      executed_at: Date
    }
  ],
  external_message_id: String,
  delivery_status: Enum,            // "sent" | "delivered" | "read" | "failed"
  delivery_status_at: Date,
  created_at: Date
}
```
**Indexes:** `(business_id, conversation_id)`, `(business_id, created_at)`

---

## `meetings`

> **One meeting document per conversation** — enforced by the unique index on
> `(business_id, conversation_id)`. If a lead cancels and rebooks within the same
> conversation, the existing document is **updated** and `rescheduled_count` is incremented.

```javascript
{
  _id: ObjectId,
  business_id: ObjectId,            // ★ TENANT KEY
  business_slug: String,
  product_id: ObjectId,
  lead_id: ObjectId,
  conversation_id: ObjectId,
  title: String,
  description: String,
  scheduled_at: Date,
  duration_minutes: Number,
  timezone: String,
  provider: Enum,                   // "calendly"
  external_event_id: String,
  external_event_uri: String,
  meeting_link: String,
  lead_name: String,
  lead_email: String,
  lead_phone: String,
  host_name: String,
  host_email: String,
  status: Enum,                     // "scheduled" | "completed" | "cancelled" | "no_show"
  rescheduled_count: Number,
  cancelled_by: Enum,               // "lead" | "host"
  cancelled_at: Date,
  cancelled_reason: String,
  outcome: Enum,                    // "converted" | "follow_up" | "not_interested" | "no_outcome"
  outcome_notes: String,
  created_at: Date,
  updated_at: Date
}
```
**Indexes:** `(business_id, conversation_id)` (compound unique), `(business_id, product_id)`, `(business_id, lead_id)`, `(business_id, status)`, `(business_id, scheduled_at)`

---

# Collection Inventory

## Platform Collections (8)
| Collection | Purpose |
|---|---|
| `users` | Auth accounts for all roles |
| `user_details` | Role-specific profile data |
| `subscription_plans` | Plan catalog |
| `ai_templates` | AI agent templates |
| `businesses` | Tenant registry |
| `subscriptions` | Active subscription per business |
| `subscription_history` | Billing audit trail |
| `routing_rules` | Channel → product routing |

## Business Collections — Shared (14)
| Collection | Tenant Key | Was |
|---|---|---|
| `products` | `business_id` | `{slug}_products` |
| `agent_configs` | `business_id` | `{slug}_agent_configs` |
| `qualification_flows` | `business_id` | `{slug}_qualification_flows` |
| `calendar_configs` | `business_id` | `{slug}_calendar_configs` |
| `whatsapp_channels` | `business_id` | `{slug}_whatsapp_channels` |
| `widget_channels` | `business_id` | `{slug}_widget_channels` |
| `knowledge_base` | `business_id` | `{slug}_knowledge_base` |
| `embeddings` | `business_id` | `{slug}_embeddings` |
| `leads` | `business_id` | `{slug}_leads` |
| `lead_qualifications` | `business_id` | `{slug}_lead_qualifications` |
| `conversations` | `business_id` | `{slug}_conversations` |
| `ai_sessions` | `business_id` | `{slug}_ai_sessions` |
| `messages` | `business_id` | `{slug}_messages` |
| `meetings` | `business_id` | `{slug}_meetings` |

**Total: 22 collections — fixed, regardless of how many businesses onboard.**

---

# Implementation Rules for Developers

1. **Middleware is mandatory.** Every database query on a business collection must pass
   through a middleware layer that injects `{ business_id: <active_tenant_id> }` into the
   filter. No raw query to these collections should ever skip this step.

2. **business_id is always first in compound indexes.** This ensures MongoDB's query
   planner scopes the index scan to a single tenant before filtering on any other field.

3. **Never return cross-tenant data.** Service-layer unit tests must assert that queries
   for tenant A never return documents belonging to tenant B.

4. **business_slug is denormalized, not authoritative.** It is stored for human-readable
   logging and convenience. The source of truth for tenant identity is always `business_id`
   (ObjectId). Slug changes to a business must also update `business_slug` in all
   business collections via a migration.

5. **Deletion is clean.** To fully remove a tenant, run a single
   `deleteMany({ business_id: <id> })` on each of the 14 business collections plus
   delete the `businesses`, `subscriptions`, `subscription_history`, and `routing_rules`
   documents. No collection drops needed.
