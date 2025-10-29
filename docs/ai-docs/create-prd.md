# Rule: Generating a Product Requirements Document (PRD)

## Goal

To guide an AI assistant in creating a detailed Product Requirements Document (PRD) in Markdown format, based on an initial user prompt. The PRD should be clear, actionable, and suitable for a junior developer to understand and implement the feature.

## Process

1. **Receive Initial Prompt:** The user provides a brief description or request for a new feature or functionality. It could be a few lines, or a github issue.
2. ** Get a perspective on the project by reading details from Readme.md, Claude.md, docs/, the last 5 PRs in github, and any logged github issues 
3. ** Ask Clarifying Questions:** Before writing the PRD, the AI *must* ask clarifying questions to gather sufficient detail. The goal is to understand the "what" and "why" of the feature, not necessarily the "how" (which the developer will figure out).
4. ** Generate PRD:** Based on the initial prompt and the user's answers to the clarifying questions, generate a PRD using the structure outlined below.
5. ** Save PRD:** Create a new feature directory `docs/features/[feature-name]-PLANNED/` and save the generated document as `prd.md` inside that directory.

## Status Management
- **PLANNED**: Feature is documented but not yet started
- **IN_PROGRESS**: Feature is being actively developed
- **COMPLETED**: Feature is fully implemented and deployed

Rename the directory to reflect current status (e.g., `user-auth-PLANNED` → `user-auth-IN_PROGRESS` → `user-auth-COMPLETED`).

## Clarifying Questions (Examples)

The AI should adapt its questions based on the prompt, but here are some common areas to explore:

*   **Problem/Goal:** "What problem does this feature solve for the user?" or "What is the main goal we want to achieve with this feature?"
*   **Target User:** "Who is the primary user of this feature?"
*   **Core Functionality:** "Can you describe the key actions a user should be able to perform with this feature?"
*   **User Stories:** "Could you provide a few user stories? (e.g., As a [type of user], I want to [perform an action] so that [benefit].)"
*   **Acceptance Criteria:** "How will we know when this feature is successfully implemented? What are the key success criteria?"
*   **Scope/Boundaries:** "Are there any specific things this feature *should not* do (non-goals)?"
*   **Data Requirements:** "What kind of data does this feature need to display or manipulate?"
*   **Design/UI:** "Are there any existing design mockups or UI guidelines to follow?" or "Can you describe the desired look and feel?"
*   **Edge Cases:** "Are there any potential edge cases or error conditions we should consider?"
*   **Platforms:** Will this be used on desktop, phone and tablet?

## PRD Structure Options

### Option 1: Standard PRD Structure

The generated PRD should include the following sections:

1.  **Introduction/Overview:** Briefly describe the feature and the problem it solves. State the goal.
2.  **Goals:** List the specific, measurable objectives for this feature.
3.  **User Stories:** Detail the user narratives describing feature usage and benefits.
4.  **Functional Requirements:** List the specific functionalities the feature must have. Use clear, concise language (e.g., "The system must allow users to upload a profile picture."). Number these requirements.
5.  **Non-Goals (Out of Scope):** Clearly state what this feature will *not* include to manage scope.
6.  **Design Considerations (Optional):** Link to mockups, describe UI/UX requirements, or mention relevant components/styles if applicable.
7.  **Technical Considerations (Optional):** Mention any known technical constraints, dependencies, or suggestions (e.g., "Should integrate with the existing Auth module").
8.  **Success Metrics:** How will the success of this feature be measured? (e.g., "Increase user engagement by 10%", "Reduce support tickets related to X").
9.  **Open Questions:** List any remaining questions or areas needing further clarification.

### Option 2: Comprehensive Engineering PRD Structure

For complex technical features or when requested by the user, use this more detailed structure:

1.  **Overview:** Brief feature description and problem it solves
2.  **Problem Statement:** Detailed context and justification
3.  **Goals:** Organized into Primary and Secondary goals
4.  **Success Criteria:** Specific, measurable checkboxes for validation
5.  **Requirements:** Subdivided into:
    - **Functional Requirements** (numbered, specific features)
    - **Technical Requirements** (numbered, system/environment needs)
    - **Non-Functional Requirements** (numbered, performance/security/maintainability)
6.  **User Stories:** Organized by persona/role
7.  **Technical Specifications:** Include code examples, configurations, API specs
8.  **Dependencies:** Split into External and Internal dependencies
9.  **Timeline:** Phased approach with estimated timeframes
10. **Risks and Mitigation:** Risk/mitigation strategy pairs
11. **Out of Scope:** Clear exclusions and boundaries
12. **Acceptance Criteria:** Grouped validation criteria

### When to Use Each Structure

- **Use Option 1** for simple features, UI changes, or when working with product managers
- **Use Option 2** for complex technical features, integrations, infrastructure changes, or when the user requests "comprehensive" or "detailed" PRDs
- **Ask the user** which structure they prefer if unclear from the prompt

## Target Audience

Assume the primary reader of the PRD is a **junior developer**. Therefore, requirements should be explicit, unambiguous, and avoid jargon where possible. Provide enough detail for them to understand the feature's purpose and core logic.

## Output
*   **Format:** Markdown (`.md`)
*   **Location:** `docs/features/[feature-name]-PLANNED/`
*   **Filename:** `[feature-name]-prd.md`

## Final instructions
1. Do NOT start implementing the PRD
2. Make sure to ask the user clarifying questions
3. Take the user's answers to the clarifying questions and improve the PRD
4. Ask the user if they want to break the prd down into dev tasks using generate-tasks.mdc (Reply "yes" or "y" to continue)