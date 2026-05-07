# Alembic Migration Traceability

Auto-generated traceability matrix for all database migrations.

| Rev ID | File | Action | Date | Description | Down Revision |
|--------|------|--------|------|-------------|---------------|
| 0a1b2c3d4e5f | `0a1b2c3d4e5f_add_quiz_engine_assignment_fields.py` | add | 2026-03-27 | G20 — Add quiz engine tables and assignment quiz fields. | ? |
| 0a31b2c3d4e5 | `0a31b2c3d4e5_alter_school_model_mixins.py` | alter | 2026-03-29 | G31a — School model and school_id foreign keys. | ? |
| 0d4e5f6a7b8c | `0d4e5f6a7b8c_index_legacy_fk_indexes.py` | index | 2026-04-05 | G37b - add missing FK indexes for legacy tables. | ? |
| 1b2c3d4e5f6a | `1b2c3d4e5f6a_add_content_library_models.py` | add | 2026-03-27 | G21 — Add content library fields and models. | ? |
| 1c42d3e4f5a6 | `1c42d3e4f5a6_alter_pg_enum_columns.py` | alter | 2026-03-29 | G31b — convert string-backed status/type columns to PostgreSQL enums. | ? |
| 2c3d4e5f6a7b | `2c3d4e5f6a7b_add_notifications_center.py` | add | 2026-03-27 | G22 — Phase 13 notification center. | ? |
| 2e4f6a8b0c1d | `2e4f6a8b0c1d_add_micro_ecole_models.py` | add | 2026-04-03 | G32a — micro-school models and EDUCATOR role support. | ? |
| 3d4e5f6a7b8c | `3d4e5f6a7b8c_add_reports_analytics.py` | add | 2026-03-27 | G23 — Phase 14 reports and analytics. | ? |
| 4c6d8e0f1a2b | `4c6d8e0f1a2b_add_class_micro_budget.py` | add | 2026-04-04 | G32b - class micro-budget models. | ? |
| 4e5f6a7b8c9d | `4e5f6a7b8c9d_add_calendar_events.py` | add | 2026-03-27 | G24 — Phase 15 calendar and events. | ? |
| 5d8e9f0a1b2c | `5d8e9f0a1b2c_add_life_skills_passport.py` | add | 2026-04-04 | G33a - life skills passport models. | ? |
| 5f6a7b8c9d0e | `5f6a7b8c9d0e_add_document_management.py` | add | 2026-03-27 | G25 — Phase 16 document management. | ? |
| 6a7b8c9d0e1f | `6a7b8c9d0e1f_add_admin_content_manager_profiles.py` | add | 2026-03-28 | G26 — OOP admin and content manager profile tables. | ? |
| 6d3f2a91b4c8 | `6d3f2a91b4c8_add_student_rewards.py` | add | 2026-04-13 | g42 student rewards | a81c9e4f2b7d |
| 6f0a1b2c3d4e | `6f0a1b2c3d4e_add_men_compliance_checker.py` | add | 2026-04-04 | G34a - MEN compliance checker models. | ? |
| 72e15d401f00 | `72e15d401f00_add_academic_snapshots.py` | add | 2026-04-28 | g50c academic_snapshots (Phase 3.3). | ab873f7d5708 |
| 748989a9f381 | `748989a9f381_add_eligibility_rules.py` | add | 2026-04-28 | g50d eligibility_rules (Phase 3.4). | 72e15d401f00 |
| 7a1b2c3d4e5f | `7a1b2c3d4e5f_add_local_first_sync.py` | add | 2026-04-04 | G35a - local-first sync models. | ? |
| 7b8c9d0e1f2a | `7b8c9d0e1f2a_add_iam_impersonation_login_history.py` | add | 2026-03-28 | G27a — IAM impersonation, login history, and session limits. | ? |
| 8670b612eb3e | `8670b612eb3e_add_upload_sessions.py` | add | 2026-05-05 | G51 — Phase 8: upload_sessions table for direct-to-MinIO uploads. | ? |
| 8b2c3d4e5f6a | `8b2c3d4e5f6a_add_financial_health_dashboard.py` | add | 2026-04-05 | G36a - financial health dashboard models. | ? |
| 8c9d0e1f2a3b | `8c9d0e1f2a3b_add_rubric_engine_models.py` | add | 2026-03-28 | G28a — Rubric engine models and assignment linkage. | ? |
| 9c3d4e5f6a7b | `9c3d4e5f6a7b_index_missing_fk_indexes.py` | index | 2026-04-05 | G37a - add missing FK indexes for innovation feature tables. | ? |
| 9d0e1f2a3b4c | `9d0e1f2a3b4c_add_weighted_gradebook_models.py` | add | 2026-03-28 | G28b — Weighted gradebook models and assignment linkage. | ? |
| 9d9968735a7b | `9d9968735a7b_add_program_management_history.py` | add | 2026-04-28 | g49 program management and student academic history | f4e5d6c7b8a9 |
| 9f7257bc8dd1 | `9f7257bc8dd1_create_schema_iam_erp_lms_com_billing_audit.py` | create | 2026-03-15 | G1-G6 initial schema: IAM, ERP, LMS, COM, Billing, Audit | ? |
| a1b2c3d4e5f6 | `a1b2c3d4e5f6_add_pdf_exercise_workflow.py` | add | 2026-03-22 | G13 — Phase 9C: PDF exercise workflow fields. | f7a8b9c0d1e2 |
| a1b2c3d4e5f7 | `a1b2c3d4e5f7_add_invoice_pdf_banking_details.py` | add | 2026-05-05 | G50E — Invoice PDF Banking Details & TVA Fields. | 8670b612eb3e |
| a2f8b3c4d5e6 | `a2f8b3c4d5e6_add_ai_writing_preferences.py` | add | 2026-03-15 | G7: AI — writing_attempts + ai_preferences tables. | 9f7257bc8dd1 |
| a3b4c5d6e7f8 | `a3b4c5d6e7f8_add_difficulty_adaptations.py` | add | 2026-04-19 | h2 difficulty adaptations table | f6e5d4c3b2a1 |
| a81c9e4f2b7d | `a81c9e4f2b7d_add_story_content_fields.py` | add | 2026-04-13 | g41 story content fields | d4a1f0c8b2e7 |
| a8b9c0d1e2f3 | `a8b9c0d1e2f3_add_timetable_slots_exceptions.py` | add | 2026-03-22 | G14: Timetable slots + exceptions (Phase 11A) | a1b2c3d4e5f6 |
| ab1c2d3e4f56 | `ab1c2d3e4f56_add_question_bank_items.py` | add | 2026-03-28 | G28c — Question bank items. | ? |
| ab873f7d5708 | `ab873f7d5708_add_program_equivalences.py` | add | 2026-04-28 | g50b program_equivalences (Phase 3.2). | cb375ca25f1b |
| b2c3d4e5f6a7 | `b2c3d4e5f6a7_index_attendance_performance_indexes.py` | index | 2026-05-06 | G51a — Attendance Performance Indexes. | a1b2c3d4e5f7 |
| b3c4d5e6f7a8 | `b3c4d5e6f7a8_add_parent_child_links_views_kpi.py` | add | 2026-03-15 | G8: Phase 1A — parent_child_links table, views, mv_kpi_daily. | a2f8b3c4d5e6 |
| b544b2132f31 | `b544b2132f31_constraint_grade_range_check_constraints.py` | constraint | 2026-04-05 | g38 add grade 0-20 CHECK constraints. | ? |
| b71f4d2c8e9a | `b71f4d2c8e9a_add_game_config.py` | add | 2026-04-13 | g43 game config | 6d3f2a91b4c8 |
| b9c0d1e2f3a4 | `b9c0d1e2f3a4_add_fee_structures_billing_enhancements.py` | add | 2026-03-22 | G15: Fee structures, assignments, payment retry + reminder fields (Phase 11B) | a8b9c0d1e2f3 |
| bc2d3e4f5a67 | `bc2d3e4f5a67_add_late_submission_penalties.py` | add | 2026-03-28 | G28d — Late submission penalty columns on assignments and grades. | ? |
| c0d1e2f3a4b5 | `c0d1e2f3a4b5_add_messaging_announcements.py` | add | 2026-03-22 | G16: Conversations, messages, read receipts, announcements (Phase 11C) | b9c0d1e2f3a4 |
| c4d5e6f7a8b9 | `c4d5e6f7a8b9_add_session_device_info_password_policy.py` | add | 2026-03-15 | G9: Phase 2A — Session device info columns for session management. | b3c4d5e6f7a8 |
| c7d8e9f0a1b2 | `c7d8e9f0a1b2_add_longest_streak.py` | add | 2026-04-17 | g47 add longest_streak to student_rewards | f6e5d4c3b2a1 |
| c9d5e3f7a1b4 | `c9d5e3f7a1b4_index_remaining_fk_indexes.py` | index | 2026-04-05 | g39 add remaining FK indexes. | ? |
| cb375ca25f1b | `cb375ca25f1b_add_program_versions.py` | add | 2026-04-28 | g50a program_versions — promote the lightweight version_label shim into a | 9d9968735a7b |
| cd3e4f5a6b78 | `cd3e4f5a6b78_add_billing_policies_payment_plans.py` | add | 2026-03-28 | G27b — Billing sibling discounts, late fees, and payment plans. | ? |
| d1e2f3a4b5c6 | `d1e2f3a4b5c6_add_feature_toggles.py` | add | 2026-03-23 | G17: Feature toggles table (Phase 11E) | c0d1e2f3a4b5 |
| d4a1f0c8b2e7 | `d4a1f0c8b2e7_index_residual_fk_indexes.py` | index | 2026-04-05 | g40 add residual FK indexes | c9d5e3f7a1b4 |
| d4c8f1a7e2b3 | `d4c8f1a7e2b3_add_story_page_fields.py` | add | 2026-04-13 | g44 story page fields | b71f4d2c8e9a |
| d5e6f7a8b9c0 | `d5e6f7a8b9c0_add_totp_2fa_email_verification.py` | add | 2026-03-15 | G10: Phase 2B — TOTP 2FA columns and email verification on users table. | c4d5e6f7a8b9 |
| d8e9f0a1b2c3 | `d8e9f0a1b2c3_add_reward_badges.py` | add | 2026-04-18 | g47b reward badges | c7d8e9f0a1b2 |
| d9e8f7a6b5c4 | `d9e8f7a6b5c4_add_absence_justification_attachment.py` | add | 2026-04-20 | i4 absence justification attachment url | a3b4c5d6e7f8 |
| de4f5a6b7c89 | `de4f5a6b7c89_add_attendance_alerts.py` | add | 2026-03-28 | G29a — Attendance analytics alerts. | ? |
| e2f3a4b5c6d7 | `e2f3a4b5c6d7_alter_role_code_columns.py` | alter | 2026-03-27 | G18 — Expand IAM role code columns for CONTENT_MGR. | ? |
| e45b7c9a1d2f | `e45b7c9a1d2f_alter_story_content_item_types.py` | alter | 2026-04-14 | g45 align story content item types | d4c8f1a7e2b3 |
| e6f7a8b9c0d1 | `e6f7a8b9c0d1_index_gin_indexes_fulltext_search.py` | index | 2026-03-20 | G11 — GIN indexes for full-text search (Phase 3D). | d5e6f7a8b9c0 |
| e9f0a1b2c3d4 | `e9f0a1b2c3d4_add_max_consecutive_timetable_constraints.py` | add | 2026-04-18 | g48 add max_consecutive_classes timetable constraint type | d8e9f0a1b2c3 |
| ef5a6b7c8d90 | `ef5a6b7c8d90_add_timetable_generation_constraints.py` | add | 2026-03-28 | G29b — Timetable constraints and generation jobs. | ? |
| f061728394a1 | `f061728394a1_index_message_attachments_search.py` | index | 2026-03-28 | G30a — Message attachments and full-text search index. | ? |
| f1728394a5b6 | `f1728394a5b6_add_document_versions.py` | add | 2026-03-28 | G30b — Document version history. | ? |
| f28394a5b6c7 | `f28394a5b6c7_add_report_schedules.py` | add | 2026-03-28 | G30c — Report schedules. | ? |
| f3a4b5c6d7e8 | `f3a4b5c6d7e8_add_teacher_reward_points.py` | add | 2026-03-27 | G19 — Add reward_points to teacher_profiles. | ? |
| f4e5d6c7b8a9 | `f4e5d6c7b8a9_merge_g48_i4_heads.py` | merge | 2026-04-27 | merge g48 and i4 migration heads | e9f0a1b2c3d4 |
| f6e5d4c3b2a1 | `f6e5d4c3b2a1_add_level_age_mappings.py` | add | 2026-04-17 | g46 level age mappings | e45b7c9a1d2f |
| f7a8b9c0d1e2 | `f7a8b9c0d1e2_add_role_specific_profiles.py` | add | 2026-03-21 | G12 — Role-specific profile tables + invitation target_student_id (Phase 1B). | e6f7a8b9c0d1 |

## Statistics

- **Total migrations**: 65
- **Actions**: add (51), alter (4), constraint (1), create (1), index (7), merge (1)
- **Date range**: 2026-03-15 → 2026-05-06

## Naming Convention

All files follow: `{12-char-revision}_{action}_{description}.py`

| Action | Meaning | Count |
|--------|---------|-------|
| `create` | Initial schema creation | 1 |
| `add` | Add tables, columns, or features | 51 |
| `alter` | Modify existing schema | 4 |
| `index` | Add indexes for performance | 7 |
| `constraint` | Add check constraints | 1 |
| `merge` | Merge parallel migration branches | 1 |

## How to Update

This file is generated from migration docstrings. To regenerate:

```bash
cd backend/alembic/versions
python3 << 'EOF'
# (see script in repository)
EOF
```
