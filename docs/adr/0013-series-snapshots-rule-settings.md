# A Series snapshots its rule settings

When a Series is created it stores a copy of its Draft Order (with the id it came from) and its other rule settings, instead of referring to the Title profile. Editing a profile therefore affects only new Series; otherwise it would silently rewrite history. Moving an existing Series to an updated order or setting is an ordinary change to that Series, with the same checks and impact preview.

## Amendment (2026-11-28): deliberate Series Format changes

A Series Format can change after Games exist when every non-voided Game fits within the new format's maximum. Count all non-voided Games, including incomplete drafts and Games awaiting results. Refuse a smaller maximum with a specific error; keep Voided Games and their recorded history without counting them towards this limit.

As with Draft Order changes in [ADR 0012](0012-draft-order-chosen-per-series.md), show the impact before the analyst explicitly saves. The preview shows whether the Series is ended before and after, and any Games now past the deciding Game, using the existing warning while keeping those records. For example, Best-of-5 at 2–0 changed to Best-of-3 becomes ended. Cancellation changes nothing. Changes to Fearless, other rule settings, Draft Order and the Disabled List use the same preview, including Violations created or cleared and Players whose Remaining Pool changes.

This allows corrections without recreating a Series, while refusing a format that cannot contain its existing non-voided Games. Profile edits still affect only new Series unless an analyst deliberately applies an order to an existing Series.
