# References

The papers, data and software PONZI is built on. Each entry says where PONZI uses it.

## Forecasting

- **TiDE**, the default forecaster today (`ponzi.core.forecast.tide`, trained by `ponzi-models train`). It is a default, not a requirement: any forecaster registered beside it is used the same way ([System overview](../concepts/overview.md)).
  Das, A., Kong, W., Leach, A., Mathur, S., Sen, R., and Yu, R. (2023). Long-term Forecasting with TiDE: Time-series Dense Encoder. *Transactions on Machine Learning Research*. [arXiv:2304.08424](https://arxiv.org/abs/2304.08424)

## Satellite data

- **Sentinel-1**, the C-band SAR mission whose IW SLC bursts PONZI processes.
  Torres, R., et al. (2012). GMES Sentinel-1 mission. *Remote Sensing of Environment*, 120, 9-24. [doi:10.1016/j.rse.2011.05.028](https://doi.org/10.1016/j.rse.2011.05.028)
- **ASF**, the Alaska Satellite Facility, from which the SLC bursts, the burst search (`dataset=SLC-BURST`) and the orbit files (S1QC) come. [asf.alaska.edu](https://asf.alaska.edu)
- **OPERA burst database**, the burst ids and footprints (`t028_058198_iw3`) the burst catalog is built from. [opera-adt/burst_db](https://github.com/opera-adt/burst_db)

## Covariates and ancillary data

- **ERA5-Land**, the weather series of the sidecar (`era5_*`), from the DestinE Earth Data Hub or the Copernicus CDS.
  Muñoz-Sabater, J., et al. (2021). ERA5-Land: a state-of-the-art global reanalysis dataset for land applications. *Earth System Science Data*, 13, 4349-4383. [doi:10.5194/essd-13-4349-2021](https://doi.org/10.5194/essd-13-4349-2021)
- **GHSL**, the Global Human Settlement Layer of the European Commission's Joint Research Centre: the built-up surface `GHS_BUILT_S` (R2023A, epoch 2020) and the land fraction `GHS_LAND` (R2022A), the `built` and `land` layers of the sidecar. [human-settlement.emergency.copernicus.eu](https://human-settlement.emergency.copernicus.eu)
- **Copernicus DEM GLO-30**, the 30 m elevation model of the coherence chain, stitched to ellipsoidal heights by dem_stitcher. [Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)
- **World Bank Official Boundaries**, the administrative units of levels 0 to 2 that areas are chosen from (CR-053). [World Bank Data Catalog](https://datacatalog.worldbank.org)

## Grids

- **Major TOM**, the 10 km grid of the panels' cells and the delivered outputs ([Grids](../concepts/grids.md)).
  Francis, A., and Czerkawski, M. (2024). Major TOM: Expandable Datasets for Earth Observation. *IGARSS 2024*. [arXiv:2402.12095](https://arxiv.org/abs/2402.12095)

## Software

- **ISCE3**, the InSAR Scientific Computing Environment, the coherence backend of `ponzi-pipeline` (0.25.22, CUDA 12.9 build). [isce-framework/isce3](https://github.com/isce-framework/isce3)
- **s1-reader** and **COMPASS**, the OPERA readers and geocoding of Sentinel-1 bursts, beside ISCE3. [opera-adt/s1-reader](https://github.com/opera-adt/s1-reader), [opera-adt/COMPASS](https://github.com/opera-adt/COMPASS)
- **asf_search**, the search and download client of ASF. [asfadmin/Discovery-asf_search](https://github.com/asfadmin/Discovery-asf_search)
- **dem_stitcher**, the DEM tiles stitched over a burst. [ACCESS-Cloud-Based-InSAR/dem-stitcher](https://github.com/ACCESS-Cloud-Based-InSAR/dem-stitcher)
- **repeat_ccd**, by Corey Scher, from which the acquisition, orbit and ISCE3 coherence code of `ponzi-pipeline` was ported.
- **STAC**, the SpatioTemporal Asset Catalog specification every output is recorded in ([STAC profile](../concepts/stac-profile.md)). [stacspec.org](https://stacspec.org)
- **Zarr**, the format of the stores. [zarr.dev](https://zarr.dev)
- **PyTorch**, the training and the TorchScript artifacts of TiDE, the default forecaster; optional (`ponzi[tide]`). [pytorch.org](https://pytorch.org)

A paper, dataset or tool the code relies on that is missing here is a gap in this page: add it with the change that brings it in.
