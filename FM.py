import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as signal
import matplotlib.pyplot as plt

# === PARAMETERS ===
LOW_CUT = 900       # Bandpass start frequency (Hz)
HIGH_CUT = 3000     # Bandpass end frequency (Hz)
DECIMATION = 1      # Downsample factor
NORMALISE_OUTPUT = True
INPUT_FILE = 'dd.wav'
OUTPUT_FILE = 'demodulated_output.wav'

def trim_silence(audio, threshold=0.01, frame_size=1024, hop_size=512):
    """Trim silence from filtered audio and return trimmed signal and indices."""
    audio = np.array(audio)
    energy = np.array([
        np.sqrt(np.mean(audio[i:i + frame_size] ** 2))
        for i in range(0, len(audio) - frame_size, hop_size)
    ])

    mask = energy > threshold
    if not np.any(mask):
        return np.array([]), 0, 0

    start = np.argmax(mask) * hop_size
    end = (len(mask) - np.argmax(mask[::-1])) * hop_size + frame_size
    return audio[start:end], start, end


# === LOAD WAV ===
rate, data = wav.read(INPUT_FILE)

# Convert to float32 in range [-1, 1] if necessary
if data.dtype != np.float32 and data.dtype != np.float64:
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
    elif data.dtype == np.uint8:
        data = (data.astype(np.float32) - 128) / 128.0
    else:
        raise ValueError(f"Unsupported data type: {data.dtype}")

# Mono conversion if needed
if data.ndim > 1:
    data = data.mean(axis=1)


# === BANDPASS FILTER ===
nyquist = rate / 2
bpf = signal.firwin(4096, [LOW_CUT / nyquist, HIGH_CUT / nyquist], pass_zero=False)
filtered = signal.lfilter(bpf, 1.0, data)

# === Trim silence from bandpassed signal ===
filtered_trimmed, start, end = trim_silence(filtered, threshold=0.01)

if len(filtered_trimmed) == 0:
    raise ValueError("No audio left after silence trimming.")

# Apply the same trim to the original full-band data
data = data[start:end]

# === HILBERT ANALYTIC SIGNAL ===
analytic = signal.hilbert(filtered_trimmed)
inst_phase = np.unwrap(np.angle(analytic))
inst_freq = np.diff(np.unwrap(np.angle(analytic))) * rate / (2 * np.pi)

# === DOWNSAMPLE ===
demodulated = signal.decimate(inst_freq, DECIMATION)

# === NORMALISE OUTPUT TO -1.0 TO 1.0 (OPTIONAL) ===
if NORMALISE_OUTPUT:
    demodulated /= np.max(np.abs(demodulated) + 1e-9)  # avoid divide-by-zero

# === WRITE TO OUTPUT FILE ===
output_rate = rate // DECIMATION
wav.write(OUTPUT_FILE, output_rate, demodulated.astype(np.float32))

# === PLOT ===
t = np.arange(len(data)) / rate
t_demod = np.arange(len(demodulated)) / output_rate

plt.figure(figsize=(12, 6))
plt.subplot(2, 1, 1)
plt.plot(t, data)
plt.title("Original Audio Signal [-1 to 1]")
plt.xlabel("Time (s)")

plt.subplot(2, 1, 2)
plt.plot(t_demod, demodulated)
plt.title("Demodulated Baseband Signal [-1 to 1]")
plt.xlabel("Time (s)")
plt.tight_layout()
plt.show()
