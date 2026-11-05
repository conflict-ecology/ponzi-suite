---
name: ux
description: Apply the Laws of UX (lawsofux.com) when designing, building, or reviewing any user interface, such as ponzi-visual front-end screens, dashboards, forms, navigation, onboarding, CLI output meant for people, or HTML artifacts. Use it whenever the task involves layout, visual hierarchy, choice and option design, response time and loading states, grouping, progress indicators, error and input handling, or a UI/UX critique, even if the user doesn't mention "UX".
---

# Laws of UX

A working guide to the 30 heuristics collected by Jon Yablonski at https://lawsofux.com/. The text here paraphrases the site. Full notes for each law (definition, takeaways, origin) are in [references/laws.md](references/laws.md); read the entries for the laws that apply to the task.

## How to use this skill

1. **Name the user and their goal.** Decide who uses the screen and what they are trying to do. Every law below serves that goal. None of them is a reason to add decoration.
2. **Design or review against the checklist below.** Use only the groups that fit the task: a loading spinner needs the "Speed" group, a settings page needs "Choices" and "Grouping".
3. **Cite the law when you make a call.** In a review, tie each finding to a law and a concrete fix, for example: "Hick's Law: 14 equal-weight buttons in the toolbar; keep the 4 common actions and move the rest into an overflow menu."
4. **Treat the laws as heuristics.** They come from psychology research and conflict with each other at times (Occam's Razor vs. Tesler's Law, for example). When they disagree, decide based on the user's goal and say what you traded off.

## Checklist by concern

### Choices and decisions
- **Hick's Law / Choice Overload:** fewer options, a recommended default, progressive disclosure for advanced features. Offer search and filters for long lists.
- **Pareto Principle:** spend effort on the 20% of features most users rely on.
- **Occam's Razor:** cut every element that the screen still works without.
- **Tesler's Law:** don't push the complexity that can't be removed onto the user. The system should absorb it (smart defaults, inference, autofill).

### Memory and cognitive load
- **Cognitive Load / Working Memory / Miller's Law:** show only what the current step needs. Don't make users carry facts from one screen to the next; put comparisons side by side. Don't treat "7 ± 2" as a hard rule for menu length.
- **Chunking:** split long content and inputs (phone numbers, long forms, dense tables) into labeled groups with clear hierarchy.
- **Serial Position Effect:** put key items first and last; the middle is remembered least.
- **Recognition over recall** (from Working Memory): breadcrumbs, visited states, recent items.

### Grouping and visual structure (Gestalt)
- **Proximity:** related items sit close together; unrelated items get space between them.
- **Common Region:** use a border or background to mark a group.
- **Similarity:** items that look alike read as one kind of thing, so links and interactive controls must not look like body text.
- **Uniform Connectedness:** lines, arrows, or shared frames show relationships.
- **Prägnanz:** prefer simple, unambiguous shapes and layouts.
- **Von Restorff Effect:** give the primary action or critical information a distinct look, and use that sparingly. Never signal it with color alone, and keep motion gentle.

### Expectations and conventions
- **Jakob's Law / Mental Model:** follow the patterns users know from other products. When you redesign, give users a transition path.
- **Paradox of the Active User:** people skip documentation. Put help inline where it's needed (tooltips, empty states, examples next to inputs).
- **Postel's Law:** accept messy input (formats, casing, whitespace, units), normalize it, state limits clearly, and give clear feedback.

### Speed, flow, and motivation
- **Doherty Threshold:** respond in under about 400 ms. Otherwise show immediate feedback, skeletons or progress bars, and optimistic UI.
- **Flow:** match difficulty to skill, give feedback for every action, remove friction.
- **Parkinson's Law:** finish tasks sooner than users expect (autofill, sensible defaults, fewer steps).
- **Goal-Gradient / Zeigarnik:** show progress and remaining steps. Showing some progress at the start helps people finish.
- **Peak-End Rule:** polish the best moment and the final step (confirmations, success states). Bad moments weigh more, so fix friction first.

### Perception and attention
- **Aesthetic-Usability Effect:** polish builds trust and tolerance for small flaws, but it can hide real usability problems in testing. Test tasks, not looks.
- **Selective Attention:** users filter out anything that looks like an ad (banner blindness) and miss changes that lack a clear cue (change blindness). Don't make content look like an ad. Announce important changes clearly, one at a time.
- **Cognitive Bias:** defaults, framing, and ordering steer decisions. Use them to help users, never to manipulate them, and watch for your own confirmation bias when reading test results.

### Targets and input
- **Fitts's Law:** make targets large (at least about 44×44 px for touch), leave space between them, and place frequent actions near where the user is already looking or pointing.

## Output format for a UX review

For each finding give: **law**, **where** (file:line or screen element), **problem**, **fix**. Order findings by impact on the user's main task, and end with what already works well.
