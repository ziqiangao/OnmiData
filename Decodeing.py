import numpy as np
import soundfile as sf
import sounddevice as sd
import time
from scipy.fft import fft, fftfreq
from scipy.signal import find_peaks

class FileStreamOmniDecoder:
    def __init__(self, filepath, chunk_size=2048):
        self.filepath = filepath
        self.chunk_size = chunk_size
        self.reader_enabled = False
        self.reading = False
        self.click_buffer = []
        self.data_buffer = []
        self.locked = False
        self.state = "IDLE"
        self.initial_pattern = "100001100001101010101010100"

    def load_audio(self):
        signal, sr = sf.read(self.filepath)
        if signal.ndim > 1:
            signal = np.mean(signal, axis=1)
        self.signal = signal.astype(np.float32)
        self.sample_rate = sr
        self.total_samples = len(self.signal)
        print(f"[INFO] Loaded '{self.filepath}' ({self.total_samples} samples at {sr} Hz)")

    def run_live_decode(self):
        self.load_audio()
        index = 0

        def callback(outdata, frames, time_info, status):
            nonlocal index
            if status:
                print("[Audio Stream Status]", status)

            if index + self.chunk_size > self.total_samples:
                outdata[:] = np.zeros((frames, 1), dtype=np.float32)
                raise sd.CallbackStop()

            chunk = self.signal[index:index + self.chunk_size]
            chunk = chunk[:frames]

            # Playback
            outdata[:len(chunk), 0] = chunk

            # Process the chunk
            self.process_chunk(chunk)

            index += self.chunk_size

        try:
            with sd.OutputStream(channels=1, samplerate=self.sample_rate,
                                 blocksize=self.chunk_size, callback=callback):
                print("[INFO] Playing and decoding in real time. Press Ctrl+C to stop.")
                while True:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[INFO] Stopped by user.")
        except sd.CallbackStop:
            print("\n[INFO] Playback finished.")

    def process_chunk(self, chunk):
        self.detect_clicks(chunk)
        if self.reading:
            self.decode_fsk(chunk)

    def detect_clicks(self, signal, threshold=0.6, min_gap_samples=10000):
        # Absolute peaks only
        peaks, _ = find_peaks(np.abs(signal), height=threshold, distance=min_gap_samples)

        for peak in peaks:
            val = signal[peak]
            if val > 0:
                click_type = 'pullup'
            else:
                click_type = 'pulldown'
            self.click_buffer.append(click_type)
            self.handle_click_sequence()


    def handle_click_sequence(self):
        buf = self.click_buffer[-2:]

        if buf == ['pulldown', 'pulldown']:
            self.reader_enabled = True
            self.state = "READER_ENABLED"
            print("[STATE] Reader Enabled.")
        elif buf[-1:] == ['pullup'] and self.reader_enabled:
            self.reading = True
            self.state = "READING"
            print("[STATE] Started Reading.")
        elif buf[-1:] == ['pulldown'] and self.reading:
            self.reading = False
            self.state = "PROCESSING"
            print("[STATE] Stopped Reading. Processing...")
            self.process_data()
        elif buf == ['pullup', 'pullup']:
            self.reader_enabled = False
            self.data_buffer.clear()
            self.state = "IDLE"
            print("[STATE] Reader Disabled. Buffers Cleared.")

    def decode_fsk(self, signal):
        freq = self.get_dominant_freq(signal)
        bit = self.map_freq_to_bit(freq)

        if freq:
            print(f"[FSK] Freq: {freq:.1f} Hz → Bit: {bit}")

        if bit in ['0', '1']:
            self.data_buffer.append(bit)
            if not self.locked and ''.join(self.data_buffer).endswith(self.initial_pattern):
                print("[SYNC] Initial pattern found.")
                self.locked = True
                self.data_buffer = []
        elif self.locked:
            self.data_buffer.append(bit)


    def get_dominant_freq(self, chunk):
        windowed = chunk * np.hamming(len(chunk))
        fft_vals = np.abs(fft(windowed))
        freqs = fftfreq(len(fft_vals), 1 / self.sample_rate)
        positive_freqs = freqs[:len(freqs)//2]
        positive_fft = fft_vals[:len(fft_vals)//2]

        if np.max(positive_fft) < 1e-4:
            return None
        peak_index = np.argmax(positive_fft)
        return positive_freqs[peak_index]

    def map_freq_to_bit(self, freq):
        if freq is None:
            return '?'
        if 800 <= freq <= 1200:
            return '0'
        elif 2600 <= freq <= 2900:  # Adjusted for your real signal
            return '1'
        else:
            return '?'


    def process_data(self):
        bitstream = ''.join(self.data_buffer)
        if bitstream:
            print(f"[RESULT] Bitstream:\n{bitstream[:128]}...")
        else:
            print("[RESULT] No data.")
        self.data_buffer.clear()
        self.locked = False


# === Run the decoder ===
decoder = FileStreamOmniDecoder("Games Hosted by Big Bird and Other Sesame Street Friends.wav")
decoder.run_live_decode()
