"""Tests for the VXG instrument class"""

from pyarbtools.instruments import VXG
from pyarbtools.vsaControl import VSA
from pyarbtools import wfmBuilder
import socketscpi
import unittest


class VXGTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ipAddress = '141.121.151.242'
        cls.vxg = VXG(ipAddress, reset=True)
        cls.num = 400
        cls.neg = -400
        cls.string = 'bad'
        cls.numList = [0, 1, 2]
        cls.stringList = ['zero', 'one', 'two']
        cls.mixList = [0, 'one', 2e2]

    # @unittest.skip('Saving time testing the tests.')
    def test_constructor(self):
        self.assertRaises(ValueError, VXG, 'not a valid IP address')
        self.assertRaises(TypeError, VXG, self.num)
        # It's odd that a negative number results in a ValueError rather than a TypeError
        self.assertRaises(ValueError, VXG, self.neg)
        self.assertEqual(type(self.vxg), VXG)

    # @unittest.skip('Saving time testing the tests.')
    def test_configure(self):

        # general
        self.assertRaises(KeyError, self.vxg.configure, badkey=0)
        self.assertRaises(TypeError, self.vxg.configure, 5)
        self.assertRaises(TypeError, self.vxg.configure, self.string)

    # @unittest.skip('Saving time testing the tests.')
    def test_rfState(self):
        # rfState
        for ch in [1, 2]:
            exec(f'self.assertRaises(ValueError, self.vxg.configure, rfState{ch}=self.string)')
            exec(f'self.assertRaises(ValueError, self.vxg.configure, rfState{ch}=self.num)')
            exec(f'self.assertRaises(ValueError, self.vxg.configure, rfState{ch}=self.neg)')

            exec(f'self.vxg.configure(rfState{ch}="on")')
            exec(f'self.assertEqual(self.vxg.rfState{ch}, 1)')
            exec(f'self.vxg.configure(rfState{ch}="off")')
            exec(f'self.assertEqual(self.vxg.rfState{ch}, 0)')

        # self.assertRaises(ValueError, self.vxg.configure, rfState2=self.string)
        # self.assertRaises(ValueError, self.vxg.configure, rfState2=self.num)
        # self.assertRaises(ValueError, self.vxg.configure, rfState2=self.neg)
        #
        # self.vxg.configure(rfState2='on')
        # self.assertEqual(self.vxg.rfState2, 1)
        # self.vxg.configure(rfState2='off')
        # self.assertEqual(self.vxg.rfState2, 0)

    # @unittest.skip('Saving time testing the tests.')
    def test_modState(self):
        # modState
        for ch in [1, 2]:
            exec(f'self.assertRaises(ValueError, self.vxg.configure, modState{ch}=self.string)')
            exec(f'self.assertRaises(ValueError, self.vxg.configure, modState{ch}=self.num)')
            exec(f'self.assertRaises(ValueError, self.vxg.configure, modState{ch}=self.neg)')

            exec(f'self.vxg.configure(modState{ch}="on")')
            exec(f'self.assertEqual(self.vxg.modState{ch}, 1)')
            exec(f'self.vxg.configure(modState{ch}="off")')
            exec(f'self.assertEqual(self.vxg.modState{ch}, 0)')

        # self.assertRaises(ValueError, self.vxg.configure, modState1=self.string)
        # self.assertRaises(ValueError, self.vxg.configure, modState1=self.num)
        # self.assertRaises(ValueError, self.vxg.configure, modState1=self.neg)
        #
        # self.vxg.configure(modState1='on')
        # self.assertEqual(self.vxg.modState1, 1)
        # self.vxg.configure(modState1='off')
        # self.assertEqual(self.vxg.modState1, 0)

    # @unittest.skip('Saving time testing the tests.')
    def test_cf(self):
        # cf
        for ch in [1, 2]:
            exec(f'self.assertRaises(ValueError, self.vxg.configure, cf{ch}=self.string)')
            exec(f'self.assertRaises(ValueError, self.vxg.configure, cf{ch}=self.neg)')

            cf = 1e9
            exec(f'self.vxg.configure(cf{ch}={cf})')
            exec(f'self.assertEqual(self.vxg.cf{ch}, {cf})')

    # @unittest.skip('Saving time testing the tests.')
    def test_amp(self):
        # amp
        for ch in [1, 2]:
            exec(f'self.assertRaises(ValueError, self.vxg.configure, amp{ch}=self.string)')

            amp = -20
            exec(f'self.vxg.configure(amp{ch}=amp)')
            exec(f'self.assertEqual(self.vxg.amp{ch}, amp)')

    # @unittest.skip('Saving time testing the tests.')
    def test_alcState(self):
        # alcState
        for ch in [1, 2]:
            exec(f'self.assertRaises(ValueError, self.vxg.configure, alcState{ch}=self.string)')
            exec(f'self.assertRaises(ValueError, self.vxg.configure, alcState{ch}=self.num)')
            exec(f'self.assertRaises(ValueError, self.vxg.configure, alcState{ch}=self.neg)')

            exec(f'self.vxg.configure(alcState{ch}="on")')
            exec(f'self.assertEqual(self.vxg.alcState{ch}, 1)')
            exec(f'self.vxg.configure(alcState{ch}="off")')
            exec(f'self.assertEqual(self.vxg.alcState{ch}, 0)')

    # @unittest.skip('Saving time testing the tests.')
    def test_iqScale(self):
        # iqScale
        self.assertRaises(ValueError, self.vxg.configure, iqScale1=self.string)
        self.assertRaises(ValueError, self.vxg.configure, iqScale1=self.num)
        self.assertRaises(ValueError, self.vxg.configure, iqScale1=self.neg)

        iqScale = 65
        self.vxg.configure(iqScale1=iqScale)
        self.assertEqual(self.vxg.iqScale1, iqScale)

    # @unittest.skip('Saving time testing the tests.')
    def test_refSrc(self):
        # refSrc
        self.assertRaises(ValueError, self.vxg.configure, refSrc=self.string)
        self.assertRaises(ValueError, self.vxg.configure, refSrc=self.num)
        self.assertRaises(ValueError, self.vxg.configure, refSrc=self.neg)

        refSrc = 'int'
        self.vxg.configure(refSrc=refSrc)
        self.assertEqual(self.vxg.refSrc.lower(), refSrc)

    # @unittest.skip('Saving time testing the tests.')
    def test_fs(self):
        # fs
        for ch in [1, 2]:
            exec(f'self.assertRaises(ValueError, self.vxg.configure, fs{ch}=self.string)')
            exec(f'self.assertRaises(ValueError, self.vxg.configure, fs{ch}=self.neg)')

            fs = 10e6
            exec(f'self.vxg.configure(fs{ch}=fs)')
            exec(f'self.assertEqual(self.vxg.fs{ch}, fs)')

        # self.vxg.configure(rfState=1)
        # print(self.vxg.rfState)

    # @unittest.skip('Saving time testing the tests.')
    def test_download_play_stop(self):
        fs = 40e6
        self.vxg.configure(cf=1e9, amp=-20, fs=fs)
        wfmData = wfmBuilder.digmod_generator(fs=fs, symRate=10e6, modType='qpsk')

        self.assertRaises(TypeError, self.vxg.download_wfm, self.string)
        self.assertRaises(TypeError, self.vxg.download_wfm, self.num)
        self.assertRaises(TypeError, self.vxg.download_wfm, self.neg)

        id = self.vxg.download_wfm(wfmData)
        self.vxg.err_check()

        self.vxg.play(id)
        self.assertEqual(self.vxg.rfState1, 1)
        self.assertEqual(self.vxg.modState1, 1)
        self.assertEqual(self.vxg.arbState1, 1)

        self.vxg.stop()
        self.assertEqual(self.vxg.rfState1, 0)
        self.assertEqual(self.vxg.modState1, 0)
        self.assertEqual(self.vxg.arbState1, 0)

    # @unittest.skip('Saving time testing the tests.')
    def test_wfm_fidelity(self):

        amplitude = -10
        fs = 40e6
        freq = 1e9
        self.vxg.configure(amp=amplitude, fs=fs, cf=freq)

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
        self.vxg.download_wfm(data, wfmID=name)
        self.vxg.play(name)

        # Create VSA object
        vsa = VSA('127.0.0.1', vsaHardware='VXG-MXA', timeout=30, reset=False)

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
        cls.vxg.write('*rst')
        cls.vxg.query('*opc?')
        cls.vxg.disconnect()


if __name__ == 'main':

    unittest.main()
