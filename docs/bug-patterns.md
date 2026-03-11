# Bug Pattern Registry

Review agents should consult this file when reviewing code to check for known bug patterns.

---

### Orphaned Component — 2026-03-10

**Bug**: `OrgHomePage` component existed in `pages/OrgHomePage.tsx` but was never registered as a route in `app.tsx`. Clicking an org card on the homepage navigated to `/:orgSlug` which had no matching route.

**Root cause**: Component was created but the route registration step was missed. No check verified that every page component has a corresponding route.

**Prevention rule**: Spec compliance now verifies that every component in `pages/` is registered in the router, and every route has an inbound navigation link.

**Skill updated**: `/spec-compliance` — added "orphaned component" check

---

### Broken API Contract (Response Shape) — 2026-03-10

**Bug**: `OrgHomePage.fetchTypeEntities()` called `api.get<EntityRecord[]>()` expecting a bare array, but the API returns `{ entities: [...], pagination: {...} }`. The auto-unwrap in `api.ts` only handles single-key wrapper objects; this has 2 keys so it's returned as-is.

**Root cause**: Developer assumed the API response shape without verifying. The auto-unwrap behaviour is implicit and easy to get wrong — single-key objects unwrap, multi-key objects don't.

**Prevention rule**: Implementation and review agents must verify API response shapes by reading the actual route handler, and check that the frontend's type annotation matches what `handleResponse` will actually return after auto-unwrap logic.

**Skill updated**: `/implement` — added API contract verification step; `/review` — Architecture agent checks response shape alignment

---

### ID/Slug Confusion — 2026-03-10

**Bug**: `GET /organisations/:org` endpoint used `getOrganisation(db, orgId)` which only looks up by ID. But the frontend constructs URLs using the org slug (e.g., `/organisations/e2e-test-org`), so the lookup always failed.

**Root cause**: The `orgGuard` middleware correctly resolves by slug-then-ID, but the standalone GET endpoint didn't follow the same pattern.

**Prevention rule**: Any API endpoint that accepts a `:org`, `:type`, or similar URL parameter must resolve by slug first, then ID — matching the `orgGuard` pattern. Review agents should flag any direct `getById()` call on a URL parameter.

**Skill updated**: `/review` — Security agent checks URL param resolution consistency

---

### Missing Form Binding (Stale Props) — 2026-03-10

**Bug**: `EntityFormCore` always read field values from `entity?.fields ?? {}`. In create mode, `entity` is null, so the form always displayed empty values. When the user typed, `onChange` updated the parent's signal, but the form re-rendered with the same empty object — user input appeared to have no effect.

**Root cause**: The form component was designed for edit mode (where `entity` has data) and reused for create mode without providing a way to pass live form values. The component used a derived value instead of accepting controlled input.

**Prevention rule**: Any form component used in both create and edit modes must accept a `values` prop (or equivalent) for controlled input. Review agents should verify that form components display the same values the parent passes via onChange.

**Skill updated**: `/review` — Architecture agent checks form component controlled vs uncontrolled binding

---

### Missing System Field in UI — 2026-03-10

**Bug**: The entity create page had no input for the `name` field. The API requires `name` as a top-level system field, but the form only rendered custom fields from the entity type definition. The create function tried `formFields.value['name']` which was always empty.

**Root cause**: The `name` field is a system field (not part of the entity type's `fields` array), so the dynamic field renderer never included it. No one verified that the create form provides all required API fields.

**Prevention rule**: When building a create/edit form, verify that every required field in the API schema (Zod schema) has a corresponding UI input — including system fields like `name`, `slug`, etc. that aren't part of the dynamic field definitions.

**Skill updated**: `/spec-compliance` — added API schema vs UI form cross-check

---

### Broken Link Construction — 2026-03-10

**Bug**: `OrgHomePage` constructed entity links as `/${type.slug}/${entity.slug}` instead of `/${orgSlug}/${type.slug}/${entity.id}`. Two errors: missing org slug prefix, and using entity slug instead of ID.

**Root cause**: Links were written by pattern-guessing instead of reading the actual route definitions in `app.tsx`.

**Prevention rule**: Spec compliance verifies that every `href` in the codebase matches a defined route pattern. Implementation agents must read the router when constructing links.

**Skill updated**: `/spec-compliance` — added link-to-route validation
