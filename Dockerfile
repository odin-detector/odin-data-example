FROM ghcr.io/odin-detector/odin-data-build:1.12.0 AS developer

FROM developer AS build

RUN python -m pip install opencv-python-headless

# Root of example-detector
COPY . /odin/example-detector

# C++
WORKDIR /odin/example-detector
RUN mkdir -p build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/odin -DODINDATA_ROOT_DIR=/odin ../cpp && \
    make -j8 VERBOSE=1 && \
    make install

# Python
WORKDIR /odin/example-detector/python
RUN python -m pip install .

FROM ghcr.io/odin-detector/odin-data-runtime:1.12.0 AS runtime

COPY --from=build /odin /odin
COPY --from=build /venv /venv
COPY deploy /odin/example-deploy

RUN rm -rf /odin/example-detector

ENV PATH=/odin/bin:/odin/venv/bin:$PATH

WORKDIR /odin

CMD ["sh", "-c", "cd /odin/example-deploy && zellij --layout ./layout.kdl"]
