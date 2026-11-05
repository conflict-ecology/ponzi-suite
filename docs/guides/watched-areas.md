# Watched areas

A watched area is a set of bursts that keeps being run under one standard. The bursts are given by id, or chosen by the server from an administrative boundary and an orbit pass: the bursts of that pass whose footprints meet the boundary. The server's scheduler, every `scheduler_seconds` (default 300), makes each due area one `workflow` job per burst. A job's span starts on the area's `start_date` when it has one, and ends on the day of the tick or on the area's `end_date`, whichever is first. Before its first day an area makes no jobs.

```
ponzi-client area-create --name Tehran --bursts t028_058198_iw3 --standard s1-general@1.0.0 --cadence-hours 24
ponzi-client area-update AREA_ID --active false      # pause
ponzi-client area-discover AREA_ID                   # look now, whatever the cadence
ponzi-client jobs --area AREA_ID                     # its jobs; a done job lists the Items it made
```

An area from a boundary is made from Python (the command line takes burst ids only):

```python
c.boundaries(level=1, bbox=[34.2, 31.2, 34.6, 31.6])     # find the code: the Gaza Strip is PSE001
c.create_area(name="Gaza", boundary={"level": 1, "code": "PSE001"}, orbit_pass="ASCENDING",
              start_date="2023-10-01", standard="s1-general@1.0.0")
```

ponzi-visual does the same on its map: choose a level, click a boundary, give the days and the orbit.

## What a daily look computes

Content ids decide. The worker plans the standard's workflow and runs only what is not in its cache.

- **Nothing new at ASF.** Discovery is named by what it found, not by the day it looked, so every job is cached and nothing runs.
- **A new acquisition.**
    - A new pairs Item.
    - Only the new pairs' coherence, at most one per baseline. A pair's id depends only on its two granules and the coherence config, never on the rest of the series.
    - A new store, and exactly one new staged run. A monitoring update is a new run; it is never appended to an old one.
    - New events, new p-values and new cells.

`test_watched.py` in ponzi-service holds both cases.
