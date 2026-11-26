# A Series snapshots its rule settings

When a Series is created it stores a copy of its Draft Order (with the id it came from) and its other rule settings, instead of referring to the Title profile. Editing a profile therefore affects only new Series; otherwise it would silently rewrite history. Moving an existing Series to an updated order or setting is an ordinary change to that Series, with the same checks and impact preview.
