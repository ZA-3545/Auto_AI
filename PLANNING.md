# AutoAI — Project Planning & Architecture Reference

> Independent proof-of-concept AI Car Buying Assistant for Pakistan's automotive market. Not affiliated with or endorsed by PakWheels.
>
> Working name: **AutoAI** (alternatives considered: CarWise AI, AutoAdvisor, CarGuide AI, AutoMate, CarMatch AI — final name TBD). Do not use "PakWheels AI" or any PakWheels branding without explicit permission.

This document is the single source of truth for architecture, scope, and principles. Refer back to it during development (including when using AI coding tools like Cursor) to keep decisions consistent across sessions.

---

## A. Product Definition

- **What it is:** A conversational decision-support layer that converts natural-language requirements into structured search + a deterministic recommendation engine + LLM-generated explanations.
- **What it is NOT:** A generic chatbot, a listing scraper, or an "official PakWheels" product.
- **Journey it replaces:** Search → Filters → Listings → Research → Comparison → Decision, becomes: User describes requirement → AI understands → AI asks relevant questions → AI searches available vehicles → AI recommends → AI compares → AI explains pros/cons → AI guides toward purchase/inspection/finance/service. The product should feel like a knowledgeable automotive buying consultant available 24/7.
- **North star:** Trust and accuracy — never show invented data.
- **Priority order for every decision (highest to lowest):** Accuracy → Trust → Good UX → Deterministic recommendations → Explainability → Clean architecture → Scalability → Security → Legal compliance → Business value. When two priorities conflict, the higher one wins. This is a real product, not a university-style chatbot demo — do not use an LLM where simple database filtering or calculation would do.

---

## B. Architecture (fixed principles)

1. The LLM's job is only: intent detection → requirement extraction → tool selection → natural-language explanation.
2. The backend's job is: search, filter, scoring, comparison — all deterministic and testable.
3. Every LLM output must validate against a schema (structured output / function calling). Invalid output is rejected or re-asked, never silently accepted.
4. Keep an AI provider abstraction layer so the model/provider can be swapped later.

---

## C. Data Layer

- Entities: `users`, `vehicles`, `vehicle_variants`, `listings`, `conversations`, `messages`, `user_preferences`, `comparisons`, `inspection_reports`, `recommendations`.
- Sample dataset: 50–100+ realistic (manually referenced, never scraped) records, clearly labeled as demo data.
- Maintain a data dictionary: field definitions, allowed values, source of truth for each.
- Brand coverage for demo dataset: Toyota, Honda, Suzuki, Hyundai, Kia, Changan, MG, Nissan, Daihatsu, and other relevant Pakistani-market brands — with variety across models, years, cities, price ranges, mileage, transmissions, fuel types, and body types.

---

## C.1 Technology Stack

**Frontend:**
- Next.js + TypeScript
- Tailwind CSS
- shadcn/ui component library
- Lucide icons

**Backend:**
- Python + FastAPI (async support, strong AI/ML integration ecosystem)
- Responsibilities: authentication, chat API, vehicle search, recommendation engine, user preferences, conversation management, AI orchestration, listing analysis, database access

**Database:**
- PostgreSQL
- SQLAlchemy or SQLModel as ORM
- Alembic for migrations
- pgvector extension for RAG/embeddings (post-MVP)

**AI Architecture Pipeline:**
```
User message
  → Intent detection
  → Requirement extraction
  → Structured JSON
  → Backend tools/functions
  → Database search
  → Recommendation engine
  → Optional RAG retrieval
  → LLM response generation
  → User
```
Use structured outputs / function calling at each LLM boundary.

**Deployment:**
- Frontend: Vercel
- Backend: Render / Railway (or similar) initially; AWS/Azure/GCP later if scaling requires it
- Database: managed PostgreSQL service
- Use Docker, environment variables, CI/CD, logging, and monitoring from the start

---

## D. AI Layer / Tools

- Tools: `search_cars()`, `get_car_details()`, `compare_cars()`, `analyze_listing()`, `search_maintenance_info()`.
  (Finance and inspection tools are future-phase — not in MVP.)
