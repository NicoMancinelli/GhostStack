from gnuradio import gr
from gnuradio import blocks
from gnuradio import fft
from gnuradio import soapy
import sys
import signal

# GhostStack: RF/EW Layer - GNU Radio Wideband Scanner
# 
# A programmatic implementation of a wideband spectrum scanner.
# It uses a Soapy source to ingest IQ data and an FFT block to
# calculate power spectral density for signal identification.

class WidebandScanner(gr.top_block):
    def __init__(self, sample_rate=20e6, center_freq=2.44e9, gain=40):
        gr.top_block.__init__(self, "GhostStack Wideband Scanner")

        # 1. Soapy Source (Hardware Abstraction)
        self.source = soapy.source("driver=hackrf", "complex64", 1, '', '', [])
        self.source.set_sample_rate(0, sample_rate)
        self.source.set_frequency(0, center_freq)
        self.source.set_gain(0, gain)

        # 2. FFT Block (Spectrum Conversion)
        self.fft_size = 1024
        self.fft_block = fft.fft_vcc(self.fft_size, True, [], True, 1)

        # 3. Vector to Stream / Complex to Mag^2
        self.v2s = blocks.vector_to_stream(gr.sizeof_gr_complex, self.fft_size)
        self.c2mag = blocks.complex_to_mag_squared(1)
        
        # 4. Log Power
        self.n2l = blocks.nlog10_ff(10.0, 1, 0)

        # 5. Sink (Message port for detection logic or Null Sink for now)
        self.sink = blocks.null_sink(gr.sizeof_float)

        # Connections
        self.connect((self.source, 0), (self.fft_block, 0))
        self.connect((self.fft_block, 0), (self.v2s, 0))
        self.connect((self.v2s, 0), (self.c2mag, 0))
        self.connect((self.c2mag, 0), (self.n2l, 0))
        self.connect((self.n2l, 0), (self.sink, 0))

def main():
    tb = WidebandScanner()

    def signal_handler(sig, frame):
        tb.stop()
        tb.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    print("[*] GhostStack: GNU Radio Wideband Scanner Running...")
    tb.start()
    tb.wait()

if __name__ == "__main__":
    main()
