# Functional Specification

Derived from read-only analysis of `/Users/timfrench/labels/1c-portal-v2`.
This document describes WHAT the system does — not how it should be built.

## System Overview

A multi-tenant content management platform where organisations create, manage, and publish structured content entities with role-based access control, approval workflows, and real-time collaboration.

## Core Capabilities

### 1. Entity Management
- **Custom entity types** defined by superadmin (e.g. "Article", "Event", "Profile")
- Each type has configurable fields (text, number, date, select, file, markdown, link, etc.)
- Entities follow a **state lifecycle**: `draft → pending → published → archived → deleted`
- **Composite keys** `${entityId}:${state}` allow same entity in multiple states simultaneously
- **Slug uniqueness** per org+type namespace
- **Version history**: every publish creates a numbered snapshot
- **JSON Patch** operations for entity updates
- **Soft delete** with `deletedAt` timestamp

### 2. Multi-Tenancy (Organisations)
- Platform hosts multiple organisations, each isolated
- Org resolved by slug (e.g. `/my-org/articles/...`)
- Users can belong to multiple organisations
- Org-level settings and branding
- Organisation types (singleton entity per org with `isOrgType: true`)

### 3. Authentication
- **Passwordless magic link** login flow:
  1. User submits email → magic link emailed (10 min TTL)
  2. User clicks link → JWT session created (7 day TTL)
- Sessions are **org-agnostic** (user accesses any org they belong to)
- Auto-create user entity on first login
- Domain whitelisting for self-signup

### 4. Authorization & Access Control
- **Roles**: superadmin, org_admin, org_member, public (unauthenticated)
- **CASL-based** rule engine with conditions and interpolation
- **Field-level access**: each field defines `access.read` and `access.write` arrays of group names
- **Entity type visibility**: `visibleTo` controls who can see a type, `addableBy` controls who can create
- **Membership groups**: dynamic groups (public, org:{orgId}, authenticated, custom)
- **Membership keys**: configurable tiers per org with capabilities and rate limits
- Server-side enforcement: `filterForRead()` strips fields, `filterPatchOperations()` drops disallowed writes
- Frontend role checks are UI-only decoration — backend enforces independently

### 5. Real-Time Sync
- **WebSocket per group** (public, org:xyz) for live updates
- Message types: entity-update, entity-remove, config-update, me-update, catch-up, comment-update
- **Three-layer cache** for HTTP collection endpoint:
  - L1: Full assembled file (rebuilt infrequently)
  - L2: Delta file (written after 5s debounce)
  - L3: Authoritative storage (newest data, used for WS catch-up)
- **Offline-first**: local persistence, instant load from cache, network sync in background
- **ETag-based** conditional requests with per-group ETags (content hash)
- Connected: WS only, no polling. Disconnected: poll every 60s fallback.

### 6. Config Management
- Unified config with sections: entityTypes, branding, security, workflow, groups, membershipKeys, homepage, emailTemplates, ai
- Per-section visibility (public, orgMember, orgAdmin)
- Config versioning with archive/restore
- Config updates propagated immediately via WS

### 7. Workflow & Approval
- Configurable state machine (states + transitions)
- Transitions have: from/to state, allowedRoles, conditions (field_required, time_elapsed), hooks
- Approval queue for pending entities

### 8. Comments & Collaboration
- Entity-level comments with real-time delivery via WS
- Comment events stored in R2, pending events in DO
- Resolved into comment tree structure

### 9. File Management
- File upload/download with signature-based auth
- Files attached to entity fields
- Branding assets (logo, favicon) served publicly
- Entity files served with access control

### 10. Import/Export
- Bulk export all data as ZIP (superadmin)
- Bulk import from ZIP with validation
- Uses same code path as regular creation (same validation)

### 11. Audit Logging
- All mutations logged with: actor, action, resource, status, metadata (IP, user-agent)
- Queryable by org, date range, action prefix, actor
- Events stored by org and date for efficient pagination

### 12. AI Chat
- Embedded Claude API proxy with membership group access control
- System prompt from config + frontend context
- Web search tool included

### 13. Public Access
- Published entities viewable without auth via public routes
- SEO: sitemap.xml, robots.txt
- Public entity listings and detail pages
- Bootstrap script for first-paint branding

### 14. Analytics
- Cloudflare Web Analytics integration
- Dashboard in superadmin UI

## API Surface (All Endpoints)

### Auth
- `POST /login` — request magic link
- `POST /login/verify` — exchange token for session
- `POST /logout` — revoke session

### Current User
- `GET /me` — user profile + memberships
- `GET /me/profile` — enriched profile
- `PATCH /me` — update profile
- `POST /me/alerts/subscribe` — subscribe to entity updates

### Entities
- `POST /organisations/:org/:type` — create
- `GET /organisations/:org/:type/:id` — read (with optional state param)
- `PATCH /organisations/:org/:type/:id` — update (JSON Patch)
- `POST /organisations/:org/:type/:id/publish` — publish
- `POST /organisations/:org/:type/:id/transition` — workflow transition
- `DELETE /organisations/:org/:type/:id` — soft delete
- `GET /organisations/:org/:type/by-slug/:slug` — resolve by slug

### Versions
- `GET /organisations/:org/:type/:id/versions` — history
- `GET /organisations/:org/:type/:id/versions/:v` — specific version

### Comments
- `GET /organisations/:org/:type/:id/comments` — list
- `POST /organisations/:org/:type/:id/comments` — add
- `DELETE /organisations/:org/:type/:id/comments/:cid` — delete

### Collections
- `GET /collection?group=X` — assembled collection with ETag support

### Config
- `GET /config` — current config (filtered by viewer groups)
- `POST /config` — update config
- `GET /config/versions` — version history
- `POST /config/versions/:v/restore` — restore version

### Organisations
- `GET /organisations` — list all
- `GET /organisations/:org` — get org
- `GET /organisations/by-slug/:slug` — resolve slug
- `POST /organisations` — create (superadmin)
- `PATCH /organisations/:org` — update
- `POST /organisations/:org/members` — invite
- `GET /organisations/:org/members` — list members
- `DELETE /organisations/:org/members/:uid` — remove

### Files
- `GET /files/:id` — download
- `POST /files` — upload
- `DELETE /files/:id` — delete
- `GET /files/branding/*` — public branding assets

### Admin
- `GET /admin/cache/status` — cache stats
- `POST /admin/cache/rebuild` — rebuild cache
- `GET /admin/audit` — audit log
- `GET /organisations/:org/audit` — org audit log

### Backup
- `GET /backup` — export ZIP
- `POST /backup/restore` — import ZIP

### Chat
- `POST /chat` — AI chat proxy

### WebSocket
- `GET /ws/collection?group=X&token=Y` — real-time updates

### Public
- `GET /sitemap.xml` — sitemap
- `GET /robots.txt` — robots
- `GET /:orgSlug/:type` — public listing
- `GET /:orgSlug/:type/:slug` — public detail

### Health
- `GET /` — health check
- `GET /bootstrap.js` — first-paint branding script

## Field Types
text, longText, textarea, select, multiselect, number, boolean, date, dateTime, link, markdown, html, file, section (UI grouping)

## Entity System Fields
id, type, orgId, slug, state, version, createdAt, createdBy, updatedAt, updatedBy, deletedAt, _draftChanges, _versionHistory