- Confidence handling: if extraction confidence is low, the AI asks a clarifying question instead of assuming.
- Ambiguity handling: numbers without units (e.g. "budget 30") must be clarified — lakh vs PKR, etc.
- The LLM must NOT invent cars directly — extracted requirements are structured JSON, passed to the backend recommendation engine.

**Example structured requirement output:**
```json
{
  "budget_min": null,
  "budget_max": 3000000,
  "city": "Lahore",
  "condition": "used",
  "transmission": "automatic",
  "body_type": null,
  "purpose": "family",
  "fuel_priority": true,
  "resale_priority": null
}
```

**Seller/buyer questions the assistant should be able to generate** (useful even with no exact listing data):
Original owner? Number of owners? Accident history? Original paint? Engine condition? Transmission condition? Mileage verification? Service history? Token/tax status? Registration documents? Any outstanding finance? Why are you selling?

---

## E. Recommendation Engine

- Configurable weighted scoring: budget fit (30%), purpose/family suitability (25%), fuel economy (20%), resale (15%), mileage/condition (10%) — weights configurable, not hardcoded.
- Score explanation is mandatory for every result.
- The engine must be unit-testable independently of the LLM — it should work even if the LLM layer is down.

---

## F. Comparison Engine

- Structured, factor-by-factor comparison, sourced from the database only — never invented by the LLM.
- Comparison factors: price, model year, engine, transmission, fuel economy, mileage, resale, maintenance, parts availability, comfort, family suitability, performance, and safety/features where reliable data exists.
- The "best for X" conclusion must depend on the user's stated priorities, not be generic.

---

## G. Conversation Layer

- Session-based memory (budget, city, transmission preference, etc.) persists across turns.
- Provide a clear reset mechanism ("start a new search").

---

## H. Trust & Safety Layer

- Product personality: the AI behaves like an honest automotive advisor, not a salesperson pushing a purchase. It asks clarifying questions, explains reasoning, shows uncertainty, and never claims verified information without evidence.
- FACT / INFERENCE / UNKNOWN labeling is mandatory in listing analysis.
- Listing analyzer (post-MVP) covers: asking price, year, mileage, location, variant, available information, potential red flags, missing information, questions to ask the seller, and negotiation considerations.
- Never invent a price or listing — if data isn't available, say so explicitly.
- Disclaimer must be visible: "Independent proof of concept — not affiliated with PakWheels."

---

## I. Cost & Reliability

- Graceful fallback + retry logic on LLM API failure.
- Token/cost tracking per conversation, even at MVP stage (basic logging is enough).
- Rate limiting on the chat endpoint.

---

## J. Privacy Stance

- Define a simple retention policy for chat/preference data (how long stored, when anonymized).
- Document this in the repo, even briefly.

---

## K. Testing Strategy

- Requirement-extraction test set (mixed Roman Urdu + English inputs).
  - Example: input `"35 lakh mein Lahore ke liye automatic family car"` → expected `budget_max=3500000, city=Lahore, transmission=automatic, purpose=family`.
- Hallucination test set (non-existent cars, future models).
  - Example: input `"Show me a 2027 model XYZ car"` → AI must NOT invent a listing.
- Ambiguity test set.
  - Example: input `"My budget is 30"` → AI should ask `"Do you mean PKR 30 lakh?"` rather than assume.
- Recommendation-correctness tests (results actually satisfy stated filters).
- Comparison tests (data comes from the DB, never invented by the LLM).
- Target: 30–50 test queries minimum.

---

## K.1 Evaluation Metrics

Track these to keep product quality measurable, not just "it feels done":

- Requirement-extraction accuracy
- Search relevance
- Recommendation relevance
- Hallucination rate
- Response latency
- API cost per conversation
- Comparison usage rate
- Listing-analysis usage rate (once that feature exists)
- User satisfaction
- Click-through rate

---

## L. UX / UI

- Professional automotive look — chat interface + recommendation cards + comparison cards + price badges + match score + pros/cons + follow-up questions + quick-prompt buttons.
- Explicit action buttons: "Why this car?", "Analyze this listing", "Compare".
- Suggested hero copy: headline "Find the right car with AI," subheading "Tell us your budget, needs and priorities. Our AI will help you discover and compare the best options."
- Suggested quick prompts: "Best car under 30 lakh," "Family car," "Best fuel average," "Automatic cars," "Best resale," "Compare two cars."

