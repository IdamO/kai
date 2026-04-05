# Consultation: Agentic Music Curation Architecture

## Context

Kyma Computer, Inc. is a music technology startup (incorporated March 2026, pre-revenue, 2 co-founders) building at the intersection of taste intelligence and AI agents.

The founder just made a critical product direction correction. Previous direction ("Creation Engine") framed the product as AI music generation using ACE-Step (open-source 4B param music generation model). The founder rejected this: "I really would not like to be an AI generated music company." 

The corrected vision: **agentic curation at scale**. Users should be able to "play with the songs they are listening to using AI agents, like OpenClaw/Cursor — agents that connect to the internet, APIs, write scripts, use tools." Collective intelligence from all users helps individuals.

The analogy: **Cursor is an IDE where AI agents help you write code. Kyma is a music environment where AI agents help you curate, discover, and transform music.**

## What Already Exists (Data Primitives)

These are BUILT and validated. They transfer to any product direction:

1. **Taste Graph**: 27.2M curated DJ transitions (from 7 sources: 1001tracklists, Mixesdb, DJ playlists, etc.). Unique pairs after dedup: ~50.2M. Spotify-matched: ~27.2M.

2. **MERT Embeddings**: Audio feature extraction using MERT-v1-330M (Apache 2.0). Layers 5+6 concatenation = 2048d vectors. Covers 800K+ tracks in the manifest.

3. **Bridge API** (running on :8877): 7-dimensional chemistry scoring between track pairs:
   - Rhythmic compatibility (0.35 weight)
   - Harmonic compatibility (0.20)
   - Energy compatibility (0.15)
   - Taste similarity (0.10, from ALS/LightGCN vectors)
   - Community bridge score (0.10, InfoMap cartographic)
   - Timbral compatibility (0.05, MERT spectral)
   - Temporal compatibility (0.05)

4. **FAISS Index**: IVF-PQ index over MERT embeddings for fast nearest-neighbor retrieval.

5. **V8 Transition Scorer**: BPR pairwise scorer, NDCG@20 = 0.7318. Frozen as production ranking model. Uses 2176d input (128d taste + 2048d MERT).

6. **Community Structure**: InfoMap communities with Guimerà-Amaral (z,P) bridge classification. Identifies tracks that connect different taste communities.

7. **Spotify Preview CDN**: ~250M 30-second MP3 previews accessible via p.scdn.co (no auth required).

8. **ACE-Step 1.5**: Available via fal.ai API ($0.012/generation). Audio-to-audio remix mode works. Quality gate passed (10/10 pairs generated non-silent audio). MIT license, clean training data (licensed/royalty-free/synthetic).

## Technical Environment
- Local: M3 Max MacBook Pro
- GPU: Modal A100 for batch jobs (~$30-50/run)
- Stack: Python + FastAPI + DuckDB + SQLite + FAISS
- Budget: ~$50-100/mo during dev, targeting $0 infrastructure cost

## The Question

Given these primitives, what does an "agentic music curation" product actually look like? We need architecture, not just vision.

Specifically:

1. **What is the product surface?** Desktop app? Browser? CLI? Mobile? What does the user actually interact with? What's the UX paradigm — chat-based (like Cursor's CMD-K), ambient (like a DJ assistant that watches what you play), or something else?

2. **What agent architecture?** Single agent with many tools? Multi-agent with specialized roles? What framework — Claude's tool use, OpenAI function calling, custom MCP server, LangChain/LangGraph, or something simpler? What's the right level of agent autonomy?

3. **What are the agent's tools?** Map the data primitives above to concrete agent capabilities. What tools does the agent need that DON'T exist yet? What's the tool priority order?

4. **How does the taste graph feed into agent decisions?** The taste graph is the moat — 27M transitions that encode what real human curators decided sounds good together. How does this become agent intelligence rather than just a lookup table?

5. **What's the collective intelligence mechanism?** Every user's interactions should make the system smarter for everyone. What's the concrete data loop? How do you avoid cold start?

6. **What's the MVP that proves this works?** What's the smallest thing we can build in 1-2 weeks that demonstrates "Cursor for music" is real and valuable? What's the "holy shit" moment?

7. **What's the moat?** If the agent framework is Claude/GPT + tools, and anyone can build tools, what makes Kyma defensible? Is it just the taste graph data? Is that enough?

8. **How does ACE-Step fit (if at all)?** It's available as a tool. When would an agent choose to use it vs. other approaches (DSP manipulation, finding existing tracks, stem separation)?

9. **What are we NOT thinking about?** What patterns from other agentic products (Cursor, Devin, OpenClaw, Replit Agent) apply to music that nobody is considering?

Give the most rigorous, honest analysis possible. Don't soften critique to be polite. Don't agree unless you genuinely believe it's correct after trying to break it. But don't disagree just to seem thorough — if something is right, explain WHY it's right, which is equally valuable.

Think several levels deeper than the surface question. What upstream assumptions, if wrong, invalidate everything downstream? What would a domain expert with 20 years of experience immediately notice?

Structure your response:
1. IMMEDIATE REACTION (2 sentences — gut before deep analysis)
2. WHAT'S ACTUALLY RIGHT HERE (specific, with reasoning)
3. WHAT'S WRONG OR RISKY (ranked by severity, mechanism of failure)
4. WHAT'S MISSING ENTIRELY (things nobody is asking about)
5. WHAT YOU'D DO INSTEAD (specific, implementable)
6. VERDICT (Go/Modify/No-Go, confidence 0-100, one paragraph)
