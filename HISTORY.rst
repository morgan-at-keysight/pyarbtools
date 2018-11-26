=======
History
=======

0.0.7 (2018-10-09)
------------------

* First release on PyPI.

0.0.8 (2018-11-26)
------------------

* First major update. Added wfmBuilder.iq_correction(), which utilizes Keysight's VSA software and a Keysight receiver (either an oscilloscope or signal analyzer) and applies a digital predistortion filter to a waveform to flatten amplitude and phase response.

0.0.9 (2018-11-26)
------------------

* Fixed a problem with UXG.csv_pdw_file_download() and UXG.csv_windex_file_download() that threw an error when trying to delete a file that didn't exist.
