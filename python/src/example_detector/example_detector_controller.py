"""
Created on 17th November 2025
:author: Alan Greer
"""

import logging
import socket
import struct
import threading
import time
from datetime import datetime
from importlib.resources import as_file, files

import example_detector
from odin.adapters.parameter_tree import ParameterTree


class ExampleDetectorController(object):
    # Class constants
    TIME_TICK = 0.1

    def __init__(self, ports: tuple[int]):
        logging.basicConfig(format='%(asctime)-15s %(message)s')
        self._log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        self._log.setLevel(logging.DEBUG)

        # Internal parameters
        self._config_frames = 0
        self._config_exposure_time = 1.0
        self._acquiring = False
        self._acquired_frames = 0
        self._update_time = datetime.now()
        self._udp_socket = None
        self._address = "localhost"
        self._ports = ports
        self._image_bytes = None

        self.load_image()
        self.create_socket()

        # Parameter tree
        self._tree = {
            "config": {
                "frames": (self.get_config_frames, self.set_config_frames, {}),
                "exposure_time": (self.get_exposure_time, self.set_exposure_time, {}),
            },
            "command": {
                "allowed": (["start", "stop"], None, {}),
                "execute": (lambda: "", self.execute, {}),
            },
            "status": {
                "acquiring": (lambda: self._acquiring, None, {}),
                "frames": (lambda: self._acquired_frames, None, {}),
            },
            "module": {"value": "ExampleDetectorAdapter"},
        }
        self._params = ParameterTree(self._tree)

        # Set up acquisition thread
        self._acq_thread_running = True
        self._acq_lock = threading.Lock()
        self._acq_thread = threading.Thread(target=self.update_loop)
        self._acq_thread.start()

    def cleanup(self):
        self._acq_thread_running = False

    def get(self, path):
        return self._params.get(path)

    def set(self, path, data):
        self._params.set(path, data)

    def load_image(self):
        source = files(example_detector).joinpath('image.data')
        with as_file(source) as myfile:
            logging.info("Loading image data from %s", myfile)
            with open(myfile, "rb") as f:
                self._image_bytes = bytearray(f.read())
        for index in range(49, 210):
            self._image_bytes[(209*256)+index] = 150
            self._image_bytes[(230*256)+index] = 150

        for bit in range(33):
            for index in range(210, 230):
                self._image_bytes[(index*256)+209-(bit*5)] = 150

    def create_socket(self):
        # Create the UDP socket
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def set_config_frames(self, value):
        self._config_frames = value

    def get_config_frames(self):
        return self._config_frames

    def set_exposure_time(self, value):
        self._config_exposure_time = value

    def get_exposure_time(self):
        return self._config_exposure_time

    def execute(self, value):
        if value == "start":
            self.start()
        elif value == "stop":
            self.stop()
        else:
            raise Exception("Command %s not supported", value)

    def start(self):
        # Take the lock
        with self._acq_lock:
            # Reset the frames to zero
            self._acquired_frames = 0
            # Set the detector to acquiring
            self._acquiring = True

    def stop(self):
        # Take the lock
        with self._acq_lock:
            # Turn off acquiring
            self._acquiring = False

    def update_loop(self):
        port_idx = 0
        while self._acq_thread_running:
            # Execute at 1/TIME_TICK Hz
            time.sleep(ExampleDetectorController.TIME_TICK)
            # Take the lock
            with self._acq_lock:
                # Are we acquiring
                if self._acquiring:
                    # Have we waited long enough for a new frame
                    if (datetime.now() - self._update_time).total_seconds() >= self._config_exposure_time:
                        port = self._ports[port_idx]
                        # Send the frame
                        logging.info(
                            "Sending frame %d -> %d", self._acquired_frames, port
                        )
                        self.send_frame(self._ports[port_idx])
                        # Increment the frame count
                        self._acquired_frames += 1
                        # Reset the timer
                        self._update_time = datetime.now()
                        # Update port
                        port_idx = (port_idx + 1) % len(self._ports)
                    # Check if the number of frames requested have been sent
                    if self._acquired_frames == self._config_frames:
                        # Turn off acquiring
                        self._acquiring = False
                        port_idx = 0

    def send_frame(self, port: int):
        image_lines = [bytearray(self._image_bytes[i:i + 256]) for i in range(0, len(self._image_bytes), 256)]
        packet = 0
        # Inject the frame number into the data
        # Loop over 32 bits, set 1 bits to black
        for bit in range(32):
            value = self._acquired_frames >> bit & 1
            if value == 1:
                for index in range(210, 230):
                    for pixel in range(208-(bit*5)-3, 208-(bit*5)+1):
                        image_lines[index][pixel] = 1

        for line in image_lines:
            # Create the header information
            header_bytes = struct.pack('<I', self._acquired_frames)
            header_bytes += struct.pack('<I', packet)
            header_bytes += struct.pack('<I', len(line)+12)
            # Create the full packet
            packet_bytes = header_bytes+line
            if line[0] == 0:
                self._log.error("Packet: ", packet_bytes)

            # Send the bytes over UDP
            self._udp_socket.sendto(packet_bytes, (self._address, port))
            packet += 1


def main():
    """Run the odin-data client."""
    app = ExampleDetectorController()
    app.set_config_frames(2)
    app.start()
    time.sleep(10.0)


if __name__ == "__main__":
    main()
