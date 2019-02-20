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

0.0.10 (2018-12-10)
-------------------

* Added multitone generator. Added 128-QAM and 256-QAM. Streamlined UXG instrument class, split play()/stop into stream_play() and arb_play()/stream_stop() and arb_stop(). Updated index to include a better intro to the project.

0.0.11 (2019-01-23)
-------------------

* Fixed bugs with multitone generator. Added AM modulator.

0.0.12 (2019-02-20)
-------------------

* Removed UXG class and replaced it with two classes, AnalogUXG and VectorUXG. Expanded VSG class to include M9381A and M9383A without changing public API.
