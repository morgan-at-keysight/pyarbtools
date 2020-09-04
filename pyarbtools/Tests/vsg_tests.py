"""Tests for the VSG instrument class"""

from pyarbtools.instruments import VSG
from pyarbtools.vsaControl import VSA
from pyarbtools import wfmBuilder
import socketscpi
import unittest


class VSGTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ipAddress = '192.168.50.124'
        cls.vsg = VSG(ipAddress, reset=True)
        cls.num = 400
        cls.neg = -400
        cls.string = 'bad'
        cls.numList = [0, 1, 2]
        cls.stringList = ['zero', 'one', 'two']
        cls.mixList = [0, 'one', 2e2]
        cls.vsg.err_check()

    # @unittest.skip('Saving time testing the tests.')
    def test_constructor(self):
        self.assertRaises(ValueError, VSG, 'not a valid IP address')
        self.assertRaises(TypeError, VSG, self.num)
        # It's odd that a negative number results in a ValueError rather than a TypeError
        self.assertRaises(ValueError, VSG, self.neg)
        self.assertEqual(type(self.vsg), VSG)

    # @unittest.skip('Saving time testing the tests.')
    def test_configure(self):

        # general
        self.assertRaises(KeyError, self.vsg.configure, badkey=0)
        self.assertRaises(TypeError, self.vsg.configure, 5)
        self.assertRaises(TypeError, self.vsg.configure, self.string)

    # @unittest.skip('Saving time testing the tests.')
    def test_rfState(self):
        # rfState
        self.assertRaises(ValueError, self.vsg.configure, rfState=self.string)
        self.assertRaises(ValueError, self.vsg.configure, rfState=self.num)
        self.assertRaises(ValueError, self.vsg.configure, rfState=self.neg)

        self.vsg.configure(rfState='on')
        self.assertEqual(self.vsg.rfState, 1)
        self.vsg.configure(rfState='off')
        self.assertEqual(self.vsg.rfState, 0)

    # @unittest.skip('Saving time testing the tests.')
    def test_modState(self):
        # modState
        self.assertRaises(ValueError, self.vsg.configure, modState=self.string)
        self.assertRaises(ValueError, self.vsg.configure, modState=self.num)
        self.assertRaises(ValueError, self.vsg.configure, modState=self.neg)

        self.vsg.configure(modState='on')
        self.assertEqual(self.vsg.modState, 1)
        self.vsg.configure(modState='off')
        self.assertEqual(self.vsg.modState, 0)

    # @unittest.skip('Saving time testing the tests.')
    def test_cf(self):
        # cf
        self.assertRaises(ValueError, self.vsg.configure, cf=self.string)
        self.assertRaises(ValueError, self.vsg.configure, cf=self.neg)

        cf = 1e9
        self.vsg.configure(cf=cf)
        self.assertEqual(self.vsg.cf, cf)

    # @unittest.skip('Saving time testing the tests.')
    def test_amp(self):
        # amp
        self.assertRaises(ValueError, self.vsg.configure, amp=self.string)

        amp = -20
        self.vsg.configure(amp=amp)
        self.assertEqual(self.vsg.amp, amp)

    # @unittest.skip('Saving time testing the tests.')
    def test_alcState(self):
        # alcState
        self.assertRaises(ValueError, self.vsg.configure, alcState=self.string)
        self.assertRaises(ValueError, self.vsg.configure, alcState=self.num)
        self.assertRaises(ValueError, self.vsg.configure, alcState=self.neg)

        self.vsg.configure(alcState='on')
        self.assertEqual(self.vsg.alcState, 1)
        self.vsg.configure(alcState='off')
        self.assertEqual(self.vsg.alcState, 0)

    # @unittest.skip('Saving time testing the tests.')
    def test_iqScale(self):
        # iqScale
        self.assertRaises(ValueError, self.vsg.configure, iqScale=self.string)
        self.assertRaises(ValueError, self.vsg.configure, iqScale=self.num)
        self.assertRaises(ValueError, self.vsg.configure, iqScale=self.neg)

        iqScale = 65
        self.vsg.configure(iqScale=iqScale)
        self.assertEqual(self.vsg.iqScale, iqScale)

    # @unittest.skip('Saving time testing the tests.')
    def test_refSrc(self):
        # refSrc
        self.assertRaises(ValueError, self.vsg.configure, refSrc=self.string)
        self.assertRaises(ValueError, self.vsg.configure, refSrc=self.num)
        self.assertRaises(ValueError, self.vsg.configure, refSrc=self.neg)

        refSrc = 'int'
        self.vsg.configure(refSrc=refSrc)
        self.assertEqual(self.vsg.refSrc.lower(), refSrc)

    # @unittest.skip('Saving time testing the tests.')
    def test_fs(self):
        # fs
        self.assertRaises(ValueError, self.vsg.configure, fs=self.string)
        self.assertRaises(ValueError, self.vsg.configure, fs=self.neg)

        fs = 10e6
        self.vsg.configure(fs=fs)
        self.assertEqual(self.vsg.fs, fs)

        # self.vsg.configure(rfState=1)
        # print(self.vsg.rfState)

    # @unittest.skip('Saving time testing the tests.')
    def test_download_play_stop(self):
        fs = 40e6
        self.vsg.configure(cf=1e9, amp=-20, fs=fs)
        wfmData = wfmBuilder.digmod_generator(fs=fs, symRate=10e6, modType='qpsk')
        badData = wfmBuilder.sine_generator(fs=fs, wfmFormat='real')

        self.assertRaises(TypeError, self.vsg.download_wfm, self.string)
        self.assertRaises(TypeError, self.vsg.download_wfm, self.num)
        self.assertRaises(TypeError, self.vsg.download_wfm, self.neg)
        self.assertRaises(TypeError, self.vsg.download_wfm, badData)

        id = self.vsg.download_wfm(wfmData)
        self.vsg.err_check()

        self.vsg.play(id)
        self.assertEqual(self.vsg.rfState, 1)
        self.assertEqual(self.vsg.modState, 1)
        self.assertEqual(self.vsg.arbState, 1)

        self.vsg.stop()
        self.assertEqual(self.vsg.rfState, 0)
        self.assertEqual(self.vsg.modState, 0)
        self.assertEqual(self.vsg.arbState, 0)

    def test_wfm_fidelity(self):

        amplitude = -10
        fs = 40e6
        freq = 1e9
        self.vsg.configure(amp=amplitude, fs=fs, cf=freq)

        # Waveform creation variables
        symRate = 10e6
        modType = 'qpsk'
        psFilter = 'rootraisedcosine'
        alpha = 0.35
        name = 'digmod'
        mFilter = 'rootraisedcosine'
        rFilter = 'raisedcosine'

        print('Creating waveform.')
        # This is the new digital modulation waveform creation function
        data = wfmBuilder.digmod_generator(fs=fs, symRate=symRate, modType=modType, filt=psFilter, numSymbols=1000,
                                                      alpha=alpha)

        # Download and play waveform
        self.vsg.download_wfm(data, wfmID=name)
        self.vsg.play(name)

        # Create VSA object
        vsa = VSA('127.0.0.1', vsaHardware='Morgan Office MXA', timeout=30, reset=False)

        # Select a digital demod measurement and configure it to measure the saved waveform
        vsa.set_measurement('ddemod')

        # Configure digital demodulation in VSA
        vsa.configure_ddemod(cf=freq, amp=0, span=symRate * 2, modType=modType, symRate=symRate, measFilter=mFilter,
                             refFilter=rFilter, filterAlpha=alpha, measLength=4096, eqState=False)

        # Perform a single-shot replay in VSA
        vsa.acquire_single()

        meas = float(vsa.query(f'trace4:data:table? "EvmRms"').strip())
        self.assertLess(meas, 2)

        # Check for errors and gracefully disconnect
        vsa.err_check()
        vsa.disconnect()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.vsg.write('*rst')
        cls.vsg.query('*opc?')
        cls.vsg.disconnect()


if __name__ == 'main':

    unittest.main()
