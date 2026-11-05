# Watched areas

A watched area is a set of bursts that keeps being run under one standard. The server's scheduler, every `scheduler_seconds` (default 300), makes each due area one `workflow` job per burst. A job's span ends on the day of the tick.

```
ponzi-client area-create --name Tehran --bursts t028_058198_iw3 --standard s1-general@1.0.0 --cadence-hours 24
ponzi-client area-update AREA_ID --active false      # pause
ponzi-client area-discover AREA_ID                   # look now, whatever the cadence
ponzi-client jobs --area AREA_ID
```

## What a daily look computes

Content ids decide. The worker plans the standard's workflow and runs only what is not in its cache.

- **Nothing new at ASF.** Discovery is named by what it found, not by the day it looked, so every job is cached and nothing runs.
- **A new acquisition.**
    - A new pairs Item.
    - Only the new pairs' coherence, at most one per baseline. A pair's id depends only on its two granules and the coherence config, never on the rest of the series.
    - A new store, and exactly one new staged run. A monitoring update is a new run; it is never appended to an old one.
    - New events, new p-values and new cells.

`test_watched.py` in ponzi-service holds both cases.
