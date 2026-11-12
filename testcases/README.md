# Test cases

Named test locations of PONZI, one folder each. A case holds where and when it is; the specs made for it live with the
other specs under `specs/`, named after it (`tide-weather-gaza-finetune`, `single-path-gaza-release`), so that a
command or another spec can name them.

    ponzi-suite/testcases/<case>/
      README.md        what the case is, its specs, and what is still missing
      area.yaml        where and when: aoi_id, geometry (WKT), burst_ids, event_start, event_end, source

Cases:

- [gaza](gaza/README.md): the Gaza damage releases.

Panels (the bursts and cells a model is trained and calibrated on) are not test cases: their specs are
`specs/panel_specs/<name>/`, for example `specs/panel_specs/majortom-global`.

ponzi-core's tests load every case's files (`packages/core/tests/test_testcases.py`), so a case that stops loading fails
the build. Use a case's spec by its name, for example `ponzi detect RUN --calibration ID --detection-spec
single-path-gaza-release`.
