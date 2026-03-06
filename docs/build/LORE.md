# Non-Canon Characters (Claude's Contributions to the Cast)

During the Stage 5 hotfix session, Claude hallucinated three characters
who do not appear in *The Specimen*:

- **Berthold** — zero occurrences in the manuscript. Pure invention.
- **Theo** — zero occurrences. "Theo" matched substrings of "theory" and "though" in grep, which only made it funnier.
- **Agnes** — suggested as a protagonist during a re-analysis run. Also does not exist.

These were passed to the engine via `--characters emil,felix,clara,agnes,berthold,theo`,
producing agency profiles for ghosts. The incident led directly to the
Character Detection & Refinement spec update (detect → suggest → user confirms)
so that the human always has final say on the cast list.

Working title for the inevitable fanfic: *Agnes and Berthold: A Prague Romance (feat. Theoloneous)*.

**This is not part of the codebase, the spec, or canon. It is simply too funny to delete.**
