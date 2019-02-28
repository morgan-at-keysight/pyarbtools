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
        self.master = master
        setupFrame = Frame(self.master)
        setupFrame.grid(row=0, column=0)
        self.configFrame = Frame(self.master)
        self.configFrame.grid(row=1, column=0)
        sbFrame = Frame(self.master)
        sbFrame.grid(row=2, column=0)
        self.statusBar = Label(sbFrame, text='Welcome', width=100, relief=SUNKEN)
        self.statusBar.grid(row=0, sticky=W+E+N+S)

        # Constants
        self.instClasses = {'M8190A': pyarbtools.instruments.M8190A,
                       'M8195A': pyarbtools.instruments.M8195A,
                       'M8196A': pyarbtools.instruments.M8196A,
                       'VSG': pyarbtools.instruments.VSG,
                       'AnalogUXG': pyarbtools.instruments.AnalogUXG,
                       'VectorUXG': pyarbtools.instruments.VectorUXG}

        # self.instFrames = {'M8190A': self.func,
        #                'M8195A': self.func,
        #                'M8196A': self.func,
        #                'VSG': self.func,
        #                'AnalogUXG': self.func,
        #                'VectorUXG': self.func}

        # Variables
        # self.ipAddress = '127.0.0.1'
        self.ipAddress = '141.121.210.122'
        self.inst = None

        # Widgets
        self.lblInstruments = Label(setupFrame, text='Instrument Class')
        self.cbInstruments = ttk.Combobox(setupFrame, state='readonly', values=list(self.instClasses.keys()))
        self.cbInstruments.current(3)

        v = StringVar()

        self.lblInstIPAddress = Label(setupFrame, text='Instrument IP Address')
        self.eInstIPAddress = Entry(setupFrame, textvariable=v)
        v.set(self.ipAddress)

        self.lblInstStatus = Label(setupFrame, text='Not Connected', bg='red')
        self.btnInstConnect = Button(setupFrame, text='Connect', command=self.instrument_connect)

        # Geometry
        r = 0
        self.lblInstruments.grid(row=r, column=0)
        self.lblInstIPAddress.grid(row=r, column=1)
        self.lblInstStatus.grid(row=r, column=2)

        r += 1
        self.cbInstruments.grid(row=r, column=0)
        self.eInstIPAddress.grid(row=r, column=1)
        self.btnInstConnect.grid(row=r, column=2)



    def instrument_connect(self):
        """Selects the appropriate instrument class based on combobox selection."""
        self.ipAddress = self.eInstIPAddress.get()
        try:
            ipaddress.ip_address(self.ipAddress)
        except ValueError:
            self.statusBar.configure(text='Invalid IP Address.')

        self.instKey = self.cbInstruments.get()
        try:
            # self.inst = self.instClasses[self.instKey](self.ipAddress)
            self.lblInstStatus.configure(text='Connected', bg='green')
            # self.statusBar.configure(text=f'Connected to {self.inst.instId}')
            self.open_inst_config()
        except Exception as e:
            self.lblInstStatus.configure(text='Not Connected', bg='red')
            self.statusBar.configure(text=str(e))


    def instrument_configure(self):
        """pulls settings from config frame and calls instrument-specific measurement functions"""
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
                          'amp': float(self.eAmp.get()),
                          'alcState': self.alcStateArgs[self.cbAlcState.get()],
                          'iqScale': int(self.eIqScale.get()),
                          'refSrc': self.refSrcArgs[self.cbRefSrc.get()],
                          'fs': float(self.eFs.get())}
        elif self.instKey == 'AnalogUXG':
            configArgs = {'rfState': self.rfStateArgs[self.cbRfState.get()],
                          'modState': self.modStateArgs[self.cbModState.get()],
                          'cf': float(self.eCf.get()),
                          'amp': float(self.eAmp.get()),
                          'alcState': self.alcStateArgs[self.cbAlcState.get()],
                          'iqScale': int(self.eIqScale.get()),
                          'refSrc': self.refSrcArgs[self.cbRefSrc.get()],
                          'fs': float(self.eFs.get())}
        elif self.instKey == 'VectorUXG':
            configArgs = {}
        try:
            # self.inst.configure(*configArgs.values())
            self.statusBar.configure(text=f'{self.instKey} configured.')
        except Exception as e:
            print(str(e))
            self.statusBar.configure(text=str(e))


    def open_inst_config(self):
        """Creates a new frame with instrument-specific configuration fields."""
        self.configFrame.destroy()
        self.configFrame = Frame(self.master)
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
                                  'Fast CW Switching': 'fcwswitching', 'LO for Vector UXG': 'vlo'}
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
