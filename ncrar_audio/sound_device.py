import logging
log = logging.getLogger(__name__)

import threading

import numpy as np
import sounddevice as sd


class BaseCallbackContext:

    def __init__(self):
        self.i = 0

    def _valid_samples(self, samples, status):
        if status:
            log.warning('portaudio callback status: %r', status)

        # Calculate the number of valid samples remaining
        samples_remaining = self.n - self.i
        log.info('%r: %r', self.n, self.i)
        if samples_remaining == 0:
            raise sd.CallbackStop

        valid_samples = min(samples_remaining, samples)
        result = self.i, valid_samples
        self.i += valid_samples
        return result

    def __call__(self, *args):
        raise NotImplementedError


class RecordCallbackContext(BaseCallbackContext):

    def __init__(self, input_buffer):
        super().__init__()
        self.input_buffer = input_buffer
        self.n = len(input_buffer)

    def __call__(self, indata, samples, time, status):
        # Read the next segment to the input buffer
        i, valid_samples = self._valid_samples(samples, status)
        self.input_buffer[i:i + valid_samples] = indata[:valid_samples]


class PlayCallbackContext(BaseCallbackContext):

    def __init__(self, output_buffer):
        super().__init__()
        self.output_buffer = output_buffer
        self.n = len(output_buffer)

    def __call__(self, outdata, samples, time, status):
        # Write the next segment to the output buffer
        i, valid_samples = self._valid_samples(samples, status)
        outdata[:valid_samples] = self.output_buffer[i:i + valid_samples]
        outdata[valid_samples:] = 0


class PlayRecordCallbackContext(BaseCallbackContext):

    def __init__(self, input_buffer, output_buffer):
        super().__init__()
        self.input_buffer = input_buffer
        self.output_buffer = output_buffer
        self.n = len(output_buffer)

    def __call__(self, indata,  outdata, samples, time, status):
        # Read/write the next segments
        i, valid_samples = self._valid_samples(samples, status)
        outdata[:valid_samples] = self.output_buffer[i:i + valid_samples]
        outdata[valid_samples:] = 0
        self.input_buffer[i:i + valid_samples] = indata[:valid_samples]


class SoundDevice:

    def __init__(self, input_device, output_device):
        self.input_device = input_device
        self.input_info = sd.query_devices(self.input_device)
        log.info('Properties for input device %r: %r', self.input_device, self.input_info)

        self.output_device = output_device
        self.output_info = sd.query_devices(self.output_device)
        log.info('Properties for output device %r: %r', self.output_device, self.output_info)

        self.fs = self.input_info['default_samplerate']

    def _start_stream(self, stream_class, **stream_kw):
        event = threading.Event()
        stream = stream_class(finished_callback=event.set, **stream_kw)
        with stream:
            while True:
                if event.wait(0.1):
                    break

    def play(self, waveform):
        cb = PlayCallbackContext(waveform)
        self._start_stream(
            sd.OutputStream,
            device=self.output_device,
            samplerate=self.fs,
            blocksize=1024,
            callback=PlayCallbackContext(waveform),
        )

    def acquire(self, waveform, input_channels=1):
        recording = np.zeros((len(waveform), input_channels), dtype='float32')
        stream = self._start_stream(
            sd.Stream,
            device=(self.input_device, self.output_device),
            samplerate=self.fs,
            blocksize=1024,
            callback=PlayRecordCallbackContext(recording, waveform),
            channels=(input_channels, waveform.shape[-1])
        )
        return recording

    def record(self, n_samples, n_channels):
        log.info('Recording %d samples from %d channels', n_samples, n_channels)
        recording = np.zeros((n_samples, n_channels))
        self._start_stream(
            sd.InputStream,
            device=self.input_device,
            samplerate=self.fs,
            blocksize=1024,
            callback=RecordCallbackContext(recording),
        )
        return recording
