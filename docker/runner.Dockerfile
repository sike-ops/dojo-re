FROM debian:bookworm-slim

ARG ZIG_VERSION=0.13.0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        binutils \
        ca-certificates \
        curl \
        gcc \
        g++ \
        golang-go \
        rustc \
        cargo \
        xz-utils \
    && curl -fsSL "https://ziglang.org/download/${ZIG_VERSION}/zig-linux-x86_64-${ZIG_VERSION}.tar.xz" -o /tmp/zig.tar.xz \
    && mkdir -p /opt/zig \
    && tar -xJf /tmp/zig.tar.xz -C /opt/zig --strip-components=1 \
    && ln -s /opt/zig/zig /usr/local/bin/zig \
    && rm -rf /var/lib/apt/lists/* /tmp/zig.tar.xz

WORKDIR /work
