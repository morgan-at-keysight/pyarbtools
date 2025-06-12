"""
gui
Author: Morgan Allison, Keysight RF/uW Application Engineer
A much-needed GUI for pyarbtools.
"""

# from tkinter import *
import tkinter
from tkinter import ttk
# from tkinter import filedialog
from tkinter import messagebox
from os import path
import ipaddress
import pyarbtools
import socketscpi

"""
TODO
* Add an export waveform button
* Add a stop playback button
* For future help box to explain what the different DAC modes mean
    # self.dacModeArgs = {'Single (Ch 1)': 'single', 'Dual (Ch 1 & 4)': 'dual',
    #                     'Four (All Ch)': 'four', 'Marker (Sig Ch 1, Mkr Ch 3 & 4)': 'marker',
    #                     'Dual Channel Duplicate (Ch 3 & 4 copy Ch 1 & 2)': 'dcd',
    #                     'Dual Channel Marker (Sign Ch 1 & 2, Ch 1 mkr on Ch 3 & 4)': 'dcm'}
"""



# noinspection PyUnusedLocal,PyAttributeOutsideInit
class PyarbtoolsGUI:
    def __init__(self, master):
        # Constants
        self.instClasses = {'M8190A': pyarbtools.instruments.M8190A,
                            'M8195A': pyarbtools.instruments.M8195A,
                            'M8196A': pyarbtools.instruments.M8196A,
                            'VSG': pyarbtools.instruments.VSG,
                            'VXG': pyarbtools.instruments.VXG,}

        # Variables
        self.ipAddress = '127.0.0.1'
        defaultInstrument = 0
        self.inst = None
        self.cbWidth = 17

        """Master Frame Setup"""
        self.master = master

        # master Widgets
        setupFrame = tkinter.Frame(self.master, bd=5)
        self.configFrame = tkinter.Frame(self.master, bd=5)
        self.interactFrame = tkinter.Frame(self.master, bd=5)
        self.wfmTypeSelectFrame = tkinter.Frame(self.master, bd=5)
        self.wfmFrame = tkinter.Frame(self.master, bd=5)
        placeHolder = tkinter.Frame(self.master, bd=5)
        self.wfmListFrame = tkinter.Frame(self.master, bd=5)
        statusBarFrame = tkinter.Frame(self.master)

        # Master frame geometry
        r = 0
        setupFrame.grid(row=r, column=0, sticky=tkinter.N)
        self.wfmTypeSelectFrame.grid(row=r, column=1, sticky=tkinter.N)
        self.interactFrame.grid(row=r, column=2, sticky=tkinter.N, rowspan=2)
        r += 1
        self.configFrame.grid(row=r, column=0, rowspan=2)
        self.wfmFrame.grid(row=r, column=1)
        r += 1
        placeHolder.grid(row=r, column=1)
        self.wfmListFrame.grid(row=r, column=1, sticky=tkinter.N)
        r += 1
        statusBarFrame.grid(row=r, column=0, columnspan=4)

        """setupFrame"""
        # setupFrame Widgets
        self.lblInstruments = tkinter.Label(setupFrame, text='Instrument Class')
        self.cbInstruments = ttk.Combobox(setupFrame, state='readonly', values=list(self.instClasses.keys()))
        self.cbInstruments.current(defaultInstrument)

        v = tkinter.StringVar()
        self.lblInstIPAddress = tkinter.Label(setupFrame, text='Instrument IP Address')
        self.eInstIPAddress = tkinter.Entry(setupFrame, textvariable=v)
        v.set(self.ipAddress)

        self.lblInstStatus = tkinter.Label(setupFrame, text='Not Connected', bg='red', width=13)
        self.btnInstConnect = ttk.Button(setupFrame, text='Connect', command=self.instrument_connect)

        # setupFrame Geometry
        r = 0
        self.lblInstruments.grid(row=r, column=0)
        self.lblInstIPAddress.grid(row=r, column=1)
        self.lblInstStatus.grid(row=r, column=2)
        r += 1

        self.cbInstruments.grid(row=r, column=0)
        self.eInstIPAddress.grid(row=r, column=1)
        self.btnInstConnect.grid(row=r, column=2)

        self.instKey = self.cbInstruments.get()

        """configFrame"""
        # configFrame Widgets

        """interactFrame"""
        # interactFrame Widgets
        lblScpi = tkinter.Label(self.interactFrame, text='Interactive SCPI I/O')
        scpiString = tkinter.StringVar()
        self.eScpi = tkinter.Entry(self.interactFrame, textvariable=scpiString, width=40, state=tkinter.DISABLED)
        scpiString.set('*idn?')

        btnWidth = 9
        self.btnWrite = ttk.Button(self.interactFrame, text='Write', command=self.inst_write, width=btnWidth, state=tkinter.DISABLED)
        self.btnQuery = ttk.Button(self.interactFrame, text='Query', command=self.inst_query, width=btnWidth, state=tkinter.DISABLED)
        self.btnErrCheck = ttk.Button(self.interactFrame, text='Err Check', command=self.inst_err_check, width=btnWidth, state=tkinter.DISABLED)
        self.btnPreset = ttk.Button(self.interactFrame, text='Preset', command=self.inst_preset, width=btnWidth, state=tkinter.DISABLED)
        self.btnFlush = ttk.Button(self.interactFrame, text='Flush', command=self.inst_flush, width=btnWidth, state=tkinter.DISABLED)

        lblReadoutTitle = tkinter.Label(self.interactFrame, text='SCPI Readout', width=40)
        self.lblReadout = tkinter.Label(self.interactFrame, text='Connect to instrument', width=40, relief='sunken')

        # interactFrame Geometry
        r = 0
        lblScpi.grid(row=r, columnspan=4)
        r += 1
        self.eScpi.grid(row=r, columnspan=4)
        r += 1
        self.btnWrite.grid(row=r)
        self.btnErrCheck.grid(row=r, column=1)
        self.btnQuery.grid(row=r, column=2)
        self.btnPreset.grid(row=r, column=3)
        r += 1
        self.btnFlush.grid(row=r, column=0)
        r += 1
        lblReadoutTitle.grid(row=r, columnspan=4)
        r += 1
        self.lblReadout.grid(row=r, columnspan=4)

        """wfmTypeSelectFrame"""
        # wfmTypeSelectFrame Widgets
        wfmLabel = tkinter.Label(self.wfmTypeSelectFrame, text='Waveform Type')
        self.wfmTypeList = ['Sine', 'AM', 'CW Pulse', 'Chirped Pulse', 'Barker Coded Pulse', 'Multitone', 'Digital Modulation']
        self.cbWfmType = ttk.Combobox(self.wfmTypeSelectFrame, state='readonly', values=self.wfmTypeList, width=self.cbWidth)
        self.cbWfmType.current(0)

        self.cbWfmType.bind("<<ComboboxSelected>>", self.open_wfm_builder)

        # wfmTypeSelectFrame Geometry
        r = 0
        wfmLabel.grid(row=r, column=0)
        r += 1
        self.cbWfmType.grid(row=r)

        """wfmFrame"""
        self.open_wfm_builder()
        # self.disable_wfmFrame()

        """wfmListFrame"""
        self.wfmList = []

        # wfmListFrame Widgets
        lblWfmList = tkinter.Label(self.wfmListFrame, text='Waveform List')
        lblNameHdr = tkinter.Label(self.wfmListFrame, text='Name:')
        lblLengthHdr = tkinter.Label(self.wfmListFrame, text='Length:')
        lblFormatHdr = tkinter.Label(self.wfmListFrame, text='Format:')
        self.btnWfmDownload = ttk.Button(self.wfmListFrame, text='Download', command=self.download_wfm, width=btnWidth)
        self.btnWfmDownload.configure(state=tkinter.DISABLED)
        self.btnWfmPlay = ttk.Button(self.wfmListFrame, text='Play', command=self.play_wfm, width=btnWidth)
        self.btnWfmPlay.configure(state=tkinter.DISABLED)
        self.btnWfmDelete = ttk.Button(self.wfmListFrame, text='Delete', command=self.delete_wfm, width=btnWidth)
        self.btnWfmDelete.configure(state=tkinter.DISABLED)
        self.btnWfmClearAll = ttk.Button(self.wfmListFrame, text='Clear All', command=self.clear_all_wfm, width=btnWidth)
        self.btnWfmClearAll.configure(state=tkinter.DISABLED)
        lblChannel = tkinter.Label(self.wfmListFrame, text='Ch')
        self.cbChannel = ttk.Combobox(self.wfmListFrame, width=4)
        self.cbChannel.configure(state=tkinter.DISABLED)
        self.lblName = tkinter.Label(self.wfmListFrame)
        self.lblLength = tkinter.Label(self.wfmListFrame)
        self.lblFormat = tkinter.Label(self.wfmListFrame)
        self.lbWfmList = tkinter.Listbox(self.wfmListFrame, selectmode='single', width=25, exportselection=0)
        self.lbWfmList.bind("<<ListboxSelect>>", self.select_wfm)
        self.cbChannel.bind("<<ComboboxSelected>>", self.change_channel)

        # wfmListFrame Geometry
        listLength = 10
        r = 0
        lblWfmList.grid(row=r, columnspan=2)
        r += 1
        self.lbWfmList.grid(row=r, sticky=tkinter.W, rowspan=listLength, columnspan=2)
        lblNameHdr.grid(row=r, column=2, columnspan=2)
        r += 1
        self.lblName.grid(row=r, column=2, columnspan=2)
        r += 1
        lblLengthHdr.grid(row=r, column=2, columnspan=2)
        r += 1
        self.lblLength.grid(row=r, column=2, columnspan=2)
        r += 1
        lblFormatHdr.grid(row=r, column=2, columnspan=2)
        r += 1
        self.lblFormat.grid(row=r, column=2, columnspan=2)
        r += 1 + listLength
        self.btnWfmDownload.grid(row=r, column=0, sticky=tkinter.E)
        self.btnWfmPlay.grid(row=r, column=1, sticky=tkinter.W)
        lblChannel.grid(row=r, column=2)
        self.cbChannel.grid(row=r, column=3)
        r += 1
        self.btnWfmClearAll.grid(row=r, column=0, sticky=tkinter.E)
        self.btnWfmDelete.grid(row=r, column=1, sticky=tkinter.W)

        """statusBarFrame"""
        # statusBarFrame Widgets
        self.statusBar = tkinter.Label(statusBarFrame, text='Welcome', width=130, relief=tkinter.SUNKEN, bg='white')
        self.statusBar.grid(row=0, sticky=tkinter.N+tkinter.S+tkinter.E+tkinter.W)

    def open_wfm_builder(self, event=None):
        """

        Args:
            event:

        Returns:

        TODO:
            Update the Sine generator to incorporate the CF input AFTER the wfmBuilder.sine_generator() method has been updated.
        """
        self.wfmFrame.destroy()
        self.wfmFrame = tkinter.Frame(self.master, bd=5)
        self.wfmFrame.grid(row=1, column=1, sticky=tkinter.N)

        self.wfmType = self.cbWfmType.get()

        if self.wfmType == 'Sine':
            lblFs = tkinter.Label(self.wfmFrame, text='Sample Rate')
            fsVar = tkinter.StringVar()
            self.eFsWfm = tkinter.Entry(self.wfmFrame, textvariable=fsVar)

            lblSineFreq = tkinter.Label(self.wfmFrame, text='Sine Frequency')
            freqOffsetVar = tkinter.StringVar()
            self.eFreqOffset = tkinter.Entry(self.wfmFrame, textvariable=freqOffsetVar)
            freqOffsetVar.set('0')

            lblSinePhase = tkinter.Label(self.wfmFrame, text='Sine Phase')
            sinePhaseVar = tkinter.StringVar()
            self.eSinePhase = tkinter.Entry(self.wfmFrame, textvariable=sinePhaseVar)
            sinePhaseVar.set('0')

            # Sine Geometry
            r = 0
            lblFs.grid(row=r, column=0, sticky=tkinter.E)
            self.eFsWfm.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblSineFreq.grid(row=r, column=0, sticky=tkinter.E)
            self.eFreqOffset.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblSinePhase.grid(row=r, column=0, sticky=tkinter.E)
            self.eSinePhase.grid(row=r, column=1, sticky=tkinter.W)

        elif self.wfmType == 'AM':
            lblFs = tkinter.Label(self.wfmFrame, text='Sample Rate')
            fsVar = tkinter.StringVar()
            self.eFsWfm = tkinter.Entry(self.wfmFrame, textvariable=fsVar)

            lblAmDepth = tkinter.Label(self.wfmFrame, text='AM Depth')
            amDepthVar = tkinter.StringVar()
            self.eAmDepth = tkinter.Entry(self.wfmFrame, textvariable=amDepthVar)
            amDepthVar.set('50')

            lblModRate = tkinter.Label(self.wfmFrame, text='Modulation Rate')
            modRateVar = tkinter.StringVar()
            self.eModRate = tkinter.Entry(self.wfmFrame, textvariable=modRateVar)
            modRateVar.set('100e3')

            # AM Geometry
            r = 0
            lblFs.grid(row=r, column=0, sticky=tkinter.E)
            self.eFsWfm.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblAmDepth.grid(row=r, column=0, sticky=tkinter.E)
            self.eAmDepth.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblModRate.grid(row=r, column=0, sticky=tkinter.E)
            self.eModRate.grid(row=r, column=1, sticky=tkinter.W)

        elif self.wfmType == 'CW Pulse':
            lblFs = tkinter.Label(self.wfmFrame, text='Sample Rate')
            fsVar = tkinter.StringVar()
            self.eFsWfm = tkinter.Entry(self.wfmFrame, textvariable=fsVar)

            lblPulseWidth = tkinter.Label(self.wfmFrame, text='Pulse Width')
            lengthVar = tkinter.StringVar()
            self.ePulseWidth = tkinter.Entry(self.wfmFrame, textvariable=lengthVar)
            lengthVar.set('1e-6')

            lblPri = tkinter.Label(self.wfmFrame, text='Pulse Rep Interval')
            priVar = tkinter.StringVar()
            self.ePri = tkinter.Entry(self.wfmFrame, textvariable=priVar)
            priVar.set('10e-6')

            lblFreqOffset = tkinter.Label(self.wfmFrame, text='Frequency Offset')
            freqOffsetVar = tkinter.StringVar()
            self.eFreqOffset = tkinter.Entry(self.wfmFrame, textvariable=freqOffsetVar)
            freqOffsetVar.set('0')

            # Chirp Geometry
            r = 0
            lblFs.grid(row=r, column=0, sticky=tkinter.E)
            self.eFsWfm.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblPulseWidth.grid(row=r, column=0, sticky=tkinter.E)
            self.ePulseWidth.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblPri.grid(row=r, column=0, sticky=tkinter.E)
            self.ePri.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblFreqOffset.grid(row=r, column=0, sticky=tkinter.E)
            self.eFreqOffset.grid(row=r, column=1, sticky=tkinter.W)

        elif self.wfmType == 'Chirped Pulse':
            lblFs = tkinter.Label(self.wfmFrame, text='Sample Rate')
            fsVar = tkinter.StringVar()
            self.eFsWfm = tkinter.Entry(self.wfmFrame, textvariable=fsVar)

            lblPulseWidth = tkinter.Label(self.wfmFrame, text='Pulse Width')
            lengthVar = tkinter.StringVar()
            self.ePulseWidth = tkinter.Entry(self.wfmFrame, textvariable=lengthVar)
            lengthVar.set('1e-6')

            lblPri = tkinter.Label(self.wfmFrame, text='Pulse Rep Interval')
            priVar = tkinter.StringVar()
            self.ePri = tkinter.Entry(self.wfmFrame, textvariable=priVar)
            priVar.set('10e-6')

            lblChirpBw = tkinter.Label(self.wfmFrame, text='Chirp Bandwidth')
            chirpBwVar = tkinter.StringVar()
            self.eChirpBw = tkinter.Entry(self.wfmFrame, textvariable=chirpBwVar)
            chirpBwVar.set('40e6')

            # Chirp Geometry
            r = 0
            lblFs.grid(row=r, column=0, sticky=tkinter.E)
            self.eFsWfm.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblPulseWidth.grid(row=r, column=0, sticky=tkinter.E)
            self.ePulseWidth.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblPri.grid(row=r, column=0, sticky=tkinter.E)
            self.ePri.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblChirpBw.grid(row=r, column=0, sticky=tkinter.E)
            self.eChirpBw.grid(row=r, column=1, sticky=tkinter.W)

        elif self.wfmType == 'Barker Coded Pulse':
            lblFs = tkinter.Label(self.wfmFrame, text='Sample Rate')
            fsVar = tkinter.StringVar()
            self.eFsWfm = tkinter.Entry(self.wfmFrame, textvariable=fsVar)

            lblPulseWidth = tkinter.Label(self.wfmFrame, text='Pulse Width')
            lengthVar = tkinter.StringVar()
            self.ePulseWidth = tkinter.Entry(self.wfmFrame, textvariable=lengthVar)
            lengthVar.set('1e-6')

            lblPri = tkinter.Label(self.wfmFrame, text='Pulse Rep Interval')
            priVar = tkinter.StringVar()
            self.ePri = tkinter.Entry(self.wfmFrame, textvariable=priVar)
            priVar.set('10e-6')

            lblCode = tkinter.Label(self.wfmFrame, text='Code Order')
            codeList = ['b2', 'b3', 'b41', 'b42', 'b5', 'b7', 'b11', 'b13']
            self.cbCode = ttk.Combobox(self.wfmFrame, state='readonly', values=codeList, width=self.cbWidth)
            self.cbCode.current(0)

            # Barker Geometry
            r = 0
            lblFs.grid(row=r, column=0, sticky=tkinter.E)
            self.eFsWfm.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblPulseWidth.grid(row=r, column=0, sticky=tkinter.E)
            self.ePulseWidth.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblPri.grid(row=r, column=0, sticky=tkinter.E)
            self.ePri.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblCode.grid(row=r, column=0, sticky=tkinter.E)
            self.cbCode.grid(row=r, column=1, sticky=tkinter.W)

        elif self.wfmType == 'Multitone':
            lblFs = tkinter.Label(self.wfmFrame, text='Sample Rate')
            fsVar = tkinter.StringVar()
            self.eFsWfm = tkinter.Entry(self.wfmFrame, textvariable=fsVar)

            lblSpacing = tkinter.Label(self.wfmFrame, text='Tone Spacing')
            spacingVar = tkinter.StringVar()
            self.eSpacing = tkinter.Entry(self.wfmFrame, textvariable=spacingVar)
            spacingVar.set('1e6')

            lblNumTones = tkinter.Label(self.wfmFrame, text='Num Tones')
            numTonesVar = tkinter.StringVar()
            self.eNumTones = tkinter.Entry(self.wfmFrame, textvariable=numTonesVar)
            numTonesVar.set('11')

            lblPhase = tkinter.Label(self.wfmFrame, text='Phase Relationship')
            phaseList = ['random', 'zero', 'increasing', 'parabolic']
            self.cbPhase = ttk.Combobox(self.wfmFrame, state='readonly', values=phaseList, width=self.cbWidth)
            self.cbPhase.current(0)

            # Multitone Geometry
            r = 0
            lblFs.grid(row=r, column=0, sticky=tkinter.E)
            self.eFsWfm.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblSpacing.grid(row=r, column=0, sticky=tkinter.E)
            self.eSpacing.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblNumTones.grid(row=r, column=0, sticky=tkinter.E)
            self.eNumTones.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblPhase.grid(row=r, column=0, sticky=tkinter.E)
            self.cbPhase.grid(row=r, column=1, sticky=tkinter.W)

        elif self.wfmType == 'Digital Modulation':
            lblFs = tkinter.Label(self.wfmFrame, text='Sample Rate')
            fsVar = tkinter.StringVar()
            self.eFsWfm = tkinter.Entry(self.wfmFrame, textvariable=fsVar)

            lblSymrate = tkinter.Label(self.wfmFrame, text='Symbol Rate')
            symRateVar = tkinter.StringVar()
            self.eSymrate = tkinter.Entry(self.wfmFrame, textvariable=symRateVar)
            symRateVar.set('10e6')

            lblModType = tkinter.Label(self.wfmFrame, text='Modulation Type')
            modTypeList = ['bpsk', 'qpsk', 'psk8', 'psk16', 'apsk16', 'apsk32', 'apsk64', 'qam16', 'qam32', 'qam64', 'qam128', 'qam256']
            self.cbModType = ttk.Combobox(self.wfmFrame, state='readonly', values=modTypeList, width=self.cbWidth)
            self.cbModType.current(0)

            lblNumSymbols = tkinter.Label(self.wfmFrame, text='Number of Symbols')
            numSymbolsVar = tkinter.StringVar()
            self.eNumSymbols = tkinter.Entry(self.wfmFrame, textvariable=numSymbolsVar)
            numSymbolsVar.set('1000')

            lblFiltType = tkinter.Label(self.wfmFrame, text='Filter Type')
            filtTypeList = ['rootraisedcosine', 'raisedcosine']
            self.cbFiltType = ttk.Combobox(self.wfmFrame, state='readonly', values=filtTypeList, width=self.cbWidth)
            self.cbFiltType.current(0)

            lblFiltAlpha = tkinter.Label(self.wfmFrame, text='Filter Alpha')
            filtAlphaVar = tkinter.StringVar()
            self.eFiltAlpha = tkinter.Entry(self.wfmFrame, textvariable=filtAlphaVar)
            filtAlphaVar.set('0.35')

            # Digital Modulation Geometry
            r = 0
            lblFs.grid(row=r, column=0, sticky=tkinter.E)
            self.eFsWfm.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblSymrate.grid(row=r, column=0, sticky=tkinter.E)
            self.eSymrate.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblModType.grid(row=r, column=0, sticky=tkinter.E)
            self.cbModType.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblNumSymbols.grid(row=r, column=0, sticky=tkinter.E)
            self.eNumSymbols.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblFiltType.grid(row=r, column=0, sticky=tkinter.E)
            self.cbFiltType.grid(row=r, column=1, sticky=tkinter.W)

            r += 1
            lblFiltAlpha.grid(row=r, column=0, sticky=tkinter.E)
            self.eFiltAlpha.grid(row=r, column=1, sticky=tkinter.W)

        else:
            print(self.wfmType)
            raise ValueError('Invalid wfmType selected, this should never happen.')

        lblCf = tkinter.Label(self.wfmFrame, text='Carrier Frequency')
        cfVar = tkinter.StringVar()
        cfVar.set('1e9')
        self.eCf = tkinter.Entry(self.wfmFrame, textvariable=cfVar)

        lblWfmFormat = tkinter.Label(self.wfmFrame, text='Waveform Format')
        formatList = ['IQ', 'Real']
        self.cbWfmFormat = ttk.Combobox(self.wfmFrame, state=tkinter.DISABLED, values=formatList, width=self.cbWidth)
        self.cbWfmFormat.current(0)
        self.cbWfmFormat.bind("<<ComboboxSelected>>", self.wfmFormat_select)

        try:
            if self.instKey == 'M8190A':
                if 'intx' in self.inst.res.lower():
                    self.cbWfmFormat.current(0)
                else:
                    self.cbWfmFormat.current(1)
            elif self.instKey in ['M8195A', 'M8196A']:
                self.cbWfmFormat.current(1)
        except AttributeError:
            pass  # nothing is connected

        self.cbWfmFormat.event_generate("<<ComboboxSelected>>")

        lblWfmName = tkinter.Label(self.wfmFrame, text='Name')
        wfmNameVar = tkinter.StringVar()
        self.eWfmName = tkinter.Entry(self.wfmFrame, textvariable=wfmNameVar)
        wfmNameVar.set(f'{self.cbWfmType.get()}')

        self.btnCreateWfm = ttk.Button(self.wfmFrame, text='Create Waveform', command=self.create_wfm)

        if type(self.inst) == pyarbtools.instruments.M8190A and self.cbWfmFormat.get().lower() == 'iq':
            fsVar.set(f'{self.inst.bbfs:.2e}')
        elif type(self.inst) == pyarbtools.instruments.M8195A:
            fsVar.set(f'{self.inst.effFs:.2e}')
        else:
            try:
                fsVar.set(f'{self.inst.fs:.2e}')
            except AttributeError:
                fsVar.set('100e6')

        r += 1
        lblCf.grid(row=r, column=0, sticky=tkinter.E)
        self.eCf.grid(row=r, column=1, sticky=tkinter.W)
        r += 1
        lblWfmFormat.grid(row=r, column=0, sticky=tkinter.E)
        self.cbWfmFormat.grid(row=r, column=1, sticky=tkinter.W)
        r += 1
        lblWfmName.grid(row=r, column=0, sticky=tkinter.E)
        self.eWfmName.grid(row=r, column=1, sticky=tkinter.W)
        r += 1
        self.btnCreateWfm.grid(row=r, columnspan=2)

    def wfmFormat_select(self, event=None):
        """Enables or disables cf input based on waveform format."""
        wfmFormat = self.cbWfmFormat.get()
        if wfmFormat.lower() == 'iq':
            self.eCf.configure(state=tkinter.DISABLED)
        elif wfmFormat.lower() == 'real':
            self.eCf.configure(state=tkinter.NORMAL)
        else:
            raise ValueError('Invalid waveform format selected. This should never happen.')

    def create_wfm(self):
        """Calls the function to create the selected type of waveform
        and stores it in the waveform list.
        TODO
            Update Sine arguments after function gets updated in wfmBuilder.
        """

        try:
            if self.wfmType == 'Sine':
                wfmArgs = [float(self.eFsWfm.get()), float(self.eFreqOffset.get()),
                           float(self.eSinePhase.get()), self.cbWfmFormat.get()]
                wfmRaw = pyarbtools.wfmBuilder.sine_generator(*wfmArgs)
            elif self.wfmType == 'AM':
                wfmArgs = [float(self.eFsWfm.get()), int(self.eAmDepth.get()),
                           float(self.eModRate.get()), float(self.eCf.get()),
                           self.cbWfmFormat.get()]
                wfmRaw = pyarbtools.wfmBuilder.am_generator(*wfmArgs)
            elif self.wfmType == 'CW Pulse':
                wfmArgs = [float(self.eFsWfm.get()), float(self.ePulseWidth.get()),
                           float(self.ePri.get()), float(self.eFreqOffset.get()),
                           float(self.eCf.get()), self.cbWfmFormat.get()]
                wfmRaw = pyarbtools.wfmBuilder.cw_pulse_generator(*wfmArgs)
            elif self.wfmType == 'Chirped Pulse':
                wfmArgs = [float(self.eFsWfm.get()), float(self.ePulseWidth.get()),
                           float(self.ePri.get()), float(self.eChirpBw.get()),
                           float(self.eCf.get()), self.cbWfmFormat.get()]
                wfmRaw = pyarbtools.wfmBuilder.chirp_generator(*wfmArgs)
            elif self.wfmType == 'Barker Coded Pulse':
                wfmArgs = [float(self.eFsWfm.get()), float(self.ePulseWidth.get()),
                           float(self.ePri.get()), self.cbCode.get(),
                           float(self.eCf.get()), self.cbWfmFormat.get()]
                wfmRaw = pyarbtools.wfmBuilder.barker_generator(*wfmArgs)
            elif self.wfmType == 'Multitone':
                wfmArgs = [float(self.eFsWfm.get()), float(self.eSpacing.get()),
                           int(self.eNumTones.get()), self.cbPhase.get(),
                           float(self.eCf.get()), self.cbWfmFormat.get()]
                wfmRaw = pyarbtools.wfmBuilder.multitone_generator(*wfmArgs)
            elif self.wfmType == 'Digital Modulation':
                wfmArgs = [float(self.eFsWfm.get()), float(self.eSymrate.get()),
                           self.cbModType.get(), int(self.eNumSymbols.get()),
                           self.cbFiltType.get(), float(self.eFiltAlpha.get()),
                           self.cbWfmFormat.get()]
                wfmRaw = pyarbtools.wfmBuilder.digmod_generator(*wfmArgs)
            else:
                raise ValueError('Invalid selection chosen, this should never happen.')

            name = self.eWfmName.get()
            names = [w['name'] for w in self.wfmList]
            try:
                if name in names:
                    idx = names.index(name)
                    ans = messagebox.askyesno(title='Overwrite?', message=f'"{name}" already exists in waveform list. Would you like to overwrite it?')
                    if not ans:
                        raise pyarbtools.error.WfmBuilderError()
                    else:
                        del(self.wfmList[idx])
                        self.lblName.configure(text='')
                        self.lblLength.configure(text='')
                        self.lblFormat.configure(text='')
                        self.btnWfmPlay.configure(state=tkinter.DISABLED)
                        self.btnWfmDownload.configure(state=tkinter.DISABLED)
                self.wfmList.append({'name': name, 'length': len(wfmRaw), 'format': self.cbWfmFormat.get(), 'wfmData': wfmRaw, 'dl': False})
                self.lbWfmList.delete(0, tkinter.END)
                idx = 0
                for w in self.wfmList:
                    self.lbWfmList.insert(tkinter.END, w['name'])
                    if w['dl']:
                        self.lbWfmList.itemconfig(idx, selectbackground='green', selectforeground='white')
                    else:
                        self.lbWfmList.itemconfig(idx, selectbackground='yellow', selectforeground='black')
                    idx += 1
                self.lbWfmList.selection_set(tkinter.END)
                self.lbWfmList.event_generate("<<ListboxSelect>>")

            except pyarbtools.error.WfmBuilderError:
                self.statusBar.configure(text=f'"{name}" already exists in waveform list. Please select an unused waveform name.', bg='red')
            self.statusBar.configure(text=f'"{name}" created.', bg='white')
        except Exception as e:
            self.statusBar.configure(text=repr(e), bg='red')

    def download_wfm(self, event=None):
        index = self.lbWfmList.curselection()[0]
        wfmTarget = self.wfmList[index]

        try:
            if 'M819' in self.inst.instId:
                segment = self.inst.download_wfm(wfmTarget['wfmData'], ch=int(self.cbChannel.get()), name=wfmTarget['name'], wfmFormat=wfmTarget['format'])
                self.wfmList[index]['segment'] = segment
                self.update_wfm_dl(index, dlState=True)
                if 'M8196A' in self.inst.instId:
                    for i in range(len(self.wfmList)):
                        print(i, self.wfmList[i]['dl'])
                        if i != index:
                            self.update_wfm_dl(i, dlState=False)
                        else:
                            self.update_wfm_dl(i, dlState=True)
                self.btnWfmPlay.configure(state=tkinter.ACTIVE)
                self.statusBar.configure(text=f'"{wfmTarget["name"]}" downloaded to instrument at segment {segment}.', bg='white')
            else:  # 'iq' format
                if wfmTarget['format'].lower() == 'real':
                    self.statusBar.configure(text='Invalid waveform format for VSG. Select a waveform with "IQ" format.', bg='red')
                else:
                    self.inst.download_wfm(wfmTarget['wfmData'], wfmTarget['name'])
                    self.update_wfm_dl(index, True)
                    self.btnWfmPlay.configure(state=tkinter.ACTIVE)
                    self.statusBar.configure(text=f'"{wfmTarget["name"]}" downloaded to instrument.', bg='white')
        except Exception as e:
            self.statusBar.configure(text=repr(e), bg='red')

    def update_wfm_dl(self, index, dlState):
        """Updates the appearance of a given waveform in the waveform list
        depending on its "downloaded" status"""

        self.wfmList[index]['dl'] = dlState
        if dlState:
            self.lbWfmList.itemconfig(index, selectbackground='green', selectforeground='white')
        else:
            self.lbWfmList.itemconfig(index, selectbackground='yellow', selectforeground='black')

    def play_wfm(self):
        index = self.lbWfmList.curselection()[0]
        wfmData = self.wfmList[index]

        try:
            if 'M819' in self.instKey:
                if self.instKey == 'M8196A':
                    self.inst.play(ch=int(self.cbChannel.get()))
                else:
                    self.inst.play(wfmData['segment'], ch=int(self.cbChannel.get()))
                self.statusBar.configure(text=f'"{wfmData["name"]}" playing out of channel {int(self.cbChannel.get())}', bg='white')
            else:
                self.inst.play(wfmData['name'])
                self.statusBar.configure(text=f'"{wfmData["name"]}" playing.', bg='white')
        except socketscpi.SockInstError as e:
            self.statusBar.configure(repr(e), bg='red')

    def change_channel(self, event=None):
        """Resets waveform play button to ensure that the segment is
        downloaded for the selected channel."""

        self.btnWfmPlay.configure(state=tkinter.DISABLED)

    def delete_wfm(self):
        """Deletes selected waveform from the waveform list."""
        index = self.lbWfmList.curselection()[0]
        try:
            if self.instKey in ['VSG', 'VXG']:
                self.inst.delete_wfm(self.wfmList[index]['name'])
            elif 'M819' in self.instKey:
                self.inst.delete_segment(self.wfmList[index]['segment'], int(self.cbChannel.get()))
            self.statusBar.configure(text=f'"{self.wfmList[index]["name"]}" deleted from arb memory.')
        except IndexError:
            # wfm list is empty
            pass
        except AttributeError:
            # No arb connected
            pass
        except KeyError:
            # wfm hasn't been downloaded to instrument
            pass
        finally:
            del self.wfmList[index]
            self.lbWfmList.delete(index)
            if len(self.wfmList) == 0:
                self.btnWfmDownload.configure(state=tkinter.DISABLED)
                self.btnWfmPlay.configure(state=tkinter.DISABLED)
                self.lblName.configure(text='')
                self.lblLength.configure(text='')
                self.lblFormat.configure(text='')

    def clear_all_wfm(self):
        """Deletes all waveforms from waveform list."""
        try:
            self.inst.clear_all_wfm()
        except AttributeError:
            pass  # nothings is connected
        self.wfmList = []
        self.lbWfmList.delete(0, tkinter.END)
        self.btnWfmDownload.configure(state=tkinter.DISABLED)
        self.btnWfmPlay.configure(state=tkinter.DISABLED)
        self.btnWfmClearAll.configure(state=tkinter.DISABLED)
        self.btnWfmDelete.configure(state=tkinter.DISABLED)
        self.lblName.configure(text='')
        self.lblLength.configure(text='')
        self.lblFormat.configure(text='')
        self.statusBar.configure(text='All waveforms cleared from arb memory.', bg='white')

    def select_wfm(self, event=None):
        try:
            index = self.lbWfmList.curselection()[0]
            wfmTarget = self.wfmList[index]
            self.lblName.configure(text=wfmTarget['name'])
            self.lblLength.configure(text=wfmTarget['length'])
            self.lblFormat.configure(text=wfmTarget['format'])
            self.btnWfmDelete.configure(state=tkinter.ACTIVE)
            self.btnWfmClearAll.configure(state=tkinter.ACTIVE)
            if self.inst:
                self.btnWfmDownload.configure(state=tkinter.ACTIVE)
                if wfmTarget['dl']:
                    self.btnWfmPlay.configure(state=tkinter.ACTIVE)
                else:
                    self.btnWfmPlay.configure(state=tkinter.DISABLED)
            self.statusBar.configure(text='', bg='white')
        except IndexError:
            self.statusBar.configure(text='No waveforms defined.', bg='white')

    def inst_write(self):
        self.inst.write(self.eScpi.get())
        self.inst.write('*cls')
        self.lblReadout.configure(text=f'"{self.eScpi.get()}" command sent')

    def inst_query(self):
        try:
            self.inst.socket.settimeout(1)
            response = self.inst.query(self.eScpi.get())
            self.inst.write('*cls')
            self.lblReadout.configure(text=response)
        except Exception as e:
            self.lblReadout.configure(text=str(e))
        finally:
            self.inst.socket.settimeout(3)

    def inst_err_check(self):
        try:
            self.inst.err_check()
            self.lblReadout.configure(text='No error')
        except Exception as e:
            self.lblReadout.configure(text=str(e))
        finally:
            self.inst.write('*cls')

    def inst_preset(self):
        self.inst.write('*rst')
        self.inst.query('*opc?')
        self.lblReadout.configure(text='Instrument preset complete')

    def inst_flush(self):
        """Flushes the SCPI I/O buffer."""
        self.inst.socket.settimeout(0.25)
        # noinspection PyBroadException
        try:
            self.inst.query('')
        except Exception:
            pass
        finally:
            self.inst.socket.settimeout(3)

    def instrument_connect(self, debug=False):
        """Selects the appropriate instrument class based on combobox selection."""
        self.ipAddress = self.eInstIPAddress.get()
        try:
            ipaddress.ip_address(self.ipAddress)
        except ValueError:
            self.statusBar.configure(text='Invalid IP Address.', bg='red')

        self.instKey = self.cbInstruments.get()
        try:
            # Connect to instrument
            if not debug:
                self.inst = self.instClasses[self.instKey](self.ipAddress, timeout=2)
                self.statusBar.configure(text=f'Connected to {self.inst.instId}', bg='white')

            self.lblInstStatus.configure(text='Connected', bg='green')
            self.open_inst_config()
            self.btnWrite.configure(state=tkinter.ACTIVE)
            self.btnQuery.configure(state=tkinter.ACTIVE)
            self.btnErrCheck.configure(state=tkinter.ACTIVE)
            self.btnPreset.configure(state=tkinter.ACTIVE)
            self.btnFlush.configure(state=tkinter.ACTIVE)
            self.eScpi.configure(state=tkinter.NORMAL)
            self.lblReadout.configure(text='Ready for SCPI interaction')
            self.btnInstConnect.configure(text='Disconnect', command=self.instrument_disconnect)
        except Exception as e:
            self.lblInstStatus.configure(text='Not Connected', bg='red')
            self.statusBar.configure(text=repr(e), bg='red')

    def instrument_disconnect(self):
        """Disconnects from connected instrument and adjusts GUI accordingly."""
        self.inst.disconnect()
        self.inst = None
        self.statusBar.configure(text='Welcome', bg='white')
        self.btnWrite.configure(state=tkinter.DISABLED)
        self.btnQuery.configure(state=tkinter.DISABLED)
        self.btnErrCheck.configure(state=tkinter.DISABLED)
        self.btnPreset.configure(state=tkinter.DISABLED)
        self.btnFlush.configure(state=tkinter.DISABLED)
        self.eScpi.configure(state=tkinter.DISABLED)
        self.lblReadout.configure(text='Connect to instrument')
        self.lblInstStatus.configure(text='Not Connected', bg='red')
        self.btnInstConnect.configure(text='Connect', command=self.instrument_connect)

        self.disable_wfmFrame()
        self.clear_all_wfm()

        # Reset instrument config frame
        self.configFrame.destroy()
        self.configFrame = tkinter.Frame(self.master, bd=5)
        self.configFrame.grid(row=1, column=0, rowspan=2)

    def instrument_configure(self):
        """Pulls settings from config frame and calls instrument-specific measurement functions"""
        try:
            self.inst.clear_all_wfm()
            if self.cbPreset.get() == 'True':
                self.inst.write('*rst')
            if self.instKey == 'M8190A':
                configArgs = {'res': self.resArgs[self.cbRes.get()],
                              'clkSrc': self.clkSrcArgs[self.cbClkSrc.get()],
                              'fs': float(self.eFs.get()),
                              'refSrc': self.refSrcArgs[self.cbRefSrc.get()],
                              'refFreq': float(self.eRefFreq.get()),
                              'out1': self.outArgs[self.cbOut1.get()],
                              'out2': self.outArgs[self.cbOut2.get()],
                              'func1': self.funcArgs[self.cbFunc1.get()],
                              'func2': self.funcArgs[self.cbFunc2.get()],
                              'cf1': float(self.eCf1.get()),
                              'cf2': float(self.eCf2.get())}
            elif self.instKey == 'M8195A':
                configArgs = {'dacMode': self.dacModeArgs[self.cbDacMode.get()],
                             'memDiv': int(self.cbMemDiv.get()),
                             'fs': float(self.eFs.get()),
                             'refSrc': self.refSrcArgs[self.cbRefSrc.get()],
                             'refFreq': float(self.eRefFreq.get()),
                             'func': self.funcArgs[self.cbFunc.get()]}
            elif self.instKey == 'M8196A':
                configArgs = {'dacMode': self.dacModeArgs[self.cbDacMode.get()],
                              'fs': float(self.eFs.get()),
                              'refSrc': self.refSrcArgs[self.cbRefSrc.get()],
                              'refFreq': float(self.eRefFreq.get())}
            elif self.instKey in ['VSG', 'VXG']:
                configArgs = {'rfState': self.rfStateArgs[self.cbRfState.get()],
                              'modState': self.modStateArgs[self.cbModState.get()],
                              'cf': float(self.eCf.get()),
                              'amp': int(self.eAmp.get()),
                              'alcState': self.alcStateArgs[self.cbAlcState.get()],
                              'iqScale': int(self.eIqScale.get()),
                              'refSrc': self.refSrcArgs[self.cbRefSrc.get()],
                              'fs': float(self.eFs.get())}
            else:
                raise ValueError('Invalid instrument selected. This should never happen.')
            self.inst.configure(**configArgs)
            self.memDiv_select()
            self.res_select()
            self.statusBar.configure(text=f'{self.instKey} configured.', bg='white')
        except Exception as e:
            self.statusBar.configure(text=repr(e), bg='red')
        self.cbWfmType.event_generate("<<ComboboxSelected>>")
        self.cbWfmType.configure(state='readonly')

    def enable_wfmTypeSelect(self):
        self.cbWfmType.configure(state='readonly')

    def disable_wfmFrame(self):
        for c in self.wfmFrame.winfo_children():
            c.configure(state=tkinter.DISABLED)
        self.cbWfmType.configure(state=tkinter.DISABLED)

    def open_inst_config(self):
        """Creates a new frame with instrument-specific configuration fields."""
        self.configFrame.destroy()
        self.configFrame = tkinter.Frame(self.master, bd=5)
        self.configFrame.grid(row=1, column=0, rowspan=2, sticky=tkinter.N)

        configBtn = ttk.Button(self.configFrame, text='Configure', command=self.instrument_configure)

        if self.instKey == 'M8190A':
            resLabel = tkinter.Label(self.configFrame, text='Resolution')
            self.resArgs = {'12 Bit': 'wsp', '14 Bit': 'wpr', '3x Interpolation': 'intx3', '12x Interpolation': 'intx12',
                            '24x Interpolation': 'intx24', '48x Interpolation': 'intx48'}
            self.cbRes = ttk.Combobox(self.configFrame, state='readonly', values=list(self.resArgs.keys()), width=self.cbWidth)
            self.cbRes.current(0)
            self.cbRes.bind("<<ComboboxSelected>>", self.res_select)

            clkSrcLabel = tkinter.Label(self.configFrame, text='Clock Source')
            self.clkSrcArgs = {'Internal': 'int', 'External': 'ext'}
            self.cbClkSrc = ttk.Combobox(self.configFrame, state='readonly', values=list(self.clkSrcArgs.keys()), width=self.cbWidth)
            self.cbClkSrc.current(0)

            fsLabel = tkinter.Label(self.configFrame, text='Sample Rate')
            fsVar = tkinter.StringVar()
            self.eFs = tkinter.Entry(self.configFrame, textvariable=fsVar)
            fsVar.set('7.2e9')

            bbfsLabel = tkinter.Label(self.configFrame, text='Baseband Sample Rate')
            self.lblBbFs = tkinter.Label(self.configFrame, text=0)

            refSrcLabel = tkinter.Label(self.configFrame, text='Reference Source')
            self.refSrcArgs = {'AXIe': 'axi', 'Internal': 'int', 'External': 'ext'}
            self.cbRefSrc = ttk.Combobox(self.configFrame, state='readonly', values=list(self.refSrcArgs.keys()), width=self.cbWidth)
            self.cbRefSrc.current(0)

            refFreqLabel = tkinter.Label(self.configFrame, text='Reference Frequency')
            refFreqVar = tkinter.StringVar()
            self.eRefFreq = tkinter.Entry(self.configFrame, textvariable=refFreqVar)
            refFreqVar.set('100e6')

            out1Label = tkinter.Label(self.configFrame, text='Ch 1 Output Path')
            self.outArgs = {'Direct DAC': 'dac', 'AC Amplified': 'ac', 'DC Amplified': 'dc'}
            self.cbOut1 = ttk.Combobox(self.configFrame, state='readonly', values=list(self.outArgs.keys()), width=self.cbWidth)
            self.cbOut1.current(0)

            out2Label = tkinter.Label(self.configFrame, text='Ch 2 Output Path')
            self.cbOut2 = ttk.Combobox(self.configFrame, state='readonly', values=list(self.outArgs.keys()), width=self.cbWidth)
            self.cbOut2.current(0)

            func1Label = tkinter.Label(self.configFrame, text='Ch 1 Function')
            # self.funcArgs = {'Arb Waveform': 'arb', 'Sequence': 'sts', 'Scenario': 'stc'}
            self.funcArgs = {'Arb Waveform': 'arb'}
            self.cbFunc1 = ttk.Combobox(self.configFrame, state='readonly', values=list(self.funcArgs.keys()), width=self.cbWidth)
            self.cbFunc1.current(0)

            func2Label = tkinter.Label(self.configFrame, text='Ch 2 Function')
            self.cbFunc2 = ttk.Combobox(self.configFrame, state='readonly', values=list(self.funcArgs.keys()), width=self.cbWidth)
            self.cbFunc2.current(0)

            cf1Label = tkinter.Label(self.configFrame, text='Ch 1 Carrier Frequency')
            cf1Var = tkinter.StringVar()
            self.eCf1 = tkinter.Entry(self.configFrame, textvariable=cf1Var)
            cf1Var.set('1e9')

            cf2Label = tkinter.Label(self.configFrame, text='Ch 2 Carrier Frequency')
            cf2Var = tkinter.StringVar()
            self.eCf2 = tkinter.Entry(self.configFrame, textvariable=cf2Var)
            cf2Var.set('1e9')

            # Layout
            r = 0
            resLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbRes.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            clkSrcLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbClkSrc.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            fsLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.eFs.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            bbfsLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.lblBbFs.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            refSrcLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbRefSrc.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            refFreqLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.eRefFreq.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            out1Label.grid(row=r, column=0, sticky=tkinter.E)
            self.cbOut1.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            out2Label.grid(row=r, column=0, sticky=tkinter.E)
            self.cbOut2.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            func1Label.grid(row=r, column=0, sticky=tkinter.E)
            self.cbFunc1.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            func2Label.grid(row=r, column=0, sticky=tkinter.E)
            self.cbFunc2.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            cf1Label.grid(row=r, column=0, sticky=tkinter.E)
            self.eCf1.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            cf2Label.grid(row=r, column=0, sticky=tkinter.E)
            self.eCf2.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            # Special
            self.cbChannel.configure(values=[1, 2], state='readonly')
            self.cbChannel.current(0)
            self.cbRes.event_generate("<<ComboboxSelected>>")

        elif self.instKey == 'M8195A':
            dacModeLabel = tkinter.Label(self.configFrame, text='DAC Mode')
            self.dacModeArgs = {'Single': 'single', 'Dual': 'dual',
                                'Four': 'four', 'Marker': 'marker',
                                'Dual Channel Dup.': 'dcd',
                                'Dual Channel Marker': 'dcm'}
            # For future help box to explain what the different DAC modes mean
            # self.dacModeArgs = {'Single (Ch 1)': 'single', 'Dual (Ch 1 & 4)': 'dual',
            #                     'Four (All Ch)': 'four', 'Marker (Sig Ch 1, Mkr Ch 3 & 4)': 'marker',
            #                     'Dual Channel Duplicate (Ch 3 & 4 copy Ch 1 & 2)': 'dcd',
            #                     'Dual Channel Marker (Sign Ch 1 & 2, Ch 1 mkr on Ch 3 & 4)': 'dcm'}
            self.cbDacMode = ttk.Combobox(self.configFrame, state='readonly', values=list(self.dacModeArgs.keys()), width=self.cbWidth)
            self.cbDacMode.current(0)

            memDivLabel = tkinter.Label(self.configFrame, text='Sample Rate Divider')
            memDivList = [1, 2, 4]
            self.cbMemDiv = ttk.Combobox(self.configFrame, state='readonly', values=memDivList, width=self.cbWidth)
            self.cbMemDiv.current(0)
            self.cbMemDiv.bind("<<ComboboxSelected>>", self.memDiv_select)

            fsLabel = tkinter.Label(self.configFrame, text='Sample Rate')
            fsVar = tkinter.StringVar()
            self.eFs = tkinter.Entry(self.configFrame, textvariable=fsVar)
            fsVar.set('64e9')

            effFsLabel = tkinter.Label(self.configFrame, text='Effective Sample Rate')
            self.effFs = float(self.eFs.get()) / float(self.cbMemDiv.get())
            self.lblEffFs = tkinter.Label(self.configFrame, text=f'{self.effFs:.2e}')
            refSrcLabel = tkinter.Label(self.configFrame, text='Reference Source')

            self.refSrcArgs = {'AXIe': 'axi', 'Internal': 'int', 'External': 'ext'}
            self.cbRefSrc = ttk.Combobox(self.configFrame, state='readonly',
                                         values=list(self.refSrcArgs.keys()), width=self.cbWidth)
            self.cbRefSrc.current(0)

            refFreqLabel = tkinter.Label(self.configFrame, text='Reference Frequency')
            refFreqVar = tkinter.StringVar()
            self.eRefFreq = tkinter.Entry(self.configFrame, textvariable=refFreqVar)
            refFreqVar.set('100e6')

            funcLabel = tkinter.Label(self.configFrame, text='Function')
            # self.funcArgs = {'Arb Waveform': 'arb', 'Sequence': 'sts', 'Scenario': 'stc'}
            self.funcArgs = {'Arb Waveform': 'arb'}
            self.cbFunc = ttk.Combobox(self.configFrame, state='readonly', values=list(self.funcArgs.keys()), width=self.cbWidth)
            self.cbFunc.current(0)

            # Layout
            r = 0
            dacModeLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbDacMode.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            memDivLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbMemDiv.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            fsLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.eFs.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            effFsLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.lblEffFs.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            refSrcLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbRefSrc.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            refFreqLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.eRefFreq.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            funcLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbFunc.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            # Special
            self.cbChannel.configure(values=[1, 2, 3, 4], state='readonly')
            self.cbChannel.current(0)

        elif self.instKey == 'M8196A':
            dacModeLabel = tkinter.Label(self.configFrame, text='DAC Mode')
            self.dacModeArgs = {'Single': 'single', 'Dual': 'dual',
                                'Four': 'four', 'Marker': 'marker',
                                'Dual Channel Marker': 'dcm'}
            # self.dacModeArgs = {'Single (Ch 1)': 'single', 'Dual (Ch 1 & 4)': 'dual',
            #                     'Four (All Ch)': 'four', 'Marker (Sig Ch 1, Mkr Ch 2 & 3)': 'marker',
            #                     'Dual Channel Marker (Sign Ch 1 & 4, Ch 1 mkr on Ch 2 & 3)': 'dcm'}
            self.cbDacMode = ttk.Combobox(self.configFrame, state='readonly',
                                          values=list(self.dacModeArgs.keys()), width=self.cbWidth)
            self.cbDacMode.current(0)

            fsLabel = tkinter.Label(self.configFrame, text='Sample Rate')
            fsVar = tkinter.StringVar()
            self.eFs = tkinter.Entry(self.configFrame, textvariable=fsVar)
            fsVar.set('92e9')

            refSrcLabel = tkinter.Label(self.configFrame, text='Reference Source')

            self.refSrcArgs = {'AXIe': 'axi', 'Internal': 'int', 'External': 'ext'}
            self.cbRefSrc = ttk.Combobox(self.configFrame, state='readonly',
                                         values=list(self.refSrcArgs.keys()), width=self.cbWidth)
            self.cbRefSrc.current(0)

            refFreqLabel = tkinter.Label(self.configFrame, text='Reference Frequency')
            refFreqVar = tkinter.StringVar()
            self.eRefFreq = tkinter.Entry(self.configFrame, textvariable=refFreqVar)
            refFreqVar.set('100e6')

            # Layout
            r = 0
            dacModeLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbDacMode.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            fsLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.eFs.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            refSrcLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbRefSrc.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            refFreqLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.eRefFreq.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            # Special
            self.cbChannel.configure(values=[1, 2, 3, 4], state='readonly')
            self.cbChannel.current(0)

        elif self.instKey in ['VSG', 'VXG']:
            rfStateLabel = tkinter.Label(self.configFrame, text='RF State')
            self.rfStateArgs = {'On': 1, 'Off': 0}
            self.cbRfState = ttk.Combobox(self.configFrame, state='readonly', values=list(self.rfStateArgs.keys()), width=self.cbWidth)
            self.cbRfState.current(0)

            modStateLabel = tkinter.Label(self.configFrame, text='Modulation State')
            self.modStateArgs = {'On': 1, 'Off': 0}
            self.cbModState = ttk.Combobox(self.configFrame, state='readonly', values=list(self.modStateArgs.keys()), width=self.cbWidth)
            self.cbModState.current(0)

            cfLabel = tkinter.Label(self.configFrame, text='Carrier Frequency')
            cfVar = tkinter.StringVar()
            self.eCf = tkinter.Entry(self.configFrame, textvariable=cfVar)
            cfVar.set('1e9')

            ampLabel = tkinter.Label(self.configFrame, text='Amplitude (dBm)')
            ampVar = tkinter.StringVar()
            self.eAmp = tkinter.Entry(self.configFrame, textvariable=ampVar)
            ampVar.set(-20)

            alcStateLabel = tkinter.Label(self.configFrame, text='ALC State')
            self.alcStateArgs = {'On': 1, 'Off': 0}
            self.cbAlcState = ttk.Combobox(self.configFrame, state='readonly', values=list(self.alcStateArgs.keys()), width=self.cbWidth)
            self.cbAlcState.current(0)

            iqScaleLabel = tkinter.Label(self.configFrame, text='IQ Scale (%)')
            iqScaleVar = tkinter.StringVar()
            self.eIqScale = tkinter.Entry(self.configFrame, textvariable=iqScaleVar)
            iqScaleVar.set(70)

            refSrcLabel = tkinter.Label(self.configFrame, text='Reference Source')
            self.refSrcArgs = {'Internal': 'int', 'External': 'ext'}
            self.cbRefSrc = ttk.Combobox(self.configFrame, state='readonly', values=list(self.refSrcArgs.keys()), width=self.cbWidth)
            self.cbRefSrc.current(0)

            fsLabel = tkinter.Label(self.configFrame, text='Sample Rate')
            fsVar = tkinter.StringVar()
            self.eFs = tkinter.Entry(self.configFrame, textvariable=fsVar)
            fsVar.set('200e6')

            # Layout
            r = 0
            rfStateLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbRfState.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            modStateLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbModState.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            cfLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.eCf.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            ampLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.eAmp.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            alcStateLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbAlcState.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            iqScaleLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.eIqScale.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            refSrcLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.cbRefSrc.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            fsLabel.grid(row=r, column=0, sticky=tkinter.E)
            self.eFs.grid(row=r, column=1, sticky=tkinter.W)
            r += 1

            # Special
            self.cbChannel.configure(state=tkinter.DISABLED)
        else:
            raise ValueError('You got an argument that was not in the instrument select combobox. This should never happen.')

        lblPreset = tkinter.Label(self.configFrame, text='Preset')
        presetList = ['False', 'True']
        self.cbPreset = ttk.Combobox(self.configFrame, state='readonly', values=presetList, width=self.cbWidth)
        self.cbPreset.current(0)

        lblPreset.grid(row=r, column=0, sticky=tkinter.E)
        self.cbPreset.grid(row=r, column=1, sticky=tkinter.W)
        r += 1
        configBtn.grid(row=r, column=0, columnspan=2)

    def memDiv_select(self, event=None):
        """Updates effective sample rate."""
        # self.effFs = float(self.eFs.get()) / float(self.cbMemDiv.get())
        # self.lblEffFs.configure(text=f'{self.effFs:.2e}')
        if type(self.inst) == pyarbtools.instruments.M8195A:
            self.lblEffFs.configure(text=f'{self.inst.effFs:.2e}')

    def res_select(self, event=None):
        """Updates baseband sample rate."""
        if type(self.inst) == pyarbtools.instruments.M8190A:
            if 'intx' in self.resArgs[self.cbRes.get()].lower():
                self.lblBbFs.configure(text=f'{self.inst.bbfs:.2e}')
                self.eCf1.configure(state=tkinter.NORMAL)
                self.eCf2.configure(state=tkinter.NORMAL)
            else:
                self.lblBbFs.configure(text=f'{self.inst.fs:.2e}')
                self.eCf1.configure(state=tkinter.DISABLED)
                self.eCf2.configure(state=tkinter.DISABLED)


def main():
    root = tkinter.Tk()
    root.resizable(False, False)
    root.title('Keysight PyArbTools')

    PyarbtoolsGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
