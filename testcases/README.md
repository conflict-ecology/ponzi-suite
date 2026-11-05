# Test cases

Named test cases of PONZI, one folder each (CR-043; in ponzi-suite since ponzi-core CR-048). A case is a test location: everything that says how PONZI runs
there, as composable yaml files. The library holds no named recipes or presets. A case's files are named by their
path, and a file builds on another with `extends:` (`ponzi_spec.compose`).

    ponzi-suite/testcases/<case>/
      README.md        what the case is, and what is still missing
      recipe.yaml      its detection recipe (ponzi.products.DetectionRecipe fields)
      area.yaml        where and when: aoi_id, geometry (WKT), burst_ids, event_start, event_end, source
      forecaster.yaml  its model's forecaster, when it has its own (ponzi_models.training.fit_spec)
      run_config.yaml  its run config (C10), when there is one
      standard.yaml    its standard, when there is one

Cases:

- [gaza](gaza/README.md): the Gaza damage releases.

Panels (the bursts and cells a model is trained and calibrated on) are not test cases. Their definitions live in ponzi-suite `panels/<id>/` (ponzi-core CR-046 to CR-048), for example `panels/majortom-global`.

ponzi-core's tests load every case's files (`packages/core/tests/test_testcases.py`), so a case that stops loading fails the
build. Use one from the command line by its path, for example `ponzi detect RUN --calibration ID --recipe
../ponzi-suite/testcases/gaza/recipe.yaml` from ponzi-core.
