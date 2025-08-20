## API Parity Checklist — HTML/HTMX → JSON mappings (Phase 1.1)

Legend: [E] existing JSON endpoint, [N] needed JSON endpoint

### Pages (full HTML routes)
- `/` → renders `pages/index.html` → [N] JSON not required (static shell). If data added later, map accordingly.
- `/dashboard` → `pages/dashboard.html` → aggregates child cards and summaries
  - Children cards: see Components mapping below
  - Allowance summary: see Components mapping below
- `/chores` → `pages/chores.html` → shell; lists use components below
- `/users` → `pages/users.html` → shell; lists/components below
- `/reports` → `pages/reports.html` → shell; components below

### Components and HTML endpoints → JSON parity

1) Children options/cards
   - HTML endpoints:
     - `/api/v1/users/children` (TemplateResponse `components/children_dropdown_options.html`)
     - `/api/v1/users/children-cards` (TemplateResponse `components/children_options.html`)
   - Required fields in template: `child.id`, `child.username`, optional `child.email`
   - JSON mapping: [E] `GET /api/v1/users/children/{parent_id}` returns `List[UserResponse]`
     - Added: [E] `GET /api/v1/users/my-children` (current parent inferred)

2) Parent allowance summary (dashboard)
   - HTML: `/api/v1/users/summary` → `components/allowance_summary.html`
   - Fields used: per child `{ id, username, completed_chores, total_earned, total_adjustments, paid_out, balance_due }`
   - JSON mapping: [E] `GET /api/v1/users/allowance-summary` (JSON) returning list of aggregates per child.

3) Child balance card (child dashboard)
   - HTML: `/api/v1/html/users/me/balance-card` → `components/balance-card.html`
   - Fields used: `{ balance, total_earned, adjustments, paid_out, pending_chores_value }`
   - JSON mapping: [E] `GET /api/v1/users/me/balance` returns `UserBalanceResponse` (already implemented in `main.py`).

4) Chore lists (various)
   - HTML endpoints and templates:
     - `/api/v1/chores` (role-aware, optional filters) → `components/chore_list.html`
     - `/api/v1/html/chores/available` → `components/chore_list.html`
     - `/api/v1/html/chores/active` → `components/chore_list.html`
     - `/api/v1/html/chores/completed` → `components/chore_list.html`
     - `/api/v1/html/chores/pending` → `components/chore_list.html`
     - `/api/v1/html/chores/pending-approval` → `components/chore_list.html`
     - `/api/v1/html/chores/child/{child_id}` → `components/chore_list.html`
     - `/api/v1/html/chores/child/{child_id}/completed` → `components/chore_list.html`
   - Fields used in list/item templates include: `id, title, description, reward, is_range_reward, min_reward, max_reward, cooldown_days, is_completed, is_approved, is_disabled, assignee.username`
   - JSON mapping: [E]
     - `GET /api/v1/chores` (role-aware)
       - Added optional filters: `state=active|completed|pending-approval`, `child_id=<id>` (parent only)
     - `GET /api/v1/chores/available` (child only)
     - `GET /api/v1/chores/pending-approval` (parent only)
     - `GET /api/v1/chores/child/{child_id}` (parent only)
     - `GET /api/v1/chores/child/{child_id}/completed` (parent only)
   - Note: The HTML endpoints do server-side filtering for active/completed views; RN can filter client-side using the existing JSON lists.

5) Chore actions
   - HTML endpoints:
     - POST `/api/v1/chores/{chore_id}/complete` → returns updated `components/chore_item.html`
     - POST `/api/v1/chores/{chore_id}/approve` → returns updated `components/chore_item.html`
     - POST `/api/v1/chores/{chore_id}/disable` → returns updated `components/chore_item.html`
     - POST `/api/v1/chores/{chore_id}/enable` → returns updated `components/chore_item.html`
     - DELETE `/api/v1/chores/{chore_id}` → empty HTML
   - JSON mapping: [E]
     - POST `/api/v1/chores/{chore_id}/complete`
     - POST `/api/v1/chores/{chore_id}/approve` (body: `reward_value` when range)
     - POST `/api/v1/chores/{chore_id}/disable`
     - PUT `/api/v1/chores/{chore_id}` (update)
     - DELETE `/api/v1/chores/{chore_id}`
   - [N] Consider `POST /api/v1/chores/{chore_id}/enable` JSON if RN needs explicit enable; currently only HTML route exists in `main.py`.

6) Chore edit/approve forms (HTML-only)
   - HTML: `/chores/{chore_id}/edit-form`, `/chores/{chore_id}/approve-form` render forms
   - JSON mapping: Forms not needed in RN; RN will render forms client-side and use JSON actions above. No new JSON required.

7) Adjustments (parent)
   - HTML endpoints:
     - `/api/v1/html/adjustments/inline-form/{child_id}` → `adjustments/inline-form.html`
     - `/api/v1/html/adjustments/modal-form/{child_id}` → `adjustments/modal-form.html`
     - `/api/v1/html/adjustments/form` → `adjustments/form.html`
     - `/api/v1/html/adjustments/list/{child_id}` → `adjustments/list.html`
   - JSON mapping: [E]
     - POST `/api/v1/adjustments/` (create)
     - GET `/api/v1/adjustments/child/{child_id}` (list)
     - GET `/api/v1/adjustments/total/{child_id}` (totals)

8) Reset password (parent → child)
   - HTML endpoints: `/api/v1/html/children/{child_id}/reset-password-form`, `/api/v1/direct-reset-password/{child_id}` (testing)
   - JSON mapping: [E] POST `/api/v1/users/children/{child_id}/reset-password`

9) Reports
   - HTML: `/api/v1/reports/potential-earnings` → `components/potential_earnings_report.html`
   - Fields used: per child recurring chores, weekly/monthly potential, counts
   - JSON mapping: [N] add `GET /api/v1/reports/potential-earnings` returning per-child summary or compute on client using existing chores lists. Prefer client-side; add minimal JSON only if needed.

10) Page shells and generic includes
   - `/pages/{page}` and `/components/{component}` are server-rendered conveniences. RN will not use these routes. No JSON required.

### Summary of new JSON endpoints added
- [E] `GET /api/v1/users/my-children` (current parent’s children)
- [E] `GET /api/v1/users/allowance-summary` (parent allowance summary aggregates)
- [N] `POST /api/v1/chores/{chore_id}/enable` (JSON version for enabling chore)
- [N] `GET /api/v1/reports/potential-earnings` (optional; prefer client-side if feasible)

### Acceptance criteria
- Checklist covers all items in `backend/app/templates/**`
- Each HTML route/component mapped to an existing or proposed JSON endpoint with required fields noted
- No behavior changes in this subphase; documentation and mapping only

### Notes
- RN Web should use existing JSON where possible and handle list filtering (active/completed) client-side.
- Any [N] endpoints added in later subphase should use existing repository/service logic and include tests under `backend/tests/`.


