# Diagnostic Report: Streamlit Process Crash

## A. Root Cause
The Streamlit "Oh no. Error running app" crash after pipeline execution is caused by a catastrophic combination of **$O(N^2)$ memory explosion** in the `CandidateFactMatcher` and **Streamlit WebSocket/DOM overload** due to unbatched `st.markdown` calls inside `for` loops.

When a user uploads realistic or edge-case PDFs, they can easily yield thousands of generic "NUMERICAL" facts. 
1. `candidate_matcher.py` buckets these facts. If a single bucket gets 5,000 facts, the nested `for i in range... for j in range(i+1...` loop executes **12.5 million times**, allocating millions of dictionary references in RAM, spiking RSS memory until the OS triggers an OOM kill.
2. If it survives the OOM kill, `app.py` iterates over all these relationships and calls `st.markdown(card_html, unsafe_allow_html=True)` individually for each. Streamlit's architecture sends each `st.markdown` as a separate protobuf message over WebSockets. Sending tens of thousands of WebSocket messages instantly overwhelms the Tornado server buffer and crashes the browser frontend, causing the "Oh no" disconnect error.

## B. Evidence
1. **Unbounded $O(N^2)$ Loop**: `backend/app/pipeline/candidate_matcher.py` lines 21-41 groups facts by predicate, but has no upper limit on bucket size. A 100-page PDF could generate 2,000 facts in a single generic bucket, resulting in 2M iterations.
2. **Memory Amplification**: `relationship_engine.py` creates a brand new dictionary with multiple lists/strings for *every* candidate pair.
3. **WebSocket Overload**: `app.py` lines 490-493 loop over `items` (which could be thousands of elements) and call `st.markdown` for each, rather than joining the HTML strings into a single call.

## C. Confidence
**95% Confidence.** The architectural pattern of looping `st.markdown` and unbounded $O(N^2)$ pairwise combination is a classic and proven cause of Streamlit stability failures (both OOM backend crashes and browser frontend crashes). 

## D. Secondary issues
- Missing GC (Garbage Collection) hints for the spaCy native memory objects (`doc = nlp(text)`).
- `st.session_state` retains these massive lists indefinitely if they aren't explicitly cleared on reset.

## E. Minimal fix
1. **Bound the $O(N^2)$ Combinatorics:** In `candidate_matcher.py`, cap `bucket_facts` to a reasonable limit (e.g., max 200 items per bucket) before the pairwise loop to prevent CPU/RAM explosions.
2. **Batch HTML Rendering:** In `app.py`, join all the `card_html` strings into a single array and call `st.markdown("".join(all_cards_html))` exactly once per tab.
3. **Paginate Frontend:** In `app.py`, enforce a maximum display limit (e.g., render only the top 100 facts/relationships) to prevent browser DOM crashes.

## F. Production fix
For true production readiness:
- Move the O(N^2) candidate matching and relationship evaluation to a background Celery worker or FastAPI subprocess.
- Store results in a lightweight SQLite database instead of passing gigabytes of lists through Streamlit's memory.
- Use native pagination components (e.g., `streamlit-aggrid` or custom React component) to render results lazily.

## G. Verification
1. I will implement the minimal safe fix.
2. Upload the edge-case PDF generated in `debug_crash2.py` (which creates generic numerical buckets).
3. Verify that the Streamlit process stays below 300MB RAM and that the UI renders instantly without disconnecting.

## H. Files to change
- `backend/app/pipeline/candidate_matcher.py` (Lines 21-23: Add `bucket_facts = bucket_facts[:150]`)
- `app.py` (Lines 440-548: Add `max_display` limits and batch `st.markdown` calls by joining arrays)
