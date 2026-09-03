# Link Relationships v1

Status: prepared and tested on a temporary Neon branch; production apply requires explicit Human Authority approval.

Canonical flow: People → Link Request → Accept/Decline → Link → Link Up.

Accepted `link_requests` rows are the relationship record. Conversation threads continue to be derived from the existing `messages` store; no duplicate `links` or `conversations` table is introduced.

The schema prevents self-requests and duplicate pending/accepted pairs in either direction. Link Request creation also checks the existing Link Up block state before writing.

Production migration must never run at import, GET, startup, or deploy time.