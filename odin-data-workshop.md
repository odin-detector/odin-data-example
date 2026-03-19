# ODIN data workshop
## 26 November 2025
(inspired by https://github.com/stfc-aeg/odin-workshop/blob/master/odin-data.md)

# Table of Contents

* odin-data
  * Frame Receiver
  * Frame Processor
  * Shared Buffers
  * External Software Dependencies
* Building odin-data and odin-data-example applications and libraries
  * C++ Build
  * Python Build
  * Running up the FR and FP application pair
  * Running up the control server
  * Interacting with the applications using a Web browser
* Next steps

## odin-data

* `odin-data` is the _**data plane**_ component of ODIN-based systems
* provides a high-performance, scalable data capture and processing chain
* designed (primarily) for systems sending data as _frames_ over 10GigE+ network links
* consists of two communicating processes:
  * **frame receiver**
  * **frame processor**
* generic applications written in C++ with dynamically-loaded plugins for specific detectors
* both have integrated IPC ZeroMQ channels to allow control/monitoring
* can be integrated with `odin-control`

![ODIN data](images/odin_data.png)

### Frame Receiver

* does what is says on the tin! :+1:
* captures incoming data (UDP, TCP, ZeroMQ channels, +...)
* stores frames in shared memory buffers
* hands off completed frames to frame processor for further processing
* designed to be as lightweight as possible
* tolerant of packet loss and out-of-order data

### Frame Processor

* also does what it says on the tin!
* listens from frame ready notifications from FR via ZeroMQ channel
* passes frames through dynamically-configurable chain of plugins for e.g.:
  * decoding/reordering pixel data
  * applying calibration algorithms (e.g. flat field, b/g subtraction)
  * writes data out to file system in e.g. HDF5 format
  * side-channel plugins for handling e.g. metadata
* future components planned:
  * live image preview endpoint
  * remote streaming endpoint
  * opportunities here for contributions!

### Shared Buffers

* shared buffers are *stateless* - message driven sharing
* each buffer contains header followed by payload
* Header contains metadata describing *state* of received frame, e.g. frame counter, 
number of received packets, missing packets, timestamp etc
* Headers are detector-specific, defined in common include files, e.g:
```
    /*
     * ExcaliburDefinitions.h
     */

    typedef struct
    {
      uint32_t packets_received;
      uint8_t  sof_marker_count;
      uint8_t  eof_marker_count;
      uint8_t  packet_state[max_num_subframes][max_primary_packets + num_tail_packets];
    } FemReceiveState;

    typedef struct
    {
        uint32_t frame_number;
        uint32_t frame_state;
        struct timespec frame_start_time;
        uint32_t total_packets_received;
        uint8_t total_sof_marker_count;
        uint8_t total_eof_marker_count;
        uint8_t num_active_fems;
        uint8_t active_fem_idx[max_num_fems];
        FemReceiveState fem_rx_state[max_num_fems];
    } FrameHeader;
```

### External Software Dependencies

The following libraries and packages are required:

* [CMake](http://www.cmake.org) : build management system (version >= 2.8)
* [Boost](http://www.boost.org) : portable C++ utility libraries. The following components are 
   used - program_options, unit_test_framework, date_time, interprocess, bimap (version >= 1.41)
* [ZeroMQ](http://zeromq.org) : high-performance asynchronous messaging library (version >= 3.2.4)
* [Log4CXX](http://logging.apache.org/log4cxx/): Configurable message logger (version >= 0.10.0)
* [HDF5](https://www.hdfgroup.org/HDF5): __Optional:__ if found, the frame processor application 
will be built (version >= 1.8.14)
* [LibPCAP](https://github.com/the-tcpdump-group/libpcap): TCPDUMP packet capture libraries - usually
 installed with distro install tools. e.g. yum
* [blosc](https://github.com/Blosc/c-blosc): An fast compression library - needed for the frame
 processor compression plugin (__Beware__: API change with version 1.13 -> 1.14)

## Building odin-data and odin-data-example applications and libraries

### C++ Build

1. Create a project development directory and clone the required Odin software:
```
mkdir ~/example
cd ~/example
```
```
git clone https://github.com/odin-detector/odin-data.git
Cloning into 'odin-data'...
remote: Enumerating objects: 25882, done.
remote: Counting objects: 100% (6510/6510), done.
remote: Compressing objects: 100% (985/985), done.
remote: Total 25882 (delta 6144), reused 5576 (delta 5518), pack-reused 19372 (from 3)
Receiving objects: 100% (25882/25882), 86.16 MiB | 18.73 MiB/s, done.
Resolving deltas: 100% (18128/18128), done.
```
```
git clone https://github.com/Observatory-Sciences/odin-data-example.git
Cloning into 'odin-data-example'...
remote: Enumerating objects: 114, done.
remote: Counting objects: 100% (114/114), done.
remote: Compressing objects: 100% (84/84), done.
remote: Total 114 (delta 26), reused 108 (delta 24), pack-reused 0 (from 0)
Receiving objects: 100% (114/114), 474.52 KiB | 14.83 MiB/s, done.
Resolving deltas: 100% (26/26), done.
```

2. Create an `install` directory to install `odin-data` and `odin-data-example` plugins into:
```
mkdir ~/example/install
```

3. Create a build directory for odin-data CMake to use N.B. ODIN uses CMake ***out-of-source*** build semantics:
```
cd ~/example/odin-data
mkdir build && cd build
```

4. Configure CMake to define use of correct packages and set up install directory:
```
cmake -DCMAKE_INSTALL_PREFIX=~/example/install ../cpp/
CMake Warning (dev) at CMakeLists.txt:2 (project):
  cmake_minimum_required() should be called prior to this top-level project()
  call.  Please see the cmake-commands(7) manual for usage documentation of
  both commands.
This warning is for project developers.  Use -Wno-dev to suppress it.

-- The C compiler identification is GNU 13.3.0
-- The CXX compiler identification is GNU 13.3.0
-- Detecting C compiler ABI info
-- Detecting C compiler ABI info - done
-- Check for working C compiler: /usr/bin/cc - skipped
-- Detecting C compile features
-- Detecting C compile features - done
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/c++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
CMake Deprecation Warning at CMakeLists.txt:5 (cmake_minimum_required):
  Compatibility with CMake < 3.5 will be removed from a future version of
  CMake.

  Update the VERSION argument <min> value or use a ...<max> suffix to tell
  CMake that the project does not need compatibility with older versions.


-- Found Boost: /usr/lib/x86_64-linux-gnu/cmake/Boost-1.83.0/BoostConfig.cmake (found suitable version "1.83.0", minimum required is "1.41.0") found components: program_options system filesystem unit_test_framework date_time thread regex 

Looking for log4cxx headers and libraries
-- Found PkgConfig: /usr/bin/pkg-config (found version "1.8.1") 
using pkgconfig
-- Checking for module 'log4cxx'
--   Package 'log4cxx', required by 'virtual:world', not found
-- Found LOG4CXX: /usr/lib/x86_64-linux-gnu/liblog4cxx.so (Required is at least version "0.10.0") 
-- Include directories: /usr/include/log4cxx
-- Libraries: /usr/lib/x86_64-linux-gnu/liblog4cxx.so

Looking for ZeroMQ headers and libraries
-- Checking for one of the modules 'libzmq'
-- Found ZEROMQ: /usr/lib/x86_64-linux-gnu/libzmq.so (found suitable version "4.3.5", minimum required is "4.1.4") 
-- Include directories: /usr/include
-- Libraries: /usr/lib/x86_64-linux-gnu/libzmq.so

Looking for pcap headers and libraries
-- Found PCAP: /usr/lib/x86_64-linux-gnu/libpcap.so (Required is at least version "1.4.0") 
-- Performing Test PCAP_LINKS
-- Performing Test PCAP_LINKS - Success

Looking for blosc headers and libraries
-- Found Blosc: /usr/lib/x86_64-linux-gnu/libblosc.so

Looking for kafka headers and libraries
-- Could not find the Kafka library.

Checking Boost version placeholder support
-- Boost version 1.83.0 has placeholders

Searching for HDF5
-- Found HDF5: /usr/lib/x86_64-linux-gnu/hdf5/serial/libhdf5.so;/usr/lib/x86_64-linux-gnu/libcrypto.so;/usr/lib/x86_64-linux-gnu/libcurl.so;/usr/lib/x86_64-linux-gnu/libpthread.a;/usr/lib/x86_64-linux-gnu/libsz.so;/usr/lib/x86_64-linux-gnu/libz.so;/usr/lib/x86_64-linux-gnu/libdl.a;/usr/lib/x86_64-linux-gnu/libm.so (found suitable version "1.10.10", minimum required is "1.8.14") found components: C HL 
-- HDF5 include files:  /usr/include/hdf5/serial
-- HDF5 libs:           /usr/lib/x86_64-linux-gnu/hdf5/serial/libhdf5.so/usr/lib/x86_64-linux-gnu/libcrypto.so/usr/lib/x86_64-linux-gnu/libcurl.so/usr/lib/x86_64-linux-gnu/libpthread.a/usr/lib/x86_64-linux-gnu/libsz.so/usr/lib/x86_64-linux-gnu/libz.so/usr/lib/x86_64-linux-gnu/libdl.a/usr/lib/x86_64-linux-gnu/libm.so/usr/lib/x86_64-linux-gnu/hdf5/serial/libhdf5_hl.so
-- HDF5 defs:           

Determining odin-data version
-- Git describe version: 1.11.0-23-g50e37dbc
-- major:1 minor:11 patch:0 sha1:g50e37dbc
-- short version: 1.11.0
-- Configuring done (1.7s)
-- Generating done (0.2s)
-- Build files have been written to: ~/example/odin-data/build
```

5. Build odin-data:
```
make -j4
```
```
[  2%] Building CXX object common/src/CMakeFiles/OdinData.dir/DebugLevelLogger.cpp.o
[  2%] Building CXX object common/src/CMakeFiles/OdinData.dir/IpcChannel.cpp.o
[  4%] Generating ../../test_config/client_msgs/config_ctrl_chan_port_5000.json
[  4%] Building CXX object frameSimulator/src/CMakeFiles/DummyUDPFrameSimulatorPlugin.dir/DummyUDPFrameSimulatorPlugin.cpp.o
[  5%] Generating ../../test_config/client_msgs/config_ctrl_chan_port_5010.json
[  5%] Generating ../../test_config/client_msgs/reconfig_buffer_manager.json
[  6%] Generating ../../test_config/client_msgs/reconfig_decoder.json
[  7%] Generating ../../test_config/client_msgs/reconfig_endpoints.json
[  8%] Generating ../../test_config/client_msgs/reconfig_rx_thread.json
[  8%] Built target CopyClientMsgFiles
[  8%] Building CXX object frameSimulator/src/CMakeFiles/DummyUDPFrameSimulatorPlugin.dir/DummyUDPFrameSimulatorPluginLib.cpp.o
[  8%] Building CXX object common/src/CMakeFiles/OdinData.dir/IpcMessage.cpp.o
[  9%] Building CXX object common/src/CMakeFiles/OdinData.dir/IpcReactor.cpp.o
[ 10%] Building CXX object common/src/CMakeFiles/OdinData.dir/Json.cpp.o

<< snip >>  NOTE warnings are currently generated by the compiler but there should be no build errors

[ 93%] Linking CXX shared library ../../lib/libGapFillPlugin.so
[ 93%] Built target GapFillPlugin
[ 95%] Building CXX object frameProcessor/test/CMakeFiles/frameProcessorTest.dir/DummyUDPProcessPluginTest.cpp.o
[ 95%] Building CXX object frameProcessor/test/CMakeFiles/frameProcessorTest.dir/FrameProcessorTest.cpp.o
[ 95%] Building CXX object frameProcessor/test/CMakeFiles/frameProcessorTest.dir/FrameProcessorUnitTestMain.cpp.o
[ 96%] Building CXX object frameProcessor/test/CMakeFiles/frameProcessorTest.dir/GapFillPluginTest.cpp.o
[ 97%] Linking CXX executable ../../bin/frameSimulator
[ 97%] Built target frameSimulator
[ 98%] Building CXX object frameProcessor/test/CMakeFiles/frameProcessorTest.dir/MetaMessageTest.cpp.o
[ 99%] Building CXX object frameProcessor/test/CMakeFiles/frameProcessorTest.dir/BloscPluginTest.cpp.o
[100%] Linking CXX executable ../../bin/frameProcessorTest
[100%] Built target frameProcessorTest
```

6. Install the applications:
```
make install
```
```
[  7%] Built target OdinData
[  9%] Built target FrameReceiver
[ 14%] Built target frameReceiver
[ 17%] Built target DummyUDPFrameDecoder
[ 19%] Built target DummyTCPFrameDecoder
[ 33%] Built target frameReceiverTest
[ 44%] Built target FrameProcessor
[ 47%] Built target frameProcessor
[ 50%] Built target DummyUDPProcessPlugin
[ 52%] Built target BloscPlugin
[ 56%] Built target Hdf5Plugin
[ 58%] Built target ParameterAdjustmentPlugin
[ 61%] Built target OffsetAdjustmentPlugin
[ 64%] Built target LiveViewPlugin
[ 67%] Built target SumPlugin
[ 69%] Built target GapFillPlugin
[ 75%] Built target frameProcessorTest
[ 79%] Built target FrameSimulator
[ 84%] Built target frameSimulator
[ 86%] Built target DummyUDPFrameSimulatorPlugin
[ 88%] Built target test_rewind
[ 91%] Built target odinDataTest
[ 95%] Built target frameTests
[100%] Built target CopyClientMsgFiles
Install the project...
-- Install configuration: ""
-- Installing: ~/example/install/cmake/FindBlosc.cmake

<< snip >>

-- Installing: ~/example/install/test_config/fp_log4cxx.xml
-- Installing: ~/example/install/test_config/fr_log4cxx.xml
-- Installing: ~/example/install/test_config/fs_log4cxx.xml
```

7. Now switch to the odin-data-example plugins and configure CMake. Note that this time the root to the odin-data installation must also be specified:
```
cd ~/example/odin-data-example/
mkdir build && cd build
cmake -DODINDATA_ROOT_DIR=~/example/install -DCMAKE_INSTALL_PREFIX=~/example/install ../cpp/
```
```
CMake Deprecation Warning at CMakeLists.txt:2 (cmake_minimum_required):
  Compatibility with CMake < 3.5 will be removed from a future version of
  CMake.

  Update the VERSION argument <min> value or use a ...<max> suffix to tell
  CMake that the project does not need compatibility with older versions.



Looking for log4cxx headers and libraries
using pkgconfig
-- Checking for module 'log4cxx'
--   Package 'log4cxx', required by 'virtual:world', not found
-- Include directories: /usr/include/log4cxx
-- Libraries: /usr/lib/x86_64-linux-gnu/liblog4cxx.so

Looking for ZeroMQ headers and libraries
-- Include directories: /usr/include
-- Libraries: /usr/lib/x86_64-linux-gnu/libzmq.so

Looking for odinData headers and libraries
-- Root dir: ~/example/install
using pkgconfig
-- Checking for module 'odinData'
--   Package 'odinData', required by 'virtual:world', not found
-- Include directories: ~/example/install/include;~/example/install/include/frameReceiver;~/example/install/include/frameProcessor
-- Libraries: ~/example/install/lib/libOdinData.so;~/example/install/lib/libFrameProcessor.so;~/example/install/lib/libFrameReceiver.so
-- Configuring done (0.1s)
-- Generating done (0.0s)
-- Build files have been written to: ~/example/odin-data-example/build
```

8. Build odin-data-example:
```
make -j4
```
```
[ 16%] Building CXX object frameProcessor/src/CMakeFiles/ExampleDetectorPlugin.dir/ExampleDetectorPlugin.cpp.o
[ 33%] Building CXX object frameReceiver/src/CMakeFiles/ExampleDetectorFrameDecoder.dir/ExampleDetectorDecoderLib.cpp.o
[ 50%] Building CXX object frameProcessor/src/CMakeFiles/ExampleDetectorPlugin.dir/ExampleDetectorPluginLib.cpp.o
[ 66%] Building CXX object frameReceiver/src/CMakeFiles/ExampleDetectorFrameDecoder.dir/ExampleDetectorDecoder.cpp.o
[ 83%] Linking CXX shared library ../../lib/libExampleDetectorFrameDecoder.so
[ 83%] Built target ExampleDetectorFrameDecoder
[100%] Linking CXX shared library ../../lib/libExampleDetectorPlugin.so
[100%] Built target ExampleDetectorPlugin
```

9. Install the applications:
```
make install
```
```
[ 50%] Built target ExampleDetectorFrameDecoder
[100%] Built target ExampleDetectorPlugin
Install the project...
-- Install configuration: ""
-- Up-to-date: /home/ajg/example/install/cmake/FindLOG4CXX.cmake
-- Up-to-date: /home/ajg/example/install/cmake/FindODINDATA.cmake
-- Up-to-date: /home/ajg/example/install/cmake/FindZEROMQ.cmake
-- Up-to-date: /home/ajg/example/install/cmake/GetGitRevisionDescription.cmake
-- Up-to-date: /home/ajg/example/install/cmake/GetGitRevisionDescription.cmake.in
-- Up-to-date: /home/ajg/example/install/lib/libExampleDetectorFrameDecoder.so
-- Up-to-date: /home/ajg/example/install/lib/libExampleDetectorPlugin.so
-- Installing: /home/ajg/example/install/example_detector/frameProcessor.sh
-- Installing: /home/ajg/example/install/example_detector/frameReceiver.sh
-- Installing: /home/ajg/example/install/example_detector/example-detector-fp.json
-- Installing: /home/ajg/example/install/example_detector/example-detector-fr.json
-- Up-to-date: /home/ajg/example/install/example_detector/example-detector.cfg
-- Installing: /home/ajg/example/install/example_detector/static/index.html
-- Installing: /home/ajg/example/install/example_detector/static/js
-- Installing: /home/ajg/example/install/example_detector/static/js/jquery-3.2.1.min.js
-- Installing: /home/ajg/example/install/example_detector/static/js/jquery-ui.min.js
-- Installing: /home/ajg/example/install/example_detector/static/js/odin-data.js
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/js
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/js/npm.js
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/js/bootstrap.js
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/js/bootstrap.min.js
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/fonts
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/fonts/glyphicons-halflings-regular.woff
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/fonts/glyphicons-halflings-regular.svg
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/fonts/glyphicons-halflings-regular.woff2
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/fonts/glyphicons-halflings-regular.ttf
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/fonts/glyphicons-halflings-regular.eot
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/css
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/css/bootstrap.min.css
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/css/bootstrap-theme.min.css.map
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/css/bootstrap-theme.css
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/css/bootstrap.min.css.map
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/css/bootstrap-theme.css.map
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/css/bootstrap.css.map
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/css/bootstrap-theme.min.css
-- Installing: /home/ajg/example/install/example_detector/static/js/bootstrap-3.3.7-dist/css/bootstrap.css
-- Installing: /home/ajg/example/install/example_detector/static/img
-- Installing: /home/ajg/example/install/example_detector/static/img/green-led-on.png
-- Installing: /home/ajg/example/install/example_detector/static/img/odin_logo.png
-- Installing: /home/ajg/example/install/example_detector/static/img/odin_logo.jpg
-- Installing: /home/ajg/example/install/example_detector/static/img/green-led-off.png
-- Installing: /home/ajg/example/install/example_detector/static/img/led-off.png
```

### Python Build

1. Create the Python virtual environment:
```
cd ~/example
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install opencv-python
```

2. Install odin-data Python module (pulls in odin-control):
```
cd ~/example/odin-data/python
pip install .
```
```
Processing /home/ajg/example/odin-data/python
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Preparing metadata (pyproject.toml) ... done
Collecting odin-control@ git+https://****@github.com/odin-detector/odin-control (from odin-data==1.11.1.dev24+g12efef2b0)
  Cloning https://****@github.com/odin-detector/odin-control to /tmp/pip-install-l2s3o0gw/odin-control_3b84dabd5e3844f6bd265950d5b03c3a
  Running command git clone --filter=blob:none --quiet 'https://****@github.com/odin-detector/odin-control' /tmp/pip-install-l2s3o0gw/odin-control_3b84dabd5e3844f6bd265950d5b03c3a
  Resolved https://****@github.com/odin-detector/odin-control to commit 1cf475b60abf66666d31c7e74b9d19540c2ea6c3
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Preparing metadata (pyproject.toml) ... done
Collecting posix_ipc>=1.0.4 (from odin-data==1.11.1.dev24+g12efef2b0)
  Using cached posix_ipc-1.3.2-cp312-cp312-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (2.5 kB)
Collecting pysnmp>=4.4.4 (from odin-data==1.11.1.dev24+g12efef2b0)
  Using cached pysnmp-7.1.22-py3-none-any.whl.metadata (5.5 kB)
Collecting numpy>=1.14.0 (from odin-data==1.11.1.dev24+g12efef2b0)
  Using cached numpy-2.3.5-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (62 kB)
Collecting pyzmq>=17.1.0 (from odin-data==1.11.1.dev24+g12efef2b0)
  Using cached pyzmq-27.1.0-cp312-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl.metadata (6.0 kB)
Collecting pygelf>=0.3.5 (from odin-data==1.11.1.dev24+g12efef2b0)
  Using cached pygelf-0.4.3-py3-none-any.whl.metadata (8.7 kB)
Collecting deepdiff (from odin-data==1.11.1.dev24+g12efef2b0)
  Using cached deepdiff-8.6.1-py3-none-any.whl.metadata (8.6 kB)
Collecting tornado>=4.3 (from odin-control@ git+https://git@github.com/odin-detector/odin-control->odin-data==1.11.1.dev24+g12efef2b0)
  Using cached tornado-6.5.2-cp39-abi3-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (2.8 kB)
Collecting future (from odin-control@ git+https://git@github.com/odin-detector/odin-control->odin-data==1.11.1.dev24+g12efef2b0)
  Using cached future-1.0.0-py3-none-any.whl.metadata (4.0 kB)
Collecting psutil>=5.0 (from odin-control@ git+https://git@github.com/odin-detector/odin-control->odin-data==1.11.1.dev24+g12efef2b0)
  Using cached psutil-7.1.3-cp36-abi3-manylinux2010_x86_64.manylinux_2_12_x86_64.manylinux_2_28_x86_64.whl.metadata (23 kB)
Collecting pyasn1!=0.5.0,>=0.4.8 (from pysnmp>=4.4.4->odin-data==1.11.1.dev24+g12efef2b0)
  Using cached pyasn1-0.6.1-py3-none-any.whl.metadata (8.4 kB)
Collecting orderly-set<6,>=5.4.1 (from deepdiff->odin-data==1.11.1.dev24+g12efef2b0)
  Using cached orderly_set-5.5.0-py3-none-any.whl.metadata (6.6 kB)
Using cached numpy-2.3.5-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.6 MB)
Using cached posix_ipc-1.3.2-cp312-cp312-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (52 kB)
Using cached psutil-7.1.3-cp36-abi3-manylinux2010_x86_64.manylinux_2_12_x86_64.manylinux_2_28_x86_64.whl (263 kB)
Using cached pygelf-0.4.3-py3-none-any.whl (8.8 kB)
Using cached pysnmp-7.1.22-py3-none-any.whl (343 kB)
Using cached pyasn1-0.6.1-py3-none-any.whl (83 kB)
Using cached pyzmq-27.1.0-cp312-abi3-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl (840 kB)
Using cached tornado-6.5.2-cp39-abi3-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (443 kB)
Using cached deepdiff-8.6.1-py3-none-any.whl (91 kB)
Using cached orderly_set-5.5.0-py3-none-any.whl (13 kB)
Using cached future-1.0.0-py3-none-any.whl (491 kB)
Building wheels for collected packages: odin-data, odin-control
  Building wheel for odin-data (pyproject.toml) ... done
  Created wheel for odin-data: filename=odin_data-1.11.1.dev24+g12efef2b0-py3-none-any.whl size=49774 sha256=d0608373a287549a90e4d41cc967409bb31ab2bba8b9bf4e70cdd7da275a8b1c
  Stored in directory: /tmp/pip-ephem-wheel-cache-xkglzdne/wheels/29/83/90/854bc71162fb2e44eaf75054f3518df82b815531862724fb57
  Building wheel for odin-control (pyproject.toml) ... done
  Created wheel for odin-control: filename=odin_control-1.6.1.dev2+g1cf475b60-py3-none-any.whl size=65080 sha256=c315525a5ba74177e2bdadc28dcdaae648e9d770ac01cf4eaf85a354343bf524
  Stored in directory: /tmp/pip-ephem-wheel-cache-xkglzdne/wheels/05/eb/15/366e3ea5be5b681aed22a2ceae717c1edc6ae61336d8563177
Successfully built odin-data odin-control
Installing collected packages: pygelf, posix_ipc, tornado, pyzmq, pyasn1, psutil, orderly-set, numpy, future, pysnmp, odin-control, deepdiff, odin-data
Successfully installed deepdiff-8.6.1 future-1.0.0 numpy-2.3.5 odin-control-1.6.1.dev2+g1cf475b60 odin-data-1.11.1.dev24+g12efef2b0 orderly-set-5.5.0 posix_ipc-1.3.2 psutil-7.1.3 pyasn1-0.6.1 pygelf-0.4.3 pysnmp-7.1.22 pyzmq-27.1.0 tornado-6.5.2
```

3. Install odin-data-example Python module:
```
cd ~/example/odin-data-example/python
pip install .
```
```
Processing /home/ajg/example/odin-data-example/python
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Preparing metadata (pyproject.toml) ... done
Collecting odin_control@ git+https://****@github.com/odin-detector/odin-control.git (from example-detector==0.2.dev3+g51f0cd520.d20251124)
  Cloning https://****@github.com/odin-detector/odin-control.git to /tmp/pip-install-74dajqdf/odin-control_d727d988a25e44d897f4d4653073c81d
  Running command git clone --filter=blob:none --quiet 'https://****@github.com/odin-detector/odin-control.git' /tmp/pip-install-74dajqdf/odin-control_d727d988a25e44d897f4d4653073c81d
  Resolved https://****@github.com/odin-detector/odin-control.git to commit 1cf475b60abf66666d31c7e74b9d19540c2ea6c3
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Preparing metadata (pyproject.toml) ... done
Requirement already satisfied: tornado>=4.3 in /home/ajg/example/venv/lib/python3.12/site-packages (from example-detector==0.2.dev3+g51f0cd520.d20251124) (6.5.2)
Requirement already satisfied: future in /home/ajg/example/venv/lib/python3.12/site-packages (from example-detector==0.2.dev3+g51f0cd520.d20251124) (1.0.0)
Requirement already satisfied: pyzmq>=17.1.0 in /home/ajg/example/venv/lib/python3.12/site-packages (from odin_control@ git+https://git@github.com/odin-detector/odin-control.git->example-detector==0.2.dev3+g51f0cd520.d20251124) (27.1.0)
Requirement already satisfied: psutil>=5.0 in /home/ajg/example/venv/lib/python3.12/site-packages (from odin_control@ git+https://git@github.com/odin-detector/odin-control.git->example-detector==0.2.dev3+g51f0cd520.d20251124) (7.1.3)
Building wheels for collected packages: example-detector
  Building wheel for example-detector (pyproject.toml) ... done
  Created wheel for example-detector: filename=example_detector-0.2.dev3+g51f0cd520.d20251124-py3-none-any.whl size=14298 sha256=16818eedcac41be377b0b1e91539b903c0560cb4fd041cb6cce24fd81f3808cd
  Stored in directory: /tmp/pip-ephem-wheel-cache-lbfzj96s/wheels/96/04/27/3a7a1a2086b4a0d6714326844454d8fbb05a1308e554151250
Successfully built example-detector
Installing collected packages: example-detector
Successfully installed example-detector-0.2.dev3+g51f0cd520.d20251124
```

### Running up the FR and FP application pair

1. Take a look at the odin-data-example Frame Receiver configuration file:
```
cd ~/example/install/example_detector
```
```
cat example-detector-fr.json
[
  {
    "frame_ready_endpoint": "tcp://127.0.0.1:5001",
    "frame_release_endpoint": "tcp://127.0.0.1:5002",
    "decoder_type": "ExampleDetector",
    "decoder_path": "~/example/install/lib",
    "rx_ports": "61649",
    "max_buffer_mem": 10000000,
    "decoder_config": {
      "enable_packet_logging": false,
      "frame_timeout_ms": 1000,
      "udp_packets_per_frame": 256,
      "udp_packet_size": 1012
    }
  }
]
```

2. Run the Frame Receiver application:
```
./frameReceiver.sh
17:23:08,912  FR.App           DEBUG - Debug level set to  3
17:23:08,913  FR.App           DEBUG - Setting number of IO threads to 1
17:23:08,913  FR.App           DEBUG - Setting control channel endpoint to tcp://0.0.0.0:5000
17:23:08,913  FR.App           DEBUG - Loading JSON configuration file /home/ajg/example/install/example_detector/example-detector-fr.json
17:23:08,913  FR.App           INFO  - frameReceiver version 1.11.0-23-g50e37dbc starting up
17:23:08,918  FR.Controller    TRACE - FrameRecevierController constructor
17:23:08,920  FR.Controller    DEBUG - Configuration submitted: {"params":{"ctrl_endpoint":"tcp://0.0.0.0:5000","rx_endpoint":"inproc://rx_channel"},"msg_type":"illegal","msg_val":"illegal","id":0,"timestamp":"2025-11-24T17:23:08.918642"}
17:23:08,921  FR.Controller    DEBUG - Not unbinding channel as not bound to endpoint 
17:23:08,921  FR.Controller    DEBUG - Binding control channel to endpoint: tcp://0.0.0.0:5000
17:23:08,923  FR.Controller    DEBUG - Not unbinding channel as not bound to endpoint 
17:23:08,923  FR.Controller    DEBUG - Binding receiver thread channel to endpoint: inproc://rx_channel
17:23:08,923  FR.Controller    DEBUG - Configuring decoder with {"params":{"ctrl_endpoint":"tcp://0.0.0.0:5000","rx_endpoint":"inproc://rx_channel"},"msg_type":"illegal","msg_val":"illegal","id":0,"timestamp":"2025-11-24T17:23:08.918642"}
17:23:08,924  FR.Controller    INFO  - RX thread not configured as frame decoder and/or buffer manager configured
17:23:08,925  FR.Controller    DEBUG - Configuration submitted: {"params":{"frame_ready_endpoint":"tcp://127.0.0.1:5001","frame_release_endpoint":"tcp://127.0.0.1:5002","decoder_type":"ExampleDetector","decoder_path":"/home/ajg/example/install/lib","rx_ports":"61649","max_buffer_mem":10000000,"decoder_config":{"enable_packet_logging":false,"frame_timeout_ms":1000,"udp_packets_per_frame":256,"udp_packet_size":1012}},"msg_type":"cmd","msg_val":"configure","id":0,"timestamp":"2025-11-24T17:23:08.925287"}
17:23:08,925  FR.Controller    DEBUG - Not unbinding channel as not bound to endpoint 
17:23:08,925  FR.Controller    DEBUG - Binding frame ready notification channel to endpoint: tcp://127.0.0.1:5001
17:23:08,926  FR.Controller    DEBUG - Not unbinding channel as not bound to endpoint 
17:23:08,926  FR.Controller    DEBUG - Binding frame release notification channel to endpoint: tcp://127.0.0.1:5002
17:23:08,926  FR.Controller    DEBUG - Configuring decoder with {"params":{"frame_ready_endpoint":"tcp://127.0.0.1:5001","frame_release_endpoint":"tcp://127.0.0.1:5002","decoder_type":"ExampleDetector","decoder_path":"/home/ajg/example/install/lib","rx_ports":"61649","max_buffer_mem":10000000,"decoder_config":{"enable_packet_logging":false,"frame_timeout_ms":1000,"udp_packets_per_frame":256,"udp_packet_size":1012}},"msg_type":"cmd","msg_val":"configure","id":0,"timestamp":"2025-11-24T17:23:08.925287"}
17:23:08,927  FR.Controller    DEBUG - Built new decoder configuration message: {"params":{"enable_packet_logging":false,"frame_timeout_ms":1000,"udp_packets_per_frame":256,"udp_packet_size":1012},"msg_type":"illegal","msg_val":"illegal","id":0,"timestamp":"2025-11-24T17:23:08.913462"}
17:23:08,927  FR.Controller    INFO  - Loading decoder plugin ExampleDetectorFrameDecoder from /home/ajg/example/install/lib/libExampleDetectorFrameDecoder.so
17:23:08,931  FR.ExampleDetectorDecoderPlugin INFO  - ExampleDetectorDecoder version 0.0.0 loaded
17:23:08,931  FR.Controller    INFO  - Created ExampleDetectorFrameDecoder frame decoder instance
17:23:08,986  FR.Controller    DEBUG - Configured frame buffer manager of total size 10000000 with 151 buffers
17:23:08,987  FR.UDPRxThread   DEBUG - FrameReceiverUDPRxThread constructor entered....
17:23:08,987  FR.RxThread      DEBUG - Running RX thread service
17:23:08,988  FR.RxThread      DEBUG - Connecting RX channel to endpoint inproc://rx_channel
17:23:08,988  FR.UDPRxThread   DEBUG - Running UDP RX thread service
17:23:08,988  FR.UDPRxThread   DEBUG - RX thread receive buffer size for port 61649 is 212992
17:23:08,988  FR.RxThread      DEBUG - Advertising RX thread identity
17:23:08,988  FR.RxThread      DEBUG - Requesting buffer precharge
17:23:08,990  FR.Controller    TRACE - FrameReceiverController::run()
17:23:08,990  FR.Controller    DEBUG - Main thread entering reactor loop
17:23:08,990  FR.Controller    DEBUG - Got identity announcement from RX thread: 3292-e961
17:23:08,991  FR.Controller    DEBUG - Got buffer precharge request from RX thread
17:23:08,991  FR.RxThread      DEBUG - RX thread received acknowledgement of identity notification
17:23:08,991  FR.RxThread      DEBUG - Precharged 151 empty buffers onto queue, length is now 151
17:23:09,987  FR.Controller    DEBUG - Notifying downstream processes of shared buffer configuration
17:23:09,988  FR.ExampleDetectorDecoderPlugin DEBUG - 0 frame buffers in use, 151 empty buffers available, 0 incomplete frames timed out
17:23:10,988  FR.ExampleDetectorDecoderPlugin DEBUG - 0 frame buffers in use, 151 empty buffers available, 0 incomplete frames timed out
```

3. Take a look at the odin-data-example Frame Processor configuration file:
```
cd ~/example/install/example_detector
```
```
cat example-detector-fp.json 
[
	{
		"fr_setup": {
			"fr_ready_cnxn": "tcp://127.0.0.1:5001",
			"fr_release_cnxn": "tcp://127.0.0.1:5002"
		},
		"meta_endpoint": "tcp://*:5008"
	},
	{
		"plugin": {
			"load": {
				"index": "hdf",
				"name": "FileWriterPlugin",
				"library": "~/example/install/lib/libHdf5Plugin.so"
			}
		}
	},
	{
		"plugin": {
			"load": {
				"index": "example",
				"name": "ExampleDetectorPlugin",
				"library": "~/example/install/lib/libExampleDetectorPlugin.so"
			}
		}
	},
	{
		"plugin": {
			"connect": {
				"index": "example",
				"connection": "frame_receiver"
			}
		}
	},
	{
		"plugin": {
			"connect": {
				"index": "hdf",
				"connection": "example"
			}
		}
	},
	{
		"hdf": {
			"dataset": {
				"example": {
					"datatype": "uint8",
					"dims": [
						256,
						256
					],
					"compression": "none"
				}
			},
			"file": {
				"path": "/tmp",
				"first_number": 0
			},
			"timeout_timer_period": 3000
		}
	}
]
```

4. Run the Frame Processor application:
```
./frameProcessor.sh 
17:47:35,936  FP.App           DEBUG - log4cxx config file is set to /home/ajg/example/install/test_config/fp_log4cxx.xml
17:47:35,936  FP.App           DEBUG - Debug level set to  3
17:47:35,936  FP.App           DEBUG - Setting number of IO threads to 1
17:47:35,936  FP.App           DEBUG - Setting control channel endpoint to tcp://0.0.0.0:5004
17:47:35,936  FP.App           DEBUG - Loading JSON configuration file /home/ajg/example/install/example_detector/example-detector-fp.json
17:47:35,936  FP.App           INFO  - frameProcessor version 1.11.0-23-g50e37dbc starting up
17:47:35,937  FP.FrameProcessorController DEBUG - Running IPC thread service
17:47:35,937  FP.FrameProcessorController DEBUG - Constructing FrameProcessorController
17:47:35,938  FP.FrameProcessorController DEBUG - Connecting meta RX channel to endpoint: inproc://meta_rx
17:47:35,940  FP.FrameProcessorController DEBUG - Configuration submitted: {"params":{"ctrl_endpoint":"tcp://0.0.0.0:5004"},"msg_type":"illegal","msg_val":"illegal","id":0,"timestamp":"2025-11-24T17:47:35.939173"}
17:47:35,940  FP.FrameProcessorController DEBUG - Connecting control channel to endpoint: tcp://0.0.0.0:5004
17:47:35,941  FP.FrameProcessorController DEBUG - Configuration submitted: {"params":{"fr_setup":{"fr_ready_cnxn":"tcp://127.0.0.1:5001","fr_release_cnxn":"tcp://127.0.0.1:5002"},"meta_endpoint":"tcp://*:5008"},"msg_type":"cmd","msg_val":"configure","id":0,"timestamp":"2025-11-24T17:47:35.941416"}
17:47:35,941  FP.FrameProcessorController DEBUG - Connecting meta TX channel to endpoint: tcp://*:5008
17:47:35,941  FP.FrameProcessorController DEBUG - Shared Memory Config: Publisher=tcp://127.0.0.1:5002 Subscriber=tcp://127.0.0.1:5001
17:47:35,942  FP.SharedMemoryController TRACE - SharedMemoryController constructor.
17:47:35,942  FP.SharedMemoryController DEBUG - Connecting RX Channel to endpoint: tcp://127.0.0.1:5001
17:47:35,942  FP.SharedMemoryController DEBUG - Connecting TX Channel to endpoint: tcp://127.0.0.1:5002
17:47:35,942  FP.SharedMemoryController DEBUG - Registering timer for deferred shared buffer configuration request
17:47:35,942  FP.FrameProcessorController DEBUG - Configuration submitted: {"params":{"plugin":{"load":{"index":"hdf","name":"FileWriterPlugin","library":"/home/ajg/example/install/lib/libHdf5Plugin.so"}}},"msg_type":"cmd","msg_val":"configure","id":0,"timestamp":"2025-11-24T17:47:35.942619"}
17:47:35,972  FP.FileWriterPlugin INFO  - FileWriterPlugin version 1.11.0-23-g50e37dbc loaded
17:47:35,972  FP.Acquisition   TRACE - Acquisition constructor.
17:47:35,972  FP.Acquisition   TRACE - Acquisition constructor.
17:47:35,973  FP.FrameProcessorPlugin DEBUG - Registering blocking callback controller with hdf
17:47:35,973  FP.FrameProcessorController INFO  - Class FileWriterPlugin loaded as index = hdf
17:47:35,973  FP.FrameProcessorController DEBUG - Configuration submitted: {"params":{"plugin":{"load":{"index":"example","name":"ExampleDetectorPlugin","library":"/home/ajg/example/install/lib/libExampleDetectorPlugin.so"}}},"msg_type":"cmd","msg_val":"configure","id":0,"timestamp":"2025-11-24T17:47:35.973533"}
17:47:35,975  FP.ExampleDetectorPlugin INFO  - LATRDProcessPlugin version 0.0.0 loaded
17:47:35,975  FP.FrameProcessorController INFO  - Class ExampleDetectorPlugin loaded as index = example
17:47:35,975  FP.FrameProcessorController DEBUG - Configuration submitted: {"params":{"plugin":{"connect":{"index":"example","connection":"frame_receiver"}}},"msg_type":"cmd","msg_val":"configure","id":0,"timestamp":"2025-11-24T17:47:35.975827"}
17:47:35,976  FP.FrameProcessorController DEBUG - Configuration submitted: {"params":{"plugin":{"connect":{"index":"hdf","connection":"example"}}},"msg_type":"cmd","msg_val":"configure","id":0,"timestamp":"2025-11-24T17:47:35.976067"}
17:47:35,976  FP.FrameProcessorPlugin DEBUG - Registering non-blocking callback hdf with example
17:47:35,976  FP.FrameProcessorController DEBUG - Configuration submitted: {"params":{"hdf":{"dataset":{"example":{"datatype":"uint8","dims":[256,256],"compression":"none"}},"file":{"path":"/tmp","first_number":0},"timeout_timer_period":3000}},"msg_type":"cmd","msg_val":"configure","id":0,"timestamp":"2025-11-24T17:47:35.976278"}
17:47:35,976  FP.FileWriterPlugin INFO  - {"params":{"dataset":{"example":{"datatype":"uint8","dims":[256,256],"compression":"none"}},"file":{"path":"/tmp","first_number":0},"timeout_timer_period":3000},"msg_type":"cmd","msg_val":"configure","id":0,"timestamp":"2025-11-24T17:47:35.976389"}
17:47:35,976  FP.FileWriterPlugin DEBUG - Configure file name and path
17:47:35,977  FP.FileWriterPlugin DEBUG - Next file path changed to /tmp
17:47:35,977  FP.FileWriterPlugin DEBUG - File name first index number changed to 0
17:47:35,977  FP.FileWriterPlugin INFO  - Checking for string name of dataset
17:47:35,978  FP.FileWriterPlugin INFO  - Dataset name example found, creating...
17:47:35,978  FP.FileWriterPlugin DEBUG - Configuring dataset [example]
17:47:35,978  FP.FileWriterPlugin INFO  - Enabling compression: 1
17:47:35,979  FP.FileWriterPlugin INFO  - Setting close file timeout to 3000
17:47:35,979  FP.FrameProcessorController INFO  - Running frame processor
17:47:36,943  FP.SharedMemoryController DEBUG - Requesting shared buffer configuration from frame receiver
17:47:36,944  FP.SharedMemoryController DEBUG - RX thread called with message: {"params":{"shared_buffer_name":"OdinDataBuffer"},"msg_type":"notify","msg_val":"buffer_config","id":0,"timestamp":"2025-11-24T17:47:36.944041"}
17:47:36,944  FP.SharedMemoryController DEBUG - Shared buffer config notification received for OdinDataBuffer
17:47:36,944  FP.SharedMemoryController DEBUG - Initialised shared buffer manager for buffer OdinDataBuffer
```

### Running up the control server

1. Activate the virtual environment
```
source ~/example/venv/bin/activate
```
2. Take look at the odin-data-example server configuration file
```
cd ~/example/install/example_detector
```
```
more example-detector.cfg
[server]
debug_mode = 1
http_port  = 8888
http_addr  = 127.0.0.1
static_path = ~/example/install/example_detector/static
adapters   = detector, fr, fp, system_info

[tornado]
logging = error

[adapter.detector]
module = example_detector.example_detector_adapter.ExampleDetectorAdapter
update_interval = 0.5

[adapter.fr]
module = odin_data.control.frame_receiver_adapter.FrameReceiverAdapter
endpoints = 127.0.0.1:5000
update_interval = 0.5

[adapter.fp]
module = odin_data.control.frame_processor_adapter.FrameProcessorAdapter
endpoints = 127.0.0.1:5004
update_interval = 0.5

[adapter.system_info]
module = odin.adapters.system_info.SystemInfoAdapter
```

3. Run the control server
```
odin_control --config=./example-detector.cfg
```

### Interacting with the applications using a Web browser

1. Log into the workstation that is running the applications.
2. Open a browser.
3. Navigate to `127.0.0.1:8888`

![Web UI](images/web_ui.png)

## Next Steps

* Acquire some frames from the simulated adapter "detector".
* Set the frame processor to save the frames to a file.
* Open the file using the HDFView application (or equivalent).
* Try adjusting the debugging log level for the various applications.
