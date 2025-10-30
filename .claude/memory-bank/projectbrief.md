# Project Brief

> **Foundation Document**: This file shapes all other memory bank files. Update this first when project scope or goals change.

## Project Name
Emergency Alerts Integration for Home Assistant

## Purpose
A comprehensive Home Assistant custom integration for managing emergency alerts with hub-based organization, group management, and intuitive status tracking. Makes smart homes safer and more responsive by providing sophisticated alert monitoring with user-friendly interfaces.

## Core Goals
1. **User-Friendly Alert Management**: Provide intuitive UI for creating, editing, and managing emergency alerts without requiring YAML knowledge
2. **Flexible Monitoring**: Support multiple trigger types (simple entity, Jinja2 templates, logical conditions) for diverse use cases
3. **Organization**: Hub-based architecture with global settings and custom alert groups for clean device hierarchy
4. **Status Tracking**: Comprehensive lifecycle tracking with acknowledge, clear, and escalate actions

## Scope
### In Scope
- Hub-based organization (Global Settings Hub, Alert Group Hubs)
- Multiple trigger types (simple, template, logical with visual condition builder)
- Alert severity levels (critical, warning, info)
- Status sensors with full lifecycle tracking
- Action buttons (acknowledge, clear, escalate)
- Multi-step configuration UI with progressive disclosure
- Device hierarchy with proper Home Assistant integration
- Service calls for automation integration
- HACS compliance and distribution

### Out of Scope
- Frontend Lovelace card (separate component, may be integrated later)
- Mobile app push notifications (handled via Home Assistant notification services)
- Alert history database (relies on Home Assistant's history)
- External integrations beyond Home Assistant services
- Multi-language support beyond English (infrastructure exists, translations not implemented)

## Success Criteria
- Integration installs cleanly via HACS
- Users can create alerts through UI without touching YAML
- All trigger types work reliably
- Status tracking reflects actual alert states accurately
- Device hierarchy displays cleanly in Home Assistant
- Test coverage >90% maintained
- No critical bugs in alert evaluation logic

## Constraints
- **Technical**: Must comply with Home Assistant integration standards and best practices
- **Platform**: Python 3.9+, Home Assistant Core 2023.x+
- **Dependencies**: Zero external dependencies (pure Home Assistant integration)
- **AI-Assisted**: Project developed with AI assistance (Claude/Cursor) - may contain inconsistencies, use with awareness
- **Maintainer**: Single maintainer (issmirnov) with limited deep codebase knowledge

## Key Stakeholders
- **Primary Users**: Home Assistant users wanting sophisticated alert monitoring
- **Maintainer**: @issmirnov (project owner, limited direct coding experience)
- **Decision Maker**: @issmirnov with heavy AI assistant collaboration
- **Community**: Home Assistant community for feedback and contributions

## Context
This project serves as both a practical home automation tool and an experiment in AI-assisted software development. The maintainer is using this project to learn about Home Assistant integration development while creating a genuinely useful component. The codebase has evolved through multiple phases from simple alerts to sophisticated hub-based architecture with visual form builders. Recent focus has been on defensive coding, cleanup of legacy patterns, and establishing memory bank for better AI collaboration context.
