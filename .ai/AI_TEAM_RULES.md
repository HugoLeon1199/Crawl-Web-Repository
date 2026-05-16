# AI Team Rules

This repository is developed using a multi-AI workflow.

## Roles

- Leon = Product Owner and final approver.
- ChatGPT/GPT = Architect, Reviewer, Technical Mentor, Strategic Advisor, and GitHub review-file writer.
- Gemini = Independent Reviewer, Red-Team Critic, Research Partner. Gemini may read the repository and produce review text, but may not be able to write files directly.
- Cursor = Implementation Engineer and primary code writer.
- GitHub = Source of Truth.

## Core Workflow

1. Leon defines the goal or task.
2. GPT/Gemini analyze, review, and propose direction.
3. Cursor implements inside the repository.
4. Cursor writes an implementation report.
5. GPT reviews the repository and Cursor report.
6. Gemini reviews independently and challenges assumptions.
7. Leon sends Gemini's review text back to GPT if Gemini cannot write to GitHub.
8. GPT synthesizes the reviews.
9. Cursor patches the code if needed.
10. Leon approves or rejects.
11. Important decisions are documented.

## Source of Truth

The GitHub repository is the source of truth. Do not rely on memory if the file can be inspected.

## Safety Rules

- Do not commit secrets, API keys, tokens, passwords, cookies, or private credentials.
- Do not hardcode private machine paths.
- Do not bypass CAPTCHA, paywalls, login systems, access controls, robots restrictions, or platform policies.
- Do not run destructive commands without Leon's approval.
- Do not rewrite unrelated code.
- Do not make large architecture changes unless explicitly requested.
- Prefer small, safe, testable changes.

## Required Task Metadata

Every serious task should include:

- goal
- input
- expected output
- relevant files
- constraints
- acceptance criteria
- test plan
- risks
- rollback plan

## Required Implementation Report

After implementation, Cursor must report:

- files created
- files modified
- what changed
- how to run
- how to test
- known limitations
- notes for GPT review
- notes for Gemini review

## Required Review Format

GPT and Gemini should review with:

- verdict
- facts
- high severity issues
- medium severity issues
- low severity issues
- recommendations
- test plan
- merge checklist

## File Ownership

Cursor may write:

- `01_CURSOR_IMPLEMENTATION_REPORT.md`
- `05_CURSOR_PATCH_REPORT.md`

GPT may write:

- `02_GPT_REVIEW.md`
- `04_REVIEW_SYNTHESIS.md`
- `03_GEMINI_REVIEW.md` only when Leon provides Gemini's review text and asks GPT to archive it.

Gemini may produce content for:

- `03_GEMINI_REVIEW.md`

Leon may write:

- `06_LEON_FINAL_DECISION.md`

No AI should overwrite another AI's review file unless Leon explicitly asks.