---

## M. Repository & Presentation

- Professional README: architecture diagram, setup guide, env var docs, API docs, DB schema, screenshots, demo video, roadmap, known limitations, license.
- `.env` + `.gitignore` — never commit secrets or API keys.

---

## N. Legal / Compliance

- No scraping. No misleading use of PakWheels branding. No false claims of official affiliation.
- Clear proof-of-concept disclaimer everywhere: UI, docs, and pitch materials.

---

## O. MVP Boundary (strict)

**In scope (Must Have):**
- Chat interface
- Natural-language requirement extraction
- Car search/filtering
- Recommendation engine + match score
- Car comparison
- Conversation memory
- Responsive UI

**Nice to Have (after MVP, before "future"):**
- Listing analyzer
- AI buying advice
- Seller questions generator
- RAG knowledge base

**Future (later phases):**
- Inspection report analysis
- Finance assistant
- Maintenance assistant
- Dealer lead generation
- Voice assistant
- Mobile app
- Real-time authorized automotive listings
- Production PakWheels integration

---

## P. Risk Register

| Risk | Mitigation |
|---|---|
| Hallucination | Deterministic backend + strict prompting + test suite |
| Data realism/credibility | Manually curated, realistic sample dataset |
| Legal exposure | No scraping, explicit disclaimers |
| Scope creep | Hard MVP boundary, future features clearly separated |
| Cost/failure | Fallback handling, confidence thresholds, logging |
| Differentiation | Competitive check before pitch — confirm nothing similar already exists |
| Distribution/pitch access | Build independent traction first rather than relying solely on cold outreach |

---

## Q. Business Value (for the pitch)

The pitch should NOT simply be "we built an AI chatbot." Instead: "we built a conversational AI layer that simplifies the car discovery and buying journey."

Potential business benefits to highlight:
- Better user experience
- Faster vehicle discovery
- Higher engagement
- More comparison activity
- More qualified leads
- More inspection bookings
- More finance leads
- Better dealer conversion
- Increased time spent on platform
- Personalized recommendations
- 24/7 automotive assistance

The AI should be framed as complementing existing PakWheels services, not replacing them.

---

## R. Pitch Package (for later, post-MVP)

Do not approach PakWheels with only an idea — first build a working independent proof of concept. Only once the MVP is functional does it make sense to prepare:

- Live demo
- 2–3 minute demo video
- Product screenshots
- Architecture diagram
- Technical documentation
- Business value proposal
- MVP roadmap
- Integration proposal

Position strictly as: **"Independent proof of concept for an AI-powered conversational car buying assistant — not affiliated with or endorsed by PakWheels."**

---

## Build Order — Project Phases

**Phase 1 — Foundation:** repository, backend, frontend, database, environment configuration, API architecture.

**Phase 2 — Vehicle Search:** vehicle schema, sample dataset, search API, filtering, sorting.

**Phase 3 — AI Requirement Extraction:** LLM integration, structured output, intent detection, follow-up questions.

**Phase 4 — Recommendation Engine:** matching algorithm, scoring, ranking, explanation.

**Phase 5 — AI Comparison:** comparison API, comparison UI, personalized recommendation.

**Phase 6 — RAG (post-MVP):** automotive knowledge base, embeddings, pgvector, retrieval pipeline.

**Phase 7 — Listing Analyzer (post-MVP):** listing input, structured extraction, red flags, price analysis, questions for seller.

**Phase 8 — Production Polish:** authentication, error handling, logging, monitoring, rate limiting, security, responsive UI, testing, deployment.

Test each phase before moving to the next.

---

## Instructions for AI Coding Assistants (Cursor, etc.)

When generating code for this project:

- Keep the LLM strictly to language/orchestration tasks (Section B). Never let it perform DB queries or scoring logic directly.
- Follow the Build Order above — do not skip ahead to later phases.
- Use type hints, environment variables for secrets, and proper error handling.
- Do not introduce unnecessary dependencies.
- Verify any package/API against current documentation before relying on it — do not assume training-data knowledge is current.
- Keep the AI provider abstraction modular.
- Do not deviate from the architecture in Section B without explicit discussion.
