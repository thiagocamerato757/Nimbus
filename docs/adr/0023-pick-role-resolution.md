# A pick's Role is resolved from the most specific evidence available

Observed Role Usage is a global aggregate and is wrong exactly for flex picks, where a coach most needs the truth. The Role of a pick is therefore the first of:

1. the Role recorded for that Game;
2. the assigned Player's usual Role;
3. **Lineup pool match:** when the Lineup is known, the usual Role of the one Player who has the Character in their Character Pool (Declared or Observed), or who accounts for a clear majority of the Lineup's observed plays of it;
4. the Character's most frequent Role in Observed Role Usage, if it holds a clear majority;
5. unknown, which is left out and reported like any missing field.

The "clear majority" threshold is a Title profile setting (default 70%) used by steps 3 and 4. Roles from steps 3 and 4 are inferred: reports state how many picks behind a figure were inferred, and the copilot labels each one and says which step produced it. For an opponent's live draft, where the Lineup is usually known beforehand, step 3 gives something better than the global guess.
