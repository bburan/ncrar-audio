from .osc_client import OSCClient
from .sound_device import SoundDevice


class Babyface(SoundDevice):

    def __init__(self, ip_address=None, send_port=7001, recv_port=9001):
        self.osc_client = OSCClient(ip_address, send_port, recv_port)
        name = 'ASIO Fireface USB'
        super().__init__(name, name)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level='INFO')

    import matplotlib.pyplot as plt
    import numpy as np

    from psiaudio.api import ramped_tone, FlatCalibration
    calibration = FlatCalibration.unity()

    device = Babyface()
    frequencies = np.array([1e3, 2e3])[:, np.newaxis]
    tone = ramped_tone(device.fs, frequency=frequencies, duration=1,
                       rise_time=0.1, level=-6, calibration=calibration)
    recording = device.acquire(tone.T)
    plt.plot(recording)
    plt.axis(ymin=-10, ymax=10)
    plt.show()
