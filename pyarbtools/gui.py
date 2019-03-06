"""
gui
Author: Morgan Allison, Keysight RF/uW Application Engineer
A much-needed GUI for pyarbtools.
"""

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import ipaddress
import pyarbtools

class PyarbtoolsGUI:
    def __init__(self, master):
        # Constants
        self.instClasses = {'M8190A': pyarbtools.instruments.M8190A,
                            'M8195A': pyarbtools.instruments.M8195A,
                            'M8196A': pyarbtools.instruments.M8196A,
                            'VSG': pyarbtools.instruments.VSG,
                            'AnalogUXG': pyarbtools.instruments.AnalogUXG,
                            'VectorUXG': pyarbtools.instruments.VectorUXG}

        # Variables
        # self.ipAddress = '127.0.0.1'
        self.ipAddress = '141.121.210.122'
        self.inst = None

        """Master Frame Setup"""
        self.master = master

        # master Widgets
        setupFrame = Frame(self.master, bd=5)
        self.configFrame = Frame(self.master, bd=5)
        self.interactFrame = Frame(self.master, bd=5)
        self.wfmTypeSelectFrame = Frame(self.master, bd=5)
        self.wfmFrame = Frame(self.master, bd=5)
        placeHolder = Frame(self.master, bd=5)
        self.wfmListFrame = Frame(self.master, bd=5)
        statusBarFrame = Frame(self.master)

        # Master frame geometry
        r = 0
        setupFrame.grid(row=r, column=0, sticky=N)
        self.wfmTypeSelectFrame.grid(row=r, column=1, sticky=N)
        self.interactFrame.grid(row=r, column=2, sticky=N, rowspan=2)
        r += 1
        self.configFrame.grid(row=r, column=0)
        self.wfmFrame.grid(row=r, column=1)
        r += 1
        placeHolder.grid(row=r, column=1)
        self.wfmListFrame.grid(row=r, column=1)
        r += 1
        statusBarFrame.grid(row=r, column=0, columnspan=4)

        """setupFrame"""
        # setupFrame Widgets
        self.lblInstruments = Label(setupFrame, text='Instrument Class')
        self.cbInstruments = ttk.Combobox(setupFrame, state='readonly', values=list(self.instClasses.keys()))
        self.cbInstruments.current(3)

        v = StringVar()
        self.lblInstIPAddress = Label(setupFrame, text='Instrument IP Address')
        self.eInstIPAddress = Entry(setupFrame, textvariable=v)
        v.set(self.ipAddress)

        self.lblInstStatus = Label(setupFrame, text='Not Connected', bg='red', width=13)
        self.btnInstConnect = Button(setupFrame, text='Connect', command=self.instrument_connect)

        # setupFrame Geometry
        r = 0
        self.lblInstruments.grid(row=r, column=0)
        self.lblInstIPAddress.grid(row=r, column=1)
        self.lblInstStatus.grid(row=r, column=2)
        r += 1

        self.cbInstruments.grid(row=r, column=0)
        self.eInstIPAddress.grid(row=r, column=1)
        self.btnInstConnect.grid(row=r, column=2)

        """configFrame"""
        # configFrame Widgets

        """interactFrame"""
        # interactFrame Widgets
        lblScpi = Label(self.interactFrame, text='Interactive SCPI I/O')
        scpiString = StringVar()
        self.eScpi = Entry(self.interactFrame, textvariable=scpiString, width=40)
        scpiString.set('*idn?')

        btnWidth = 9
        self.btnWrite = Button(self.interactFrame, text='Write', command=self.inst_write, width=btnWidth, state=DISABLED)
        self.btnQuery = Button(self.interactFrame, text='Query', command=self.inst_query, width=btnWidth, state=DISABLED)
        self.btnErrCheck = Button(self.interactFrame, text='Err Check', command=self.inst_err_check, width=btnWidth, state=DISABLED)
        self.btnPreset = Button(self.interactFrame, text='Preset', command=self.inst_preset, width=btnWidth, state=DISABLED)

        lblReadoutTitle = Label(self.interactFrame, text='SCPI Readout', width=40)
        self.lblReadout = Label(self.interactFrame, text='Connect to instrument', width=40, relief='sunken')

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
        lblReadoutTitle.grid(row=r, columnspan=4)
        r += 1
        self.lblReadout.grid(row=r, columnspan=4)

        """wfmTypeSelectFrame"""
        # wfmTypeSelectFrame Widgets
        wfmLabel = Label(self.wfmTypeSelectFrame, text='Waveform Type')
        self.wfmTypeList = ['AM', 'Chirp', 'Barker Code', 'Digital Modulation', 'Multitone']
        self.cbWfmType = ttk.Combobox(self.wfmTypeSelectFrame, state='readonly', values=self.wfmTypeList)
        self.cbWfmType.current(0)

        iqSelectList = ['IQ', 'Real']
        self.cbIqSelect = ttk.Combobox(self.wfmTypeSelectFrame, state='readonly', values=iqSelectList)
        self.cbIqSelect.current(0)

        self.cbWfmType.bind("<<ComboboxSelected>>", self.open_wfm_builder)
        self.cbIqSelect.bind("<<ComboboxSelected>>", self.open_wfm_builder)

        # wfmTypeSelectFrame Geometry
        r = 0
        wfmLabel.grid(row=r, column=0)
        r += 1
        self.cbWfmType.grid(row=r)
        r += 1
        self.cbIqSelect.grid(row=r)

        """wfmFrame"""
        self.open_wfm_builder()

        """wfmListFrame"""
        # wfmListFrame Widgets
        lblWfmList = Label(self.wfmListFrame, text='Waveform List')
        lblSegment = Label(self.wfmListFrame, text='Segment:')
        lblNameHdr = Label(self.wfmListFrame, text='Name:')
        self.lblName = Label(self.wfmListFrame, text='Test')
        lblLengthHdr = Label(self.wfmListFrame, text='Length:')
        self.lblLength = Label(self.wfmListFrame, text='1024')
        lblFormatHdr = Label(self.wfmListFrame, text='Format:')
        self.lblFormat = Label(self.wfmListFrame, text='IQ')
        self.wfmList = Listbox(self.wfmListFrame, selectmode='single', width=8)

        self.wfmList.insert(END, '0')

        # wfmListFrame Geometry
        r = 0
        lblWfmList.grid(row=r, columnspan=2)
        r += 1
        lblSegment.grid(row=r, sticky=W)
        r += 1
        self.wfmList.grid(row=r, sticky=W, rowspan=10)
        lblNameHdr.grid(row=r, column=1)
        r += 1
        self.lblName.grid(row=r, column=1)
        r += 1
        lblLengthHdr.grid(row=r, column=1)
        r += 1
        self.lblLength.grid(row=r, column=1)
        r += 1
        lblFormatHdr.grid(row=r, column=1)
        r += 1
        self.lblFormat.grid(row=r, column=1)

        """statusBarFrame"""
        # statusBarFrame Widgets
        self.statusBar = Label(statusBarFrame, text='Welcome', width=130, relief=SUNKEN)
        self.statusBar.grid(row=0, sticky=N+S+E+W)



    def open_wfm_builder(self, event=None):
        self.wfmFrame.destroy()
        self.wfmFrame = Frame(self.master, bd=5)
        self.wfmFrame.grid(row=1, column=1, sticky=N)

        self.wfmType = self.cbWfmType.get()
        if self.wfmType == 'Digital Modulation' or self.wfmType == 'Multitone' or self.wfmType == 'AM':
            self.cbIqSelect.configure(state=DISABLED)
            self.cbIqSelect.current(0)
        else:
            self.cbIqSelect.configure(state=ACTIVE)
            self.genMode = self.cbIqSelect.get()

        if self.wfmType == 'AM':
            lblFs = Label(self.wfmFrame, text='Sample Rate')
            fsVar = StringVar()
            self.eFs = Entry(self.wfmFrame, textvariable=fsVar)
            try:
                fsVar.set(str(self.inst.fs))
            except AttributeError as e:
                fsVar.set('100e6')

            lblAmDepth = Label(self.wfmFrame, text='AM Depth')
            amDepthVar = StringVar()
            self.eAmDepth = Entry(self.wfmFrame, textvariable=amDepthVar)
            amDepthVar.set('50')

            lblModRate = Label(self.wfmFrame, text='Modulation Rate')
            modRateVar = StringVar()
            self.eModRate = Entry(self.wfmFrame, textvariable=modRateVar)
            modRateVar.set('100e3')

            # AM Geometry
            r = 0
            lblFs.grid(row=r, column=0, sticky=E)
            self.eFs.grid(row=r, column=1, sticky=W)

            r += 1
            lblAmDepth.grid(row=r, column=0, sticky=E)
            self.eAmDepth.grid(row=r, column=1, sticky=W)

            r += 1
            lblModRate.grid(row=r, column=0, sticky=E)
            self.eModRate.grid(row=r, column=1, sticky=W)


        elif self.wfmType == 'Chirp':
            lblFs = Label(self.wfmFrame, text='Sample Rate')
            fsVar = StringVar()
            self.eFs = Entry(self.wfmFrame, textvariable=fsVar)
            try:
                fsVar.set(str(self.inst.fs))
            except AttributeError as e:
                fsVar.set('100e6')

            lblPulseWidth = Label(self.wfmFrame, text='Pulse Width')
            lengthVar = StringVar()
            self.ePulseWidth = Entry(self.wfmFrame, textvariable=lengthVar)
            lengthVar.set('1e-6')

            lblPri = Label(self.wfmFrame, text='Pulse Rep Interval')
            priVar = StringVar()
            self.ePri = Entry(self.wfmFrame, textvariable=priVar)
            priVar.set('10e-6')

            lblChirpBw = Label(self.wfmFrame, text='Chirp Bandwidth')
            chirpBwVar = StringVar()
            self.eChirpBw = Entry(self.wfmFrame, textvariable=chirpBwVar)
            chirpBwVar.set('40e6')

            # Chirp Geometry
            r = 0
            lblFs.grid(row=r, column=0, sticky=E)
            self.eFs.grid(row=r, column=1, sticky=W)

            r += 1
            lblPulseWidth.grid(row=r, column=0, sticky=E)
            self.ePulseWidth.grid(row=r, column=1, sticky=W)

            r += 1
            lblPri.grid(row=r, column=0, sticky=E)
            self.ePri.grid(row=r, column=1, sticky=W)

            r += 1
            lblChirpBw.grid(row=r, column=0, sticky=E)
            self.eChirpBw.grid(row=r, column=1, sticky=W)

            if self.genMode == 'Real':
                lblCf = Label(self.wfmFrame, text='Carrier Frequency')
                cfVar = StringVar()
                self.eCf = Entry(self.wfmFrame, textvariable=cfVar)
                cfVar.set('1e9')

                r += 1
                lblCf.grid(row=r, column=0, sticky=E)
                self.eCf.grid(row=r, column=1, sticky=W)

        elif self.wfmType == 'Barker Code':
            lblFs = Label(self.wfmFrame, text='Sample Rate')
            fsVar = StringVar()
            self.eFs = Entry(self.wfmFrame, textvariable=fsVar)
            try:
                fsVar.set(str(self.inst.fs))
            except AttributeError as e:
                fsVar.set('100e6')

            lblPulseWidth = Label(self.wfmFrame, text='Pulse Width')
            lengthVar = StringVar()
            self.ePulseWidth = Entry(self.wfmFrame, textvariable=lengthVar)
            lengthVar.set('1e-6')

            lblPri = Label(self.wfmFrame, text='Pulse Rep Interval')
            priVar = StringVar()
            self.ePri = Entry(self.wfmFrame, textvariable=priVar)
            priVar.set('10e-6')

            lblCode = Label(self.wfmFrame, text='Code Order')
            codeList = ['b2', 'b3', 'b41', 'b42', 'b5', 'b7', 'b11', 'b13']
            self.cbCode = ttk.Combobox(self.wfmFrame, state='readonly', values=codeList)
            self.cbCode.current(0)

            # Barker Geometry
            r = 0

            lblFs.grid(row=r, column=0, sticky=E)
            self.eFs.grid(row=r, column=1, sticky=W)

            r += 1
            lblPulseWidth.grid(row=r, column=0, sticky=E)
            self.ePulseWidth.grid(row=r, column=1, sticky=W)

            r += 1
            lblPri.grid(row=r, column=0, sticky=E)
            self.ePri.grid(row=r, column=1, sticky=W)

            r += 1
            lblCode.grid(row=r, column=0, sticky=E)
            self.cbCode.grid(row=r, column=1, sticky=W)

            if self.genMode == 'Real':
                lblCf = Label(self.wfmFrame, text='Carrier Frequency')
                cfVar = StringVar()
                self.eCf = Entry(self.wfmFrame, textvariable=cfVar)
                cfVar.set('1e9')

                r += 1
                lblCf.grid(row=r, column=0, sticky=E)
                self.eCf.grid(row=r, column=1, sticky=W)

        elif self.wfmType == 'Digital Modulation':
            lblFs = Label(self.wfmFrame, text='Sample Rate')
            fsVar = StringVar()
            self.eFs = Entry(self.wfmFrame, textvariable=fsVar)
            try:
                fsVar.set(str(self.inst.fs))
            except AttributeError as e:
                fsVar.set('100e6')

            lblModType = Label(self.wfmFrame, text='Modulation Type')
            modTypeList = ['bpsk', 'qpsk', '8psk', '16psk', 'qam16', 'qam32', 'qam64', 'qam128', 'qam256']
            self.cbModType = ttk.Combobox(self.wfmFrame, state='readonly', values=modTypeList)
            self.cbModType.current(0)

            lblSymrate = Label(self.wfmFrame, text='Symbol Rate')
            symRateVar = StringVar()
            self.eSymrate = Entry(self.wfmFrame, textvariable=symRateVar)
            symRateVar.set('10e6')

            lblPrbsOrder = Label(self.wfmFrame, text='PRBS Order')
            prbsOrderList = [7, 9, 11, 13, 15, 17]
            self.cbPrbsOrder = ttk.Combobox(self.wfmFrame, state='readonly', values=prbsOrderList)
            self.cbPrbsOrder.current(0)

            lblFiltType = Label(self.wfmFrame, text='Filter Type')
            filtTypeList = ['Root Raised Cosine', 'Raised Cosine']
            self.cbFiltType = ttk.Combobox(self.wfmFrame, state='readonly', values=filtTypeList)
            self.cbFiltType.current(0)

            lblFiltAlpha = Label(self.wfmFrame, text='Filter Alpha')
            filtAlphaVar = StringVar()
            self.eFiltAlpha = Entry(self.wfmFrame, textvariable=filtAlphaVar)
            filtAlphaVar.set('0.35')

            r = 0
            lblFs.grid(row=r, column=0, sticky=E)
            self.eFs.grid(row=r, column=1, sticky=W)

            r += 1
            lblModType.grid(row=r, column=0, sticky=E)
            self.cbModType.grid(row=r, column=1, sticky=W)

            r += 1
            lblSymrate.grid(row=r, column=0, sticky=E)
            self.eSymrate.grid(row=r, column=1, sticky=W)

            r += 1
            lblPrbsOrder.grid(row=r, column=0, sticky=E)
            self.cbPrbsOrder.grid(row=r, column=1, sticky=W)

            r += 1
            lblFiltType.grid(row=r, column=0, sticky=E)
            self.cbFiltType.grid(row=r, column=1, sticky=W)

            r += 1
            lblFiltAlpha.grid(row=r, column=0, sticky=E)
            self.eFiltAlpha.grid(row=r, column=1, sticky=W)

        elif self.wfmType == 'Multitone':
            lblFs = Label(self.wfmFrame, text='Sample Rate')
            fsVar = StringVar()
            self.eFs = Entry(self.wfmFrame, textvariable=fsVar)
            try:
                fsVar.set(str(self.inst.fs))
            except AttributeError as e:
                fsVar.set('100e6')

            lblSpacing = Label(self.wfmFrame, text='Tone Spacing')
            spacingVar = StringVar()
            self.eSpacing = Entry(self.wfmFrame, textvariable=spacingVar)
            spacingVar.set('1e6')

            lblNumTones = Label(self.wfmFrame, text='Num Tones')
            numTonesVar = StringVar()
            self.eNumTones = Entry(self.wfmFrame, textvariable=numTonesVar)
            numTonesVar.set('11')

            lblPhase = Label(self.wfmFrame, text='Phase Relationship')
            phaseList = ['random', 'zero', 'increasing', 'parabolic']
            self.cbPhase = ttk.Combobox(self.wfmFrame, state='readonly', values=phaseList)
            self.cbPhase.current(0)

            r = 0
            lblFs.grid(row=r, column=0, sticky=E)
            self.eFs.grid(row=r, column=1, sticky=W)

            r += 1
            lblSpacing.grid(row=r, column=0, sticky=E)
            self.eSpacing.grid(row=r, column=1, sticky=W)

            r += 1
            lblNumTones.grid(row=r, column=0, sticky=E)
            self.eNumTones.grid(row=r, column=1, sticky=W)

            r += 1
            lblPhase.grid(row=r, column=0, sticky=E)
            self.cbPhase.grid(row=r, column=1, sticky=W)

        else:
            raise ValueError('Invalid wfmType selected, this should never happen.')

        self.btnCreateWfm = Button(self.wfmFrame, text='Create Waveform', command=self.create_wfm)

        r += 1
        self.btnCreateWfm.grid(row=r, columnspan=2)

    def create_wfm(self):
        """Calls the function to create the selected type of waveform
        and stores it in the waveform list."""

        if self.wfmType == 'AM':
            wfmArgs = [float(self.eFs.get()), int(self.eAmDepth.get()), float(self.eModRate.get())]
            i, q = pyarbtools.wfmBuilder.am_generator(*wfmArgs)
        elif self.wfmType == 'Chirp':
            wfmArgs = [float(self.eFs.get()), float(self.ePulseWidth.get()),
                       float(self.ePri.get()), float(self.eChirpBw.get())]
            if self.genMode == 'IQ':
                i, q = pyarbtools.wfmBuilder.chirp_generator(*wfmArgs)
            else:
                wfmArgs.append(float(self.eCf.get()))
                real = pyarbtools.wfmBuilder.chirp_generator_real(*wfmArgs)
        elif self.wfmType == 'Barker Code':
            wfmArgs = [float(self.eFs.get()), float(self.ePulseWidth.get()),
                       float(self.ePri.get()), self.cbCode.get()]
            if self.genMode == 'IQ':
                i, q = pyarbtools.wfmBuilder.barker_generator(*wfmArgs)
            else:
                wfmArgs.append(float(self.eCf.get()))
                real = pyarbtools.wfmBuilder.barker_generator_real(*wfmArgs)
        elif self.wfmType == 'Digital Modulation':
            filtArg = self.cbFiltType.get()
            if  filtArg == 'Root Raised Cosine':
                filtType = pyarbtools.wfmBuilder.rrc_filter
            elif filtArg == 'Raised Cosine':
                filtType = pyarbtools.wfmBuilder.rc_filter
            else:
                raise ValueError('Invalid filter type chosen, this should never happen.')
            wfmArgs = [float(self.eFs.get()), self.cbModType.get(),
                       float(self.eSymrate.get()), int(self.cbPrbsOrder.get()),
                       filtType, float(self.eFiltAlpha.get())]
            i, q = pyarbtools.wfmBuilder.digmod_prbs_generator(*wfmArgs)
        elif self.wfmType == 'Multitone':
            wfmArgs = [float(self.eFs.get()), float(self.eSpacing.get()),
                       int(self.eNumTones.get()), self.cbPhase.get()]
            i, q = pyarbtools.wfmBuilder.multitone(*wfmArgs)
        else:
            raise ValueError('Invalid selection chosen, this should never happen.')


    def inst_write(self):
        self.inst.write(self.eScpi.get())
        self.lblReadout.configure(text=f'"{self.eScpi.get()}" command sent')

    def inst_query(self):
        response = self.inst.query(self.eScpi.get())
        self.lblReadout.configure(text=response)

    def inst_err_check(self):
        try:
            self.inst.err_check()
            self.lblReadout.configure(text='No error')
        except Exception as e:
            self.lblReadout.configure(text=str(e))

    def inst_preset(self):
        self.inst.write('*rst')
        self.inst.query('*opc?')
        self.lblReadout.configure(text='Instrument preset complete')

    def instrument_connect(self):
        """Selects the appropriate instrument class based on combobox selection."""
        self.ipAddress = self.eInstIPAddress.get()
        try:
            ipaddress.ip_address(self.ipAddress)
        except ValueError:
            self.statusBar.configure(text='Invalid IP Address.')

        self.instKey = self.cbInstruments.get()
        try:
            # Connect to instrument
            # self.inst = self.instClasses[self.instKey](self.ipAddress)

            self.lblInstStatus.configure(text='Connected', bg='green')
            # self.statusBar.configure(text=f'Connected to {self.inst.instId}')
            self.open_inst_config()
            self.btnWrite.configure(state=ACTIVE)
            self.btnQuery.configure(state=ACTIVE)
            self.btnErrCheck.configure(state=ACTIVE)
            self.btnPreset.configure(state=ACTIVE)
            self.lblReadout.configure(text='Ready for SCPI interaction')
            self.btnInstConnect.configure(text='Disconnect', command=self.instrument_disconnect)
        except Exception as e:
            self.lblInstStatus.configure(text='Not Connected', bg='red')
            self.statusBar.configure(text=str(e))

    def instrument_disconnect(self):
        """Disconnects from connected instrument and adjusts GUI accordingly."""
        self.inst.disconnect()
        self.statusBar.configure(text='Welcome')
        self.btnWrite.configure(state=DISABLED)
        self.btnQuery.configure(state=DISABLED)
        self.btnErrCheck.configure(state=DISABLED)
        self.btnPreset.configure(state=DISABLED)
        self.lblReadout.configure(text='Connect to instrument')
        self.lblInstStatus.configure(text='Not Connected', bg='red')
        self.btnInstConnect.configure(text='Connect', command=self.instrument_connect)

        # Reset instrument config frame
        self.configFrame.destroy()
        self.configFrame = Frame(self.master, bd=5)
        self.configFrame.grid(row=1, column=0)

    def instrument_configure(self):
        """Pulls settings from config frame and calls instrument-specific measurement functions"""
        try:
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
                configArgs= {'dacMode': self.dacModeArgs[self.cbDacMode.get()],
                             'fs': float(self.eFs.get()),
                             'refSrc': self.refSrcArgs[self.cbRefSrc.get()],
                             'refFreq': float(self.eRefFreq.get()),
                             'func': self.funcArgs[self.cbFunc.get()]}
            elif self.instKey == 'M8196A':
                configArgs = {'dacMode': self.dacModeArgs[self.cbDacMode.get()],
                              'fs': float(self.eFs.get()),
                              'refSrc': self.refSrcArgs[self.cbRefSrc.get()],
                              'refFreq': float(self.eRefFreq.get())}
            elif self.instKey == 'VSG':
                configArgs = {'rfState': self.rfStateArgs[self.cbRfState.get()],
                              'modState': self.modStateArgs[self.cbModState.get()],
                              'cf': float(self.eCf.get()),
                              'amp': int(self.eAmp.get()),
                              'alcState': self.alcStateArgs[self.cbAlcState.get()],
                              'iqScale': int(self.eIqScale.get()),
                              'refSrc': self.refSrcArgs[self.cbRefSrc.get()],
                              'fs': float(self.eFs.get())}
            elif self.instKey == 'AnalogUXG':
                configArgs = {'rfState': self.rfStateArgs[self.cbRfState.get()],
                              'modState': self.modStateArgs[self.cbModState.get()],
                              'cf': float(self.eCf.get()),
                              'amp': int(self.eAmp.get()),
                              'mode': self.modeArgs[self.cbMode.get()]}
            elif self.instKey == 'VectorUXG':
                configArgs = {'rfState': self.rfStateArgs[self.cbRfState.get()],
                              'modState': self.modStateArgs[self.cbModState.get()],
                              'cf': float(self.eCf.get()),
                              'amp': int(self.eAmp.get()),
                              'iqScale': int(self.eIqScale.get())}
            else:
                raise ValueError('Invalid instrument selected. This should never happen.')
            self.inst.configure(*configArgs.values())
            self.statusBar.configure(text=f'{self.instKey} configured.')
        except Exception as e:
            self.statusBar.configure(text=str(e))


    def open_inst_config(self):
        """Creates a new frame with instrument-specific configuration fields."""
        self.configFrame.destroy()
        self.configFrame = Frame(self.master, bd=5)
        self.configFrame.grid(row=1, column=0)

        configBtn = Button(self.configFrame, text='Configure', command=self.instrument_configure)

        if self.instKey == 'M8190A':
            resLabel = Label(self.configFrame, text='Resolution')
            self.resArgs = {'12 Bit': 'wsp', '14 Bit': 'wpr', '3x Interpolation': 'intx3', '12x Interpolation': 'intx12',
                            '24x Interpolation': 'intx24', '48x Interpolation': 'intx48'}
            self.cbRes = ttk.Combobox(self.configFrame, state='readonly', values=list(self.resArgs.keys()))
            self.cbRes.current(0)

            clkSrcLabel = Label(self.configFrame, text='Clock Source')
            self.clkSrcArgs = {'Internal': 'int', 'External': 'ext'}
            self.cbClkSrc = ttk.Combobox(self.configFrame, state='readonly', values=list(self.clkSrcArgs.keys()))
            self.cbClkSrc.current(0)

            fsLabel = Label(self.configFrame, text='Sample Rate')
            fsVar = StringVar()
            self.eFs = Entry(self.configFrame, textvariable=fsVar)
            fsVar.set('12e9')

            refSrcLabel = Label(self.configFrame, text='Reference Source')
            self.refSrcArgs = {'AXIe': 'axi', 'Internal': 'int', 'External': 'ext'}
            self.cbRefSrc = ttk.Combobox(self.configFrame, state='readonly', values=list(self.refSrcArgs.keys()))
            self.cbRefSrc.current(0)

            refFreqLabel = Label(self.configFrame, text='Reference Frequency')
            refFreqVar = StringVar()
            self.eRefFreq = Entry(self.configFrame, textvariable=refFreqVar)
            refFreqVar.set('100e6')

            out1Label = Label(self.configFrame, text='Ch 1 Output Path')
            self.outArgs = {'Direct DAC': 'dac', 'AC Amplified': 'ac', 'DC Amplified': 'dc'}
            self.cbOut1 = ttk.Combobox(self.configFrame, state='readonly', values=list(self.outArgs.keys()))
            self.cbOut1.current(0)

            out2Label = Label(self.configFrame, text='Ch 2 Output Path')
            self.cbOut2 = ttk.Combobox(self.configFrame, state='readonly', values=list(self.outArgs.keys()))
            self.cbOut2.current(0)

            func1Label = Label(self.configFrame, text='Ch 1 Function')
            self.funcArgs = {'Arbitrary Waveform': 'arb', 'Sequence': 'sts', 'Scenario': 'stc'}
            self.cbFunc1 = ttk.Combobox(self.configFrame, state='readonly', values=list(self.funcArgs.keys()))
            self.cbFunc1.current(0)

            func2Label = Label(self.configFrame, text='Ch 2 Function')
            self.cbFunc2 = ttk.Combobox(self.configFrame, state='readonly', values=list(self.funcArgs.keys()))
            self.cbFunc2.current(0)

            cf1Label = Label(self.configFrame, text='Ch 1 Carrier Frequency')
            cf1Var = StringVar()
            self.eCf1 = Entry(self.configFrame, textvariable=cf1Var)
            cf1Var.set('1e9')

            cf2Label = Label(self.configFrame, text='Ch 2 Carrier Frequency')
            cf2Var = StringVar()
            self.eCf2 = Entry(self.configFrame, textvariable=cf2Var)
            cf2Var.set('1e9')

            # Layout
            r = 0
            resLabel.grid(row=r, column=0, sticky=E)
            self.cbRes.grid(row=r, column=1, sticky=W)
            r += 1

            clkSrcLabel.grid(row=r, column=0, sticky=E)
            self.cbClkSrc.grid(row=r, column=1, sticky=W)
            r += 1

            fsLabel.grid(row=r, column=0, sticky=E)
            self.eFs.grid(row=r, column=1, sticky=W)
            r += 1

            refSrcLabel.grid(row=r, column=0, sticky=E)
            self.cbRefSrc.grid(row=r, column=1, sticky=W)
            r += 1

            refFreqLabel.grid(row=r, column=0, sticky=E)
            self.eRefFreq.grid(row=r, column=1, sticky=W)
            r += 1

            out1Label.grid(row=r, column=0, sticky=E)
            self.cbOut1.grid(row=r, column=1, sticky=W)
            r += 1

            out2Label.grid(row=r, column=0, sticky=E)
            self.cbOut2.grid(row=r, column=1, sticky=W)
            r += 1

            func1Label.grid(row=r, column=0, sticky=E)
            self.cbFunc1.grid(row=r, column=1, sticky=W)
            r += 1

            func2Label.grid(row=r, column=0, sticky=E)
            self.cbFunc2.grid(row=r, column=1, sticky=W)
            r += 1

            cf1Label.grid(row=r, column=0, sticky=E)
            self.eCf1.grid(row=r, column=1, sticky=W)
            r += 1

            cf2Label.grid(row=r, column=0, sticky=E)
            self.eCf2.grid(row=r, column=1, sticky=W)
            r += 1

        elif self.instKey == 'M8195A':
            dacModeLabel = Label(self.configFrame, text='DAC Mode')
            self.dacModeArgs = {'Single (Ch 1)': 'single', 'Dual (Ch 1 & 4)': 'dual',
                                'Four (All Ch)': 'four', 'Marker (Sig Ch 1, Mkr Ch 3 & 4)': 'marker',
                                'Dual Channel Duplicate (Ch 3 & 4 copy Ch 1 & 2)': 'dcd',
                                'Dual Channel Marker (Sign Ch 1 & 2, Ch 1 mkr on Ch 3 & 4)': 'dcm'}
            self.cbDacMode = ttk.Combobox(self.configFrame, state='readonly',
                                          values=list(self.dacModeArgs.keys()))
            self.cbDacMode.current(0)

            fsLabel = Label(self.configFrame, text='Sample Rate')
            fsVar = StringVar()
            self.eFs = Entry(self.configFrame, textvariable=fsVar)
            fsVar.set('64e9')

            refSrcLabel = Label(self.configFrame, text='Reference Source')

            self.refSrcArgs = {'AXIe': 'axi', 'Internal': 'int', 'External': 'ext'}
            self.cbRefSrc = ttk.Combobox(self.configFrame, state='readonly',
                                         values=list(self.refSrcArgs.keys()))
            self.cbRefSrc.current(0)

            refFreqLabel = Label(self.configFrame, text='Reference Frequency')
            refFreqVar = StringVar()
            self.eRefFreq = Entry(self.configFrame, textvariable=refFreqVar)
            refFreqVar.set('100e6')

            funcLabel = Label(self.configFrame, text='Function')
            self.funcArgs = {'Arbitrary Waveform': 'arb', 'Sequence': 'sts', 'Scenario': 'stc'}
            self.cbFunc = ttk.Combobox(self.configFrame, state='readonly', values=list(self.funcArgs.keys()))
            self.cbFunc.current(0)

            # Layout
            r = 0
            dacModeLabel.grid(row=r, column=0, sticky=E)
            self.cbDacMode.grid(row=r, column=1, sticky=W)
            r += 1

            fsLabel.grid(row=r, column=0, sticky=E)
            self.eFs.grid(row=r, column=1, sticky=W)
            r += 1

            refSrcLabel.grid(row=r, column=0, sticky=E)
            self.cbRefSrc.grid(row=r, column=1, sticky=W)
            r += 1

            refFreqLabel.grid(row=r, column=0, sticky=E)
            self.eRefFreq.grid(row=r, column=1, sticky=W)
            r += 1

            funcLabel.grid(row=r, column=0, sticky=E)
            self.cbFunc.grid(row=r, column=1, sticky=W)
            r += 1

        elif self.instKey == 'M8196A':
            dacModeLabel = Label(self.configFrame, text='DAC Mode')
            self.dacModeArgs = {'Single (Ch 1)': 'single', 'Dual (Ch 1 & 4)': 'dual',
                                'Four (All Ch)': 'four', 'Marker (Sig Ch 1, Mkr Ch 2 & 3)': 'marker',
                                'Dual Channel Marker (Sign Ch 1 & 4, Ch 1 mkr on Ch 2 & 3)': 'dcm'}
            self.cbDacMode = ttk.Combobox(self.configFrame, state='readonly',
                                          values=list(self.dacModeArgs.keys()))
            self.cbDacMode.current(0)

            fsLabel = Label(self.configFrame, text='Sample Rate')
            fsVar = StringVar()
            self.eFs = Entry(self.configFrame, textvariable=fsVar)
            fsVar.set('92e9')

            refSrcLabel = Label(self.configFrame, text='Reference Source')

            self.refSrcArgs = {'AXIe': 'axi', 'Internal': 'int', 'External': 'ext'}
            self.cbRefSrc = ttk.Combobox(self.configFrame, state='readonly',
                                         values=list(self.refSrcArgs.keys()))
            self.cbRefSrc.current(0)

            refFreqLabel = Label(self.configFrame, text='Reference Frequency')
            refFreqVar = StringVar()
            self.eRefFreq = Entry(self.configFrame, textvariable=refFreqVar)
            refFreqVar.set('100e6')

            # Layout
            r = 0
            dacModeLabel.grid(row=r, column=0, sticky=E)
            self.cbDacMode.grid(row=r, column=1, sticky=W)
            r += 1

            fsLabel.grid(row=r, column=0, sticky=E)
            self.eFs.grid(row=r, column=1, sticky=W)
            r += 1

            refSrcLabel.grid(row=r, column=0, sticky=E)
            self.cbRefSrc.grid(row=r, column=1, sticky=W)
            r += 1

            refFreqLabel.grid(row=r, column=0, sticky=E)
            self.eRefFreq.grid(row=r, column=1, sticky=W)
            r += 1

        elif self.instKey == 'VSG':
            rfStateLabel = Label(self.configFrame, text='RF State')
            self.rfStateArgs = {'On': 1, 'Off': 0}
            self.cbRfState = ttk.Combobox(self.configFrame, state='readonly', values=list(self.rfStateArgs.keys()))
            self.cbRfState.current(0)

            modStateLabel = Label(self.configFrame, text='Modulation State')
            self.modStateArgs = {'On': 1, 'Off': 0}
            self.cbModState = ttk.Combobox(self.configFrame, state='readonly', values=list(self.modStateArgs.keys()))
            self.cbModState.current(0)

            cfLabel = Label(self.configFrame, text='Carrier Frequency')
            cfVar = StringVar()
            self.eCf = Entry(self.configFrame, textvariable=cfVar)
            cfVar.set('1e9')

            ampLabel = Label(self.configFrame, text='Amplitude (dBm)')
            ampVar = StringVar()
            self.eAmp = Entry(self.configFrame, textvariable=ampVar)
            ampVar.set(-130)

            alcStateLabel = Label(self.configFrame, text='ALC State')
            self.alcStateArgs = {'On': 1, 'Off': 0}
            self.cbAlcState = ttk.Combobox(self.configFrame, state='readonly', values=list(self.alcStateArgs.keys()))
            self.cbAlcState.current(0)

            iqScaleLabel = Label(self.configFrame, text='IQ Scale (%)')
            iqScaleVar = StringVar()
            self.eIqScale = Entry(self.configFrame, textvariable=iqScaleVar)
            iqScaleVar.set(70)

            refSrcLabel = Label(self.configFrame, text='Reference Source')
            self.refSrcArgs = {'Internal': 'int', 'External': 'ext'}
            self.cbRefSrc = ttk.Combobox(self.configFrame, state='readonly', values=list(self.refSrcArgs.keys()))
            self.cbRefSrc.current(0)

            fsLabel = Label(self.configFrame, text='Sample Rate')
            fsVar = StringVar()
            self.eFs = Entry(self.configFrame, textvariable=fsVar)
            fsVar.set('200e6')

            # Layout
            r = 0
            rfStateLabel.grid(row=r, column=0, sticky=E)
            self.cbRfState.grid(row=r, column=1, sticky=W)
            r += 1

            modStateLabel.grid(row=r, column=0, sticky=E)
            self.cbModState.grid(row=r, column=1, sticky=W)
            r += 1

            cfLabel.grid(row=r, column=0, sticky=E)
            self.eCf.grid(row=r, column=1, sticky=W)
            r += 1

            ampLabel.grid(row=r, column=0, sticky=E)
            self.eAmp.grid(row=r, column=1, sticky=W)
            r += 1

            alcStateLabel.grid(row=r, column=0, sticky=E)
            self.cbAlcState.grid(row=r, column=1, sticky=W)
            r += 1

            iqScaleLabel.grid(row=r, column=0, sticky=E)
            self.eIqScale.grid(row=r, column=1, sticky=W)
            r += 1

            refSrcLabel.grid(row=r, column=0, sticky=E)
            self.cbRefSrc.grid(row=r, column=1, sticky=W)
            r += 1

            fsLabel.grid(row=r, column=0, sticky=E)
            self.eFs.grid(row=r, column=1, sticky=W)
            r += 1

        elif self.instKey == 'VectorUXG':
            rfStateLabel = Label(self.configFrame, text='RF State')
            self.rfStateArgs = {'On': 1, 'Off': 0}
            self.cbRfState = ttk.Combobox(self.configFrame, state='readonly', values=list(self.rfStateArgs.keys()))
            self.cbRfState.current(0)

            modStateLabel = Label(self.configFrame, text='Modulation State')
            self.modStateArgs = {'On': 1, 'Off': 0}
            self.cbModState = ttk.Combobox(self.configFrame, state='readonly', values=list(self.modStateArgs.keys()))
            self.cbModState.current(0)

            cfLabel = Label(self.configFrame, text='Carrier Frequency')
            cfVar = StringVar()
            self.eCf = Entry(self.configFrame, textvariable=cfVar)
            cfVar.set('1e9')

            ampLabel = Label(self.configFrame, text='Amplitude (dBm)')
            ampVar = StringVar()
            self.eAmp = Entry(self.configFrame, textvariable=ampVar)
            ampVar.set(-130)

            iqScaleLabel = Label(self.configFrame, text='IQ Scale (%)')
            iqScaleVar = StringVar()
            self.eIqScale = Entry(self.configFrame, textvariable=iqScaleVar)
            iqScaleVar.set(70)

            # Layout
            r = 0
            rfStateLabel.grid(row=r, column=0, sticky=E)
            self.cbRfState.grid(row=r, column=1, sticky=W)
            r += 1

            modStateLabel.grid(row=r, column=0, sticky=E)
            self.cbModState.grid(row=r, column=1, sticky=W)
            r += 1

            cfLabel.grid(row=r, column=0, sticky=E)
            self.eCf.grid(row=r, column=1, sticky=W)
            r += 1

            ampLabel.grid(row=r, column=0, sticky=E)
            self.eAmp.grid(row=r, column=1, sticky=W)
            r += 1

            iqScaleLabel.grid(row=r, column=0, sticky=E)
            self.eIqScale.grid(row=r, column=1, sticky=W)
            r += 1

        elif self.instKey == 'AnalogUXG':
            rfStateLabel = Label(self.configFrame, text='RF State')
            self.rfStateArgs = {'On': 1, 'Off': 0}
            self.cbRfState = ttk.Combobox(self.configFrame, state='readonly', values=list(self.rfStateArgs.keys()))
            self.cbRfState.current(0)

            modStateLabel = Label(self.configFrame, text='Modulation State')
            self.modStateArgs = {'On': 1, 'Off': 0}
            self.cbModState = ttk.Combobox(self.configFrame, state='readonly', values=list(self.modStateArgs.keys()))
            self.cbModState.current(0)

            cfLabel = Label(self.configFrame, text='Carrier Frequency')
            cfVar = StringVar()
            self.eCf = Entry(self.configFrame, textvariable=cfVar)
            cfVar.set('1e9')

            ampLabel = Label(self.configFrame, text='Amplitude (dBm)')
            ampVar = StringVar()
            self.eAmp = Entry(self.configFrame, textvariable=ampVar)
            ampVar.set(-130)

            modeLabel = Label(self.configFrame, text='Instrument Mode')
            self.modeArgs = {'Streaming': 'streaming', 'Normal': 'normal', 'List': 'list',
                             'Fast CW Switching': 'fcwswitching'}
            self.cbMode = ttk.Combobox(self.configFrame, state='readonly', values=list(self.modeArgs.keys()))
            self.cbMode.current(0)

            # Layout
            r = 0
            rfStateLabel.grid(row=r, column=0, sticky=E)
            self.cbRfState.grid(row=r, column=1, sticky=W)
            r += 1

            modStateLabel.grid(row=r, column=0, sticky=E)
            self.cbModState.grid(row=r, column=1, sticky=W)
            r += 1

            cfLabel.grid(row=r, column=0, sticky=E)
            self.eCf.grid(row=r, column=1, sticky=W)
            r += 1

            ampLabel.grid(row=r, column=0, sticky=E)
            self.eAmp.grid(row=r, column=1, sticky=W)
            r += 1

            modeLabel.grid(row=r, column=0, sticky=E)
            self.cbMode.grid(row=r, column=1, sticky=W)
            r += 1

        else:
            raise ValueError('You got an argument that was not in the instrument select combobox. This should never happen.')

        configBtn.grid(row=r, column=0, columnspan=2)

def main():
    root = Tk()
    root.title('pyarbtools')
    # root.geometry('1000x200')

    PyarbtoolsGUI(root)

    root.mainloop()


if __name__ == '__main__':
    main()
