# Character roles are derived from data, never hand-maintained

The Character Catalog carries no roles or tags. Nimbus computes Observed Role Usage in code from match history, so it follows new Characters automatically and works for any Title with Roles. The copilot must not silently fall back on the language model's general knowledge, which misses Characters released after its training and is thin and quickly stale for Deadlock: when it uses general knowledge instead of Nimbus data it says so, and it says when a Character has little or no data.

## Considered Options

- Roles and tags in the catalog: upkeep by hand for every Title and every new Character.
- Rely on the model's own knowledge of Characters: unreliable for the reasons above.
