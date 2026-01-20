#
# NOTE: THIS DOCKERFILE IS GENERATED VIA "apply-templates.sh"
#
# PLEASE DO NOT EDIT IT DIRECTLY.
#

FROM docker.io/valkey/valkey:9.0.0-trixie AS build

ARG SERVER_VERSION=9.0.0

RUN set -eux;   \
                \
    apt-get update;     \
    apt-get install -y --no-install-recommends  \
                        ca-certificates         \
                        build-essential         \
                        cmake                   \
                        git                     \
                        curl                    \
                        clang                   \
                        clangd                  \
                        g++                     \
                        libgtest-dev            \
                        ninja-build             \
                        libssl-dev              \
                        clang-tidy              \
                        clang-format            \
                        libsystemd-dev          \
                        pkg-config              \
                    ;\
    apt-get clean && rm -rf /var/lib/apt/lists/* ;

# Install Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y;
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /opt

# Clone repositories
RUN set -eux; \
    git clone --depth 1 --branch 1.0.2 https://github.com/valkey-io/valkey-json.git; \
    git clone --depth 1 --branch 1.0.0 https://github.com/valkey-io/valkey-bloom.git; \
    git clone --depth 1 --branch 1.0.2 https://github.com/valkey-io/valkey-search.git; \
    git clone --depth 1 --branch 1.0.0 https://github.com/valkey-io/valkey-ldap.git;

# Build JSON module
WORKDIR /opt/valkey-json
RUN set -eux; \
    ./build.sh --release

# Build Bloom module
WORKDIR /opt/valkey-bloom
RUN cargo build --all --all-targets --release;

# Build Search module
WORKDIR /opt/valkey-search
RUN set -eux; \
    ./build.sh

# Build LDAP module
WORKDIR /opt/valkey-ldap
RUN cargo build --all --all-targets --release;

FROM docker.io/valkey/valkey:9.0.0-trixie

# Module configuration arguments (can be overridden at build time or runtime)
# Example: docker build --build-arg SEARCH_MODULE_ARGS="use-coordinator yes" .
ARG SEARCH_MODULE_ARGS=""
ARG JSON_MODULE_ARGS=""
ARG BLOOM_MODULE_ARGS=""
ARG LDAP_MODULE_ARGS=""

# Make args available at runtime as ENV
ENV SEARCH_MODULE_ARGS=${SEARCH_MODULE_ARGS}
ENV JSON_MODULE_ARGS=${JSON_MODULE_ARGS}
ENV BLOOM_MODULE_ARGS=${BLOOM_MODULE_ARGS}
ENV LDAP_MODULE_ARGS=${LDAP_MODULE_ARGS}

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends python3; \
    apt-get clean && rm -rf /var/lib/apt/lists/*;

RUN mkdir -p /usr/lib/valkey;

# Copy built modules from the build stage
COPY --from=build /opt/valkey-json/build/src/libjson.so /usr/lib/valkey/libjson.so
COPY --from=build /opt/valkey-bloom/target/release/libvalkey_bloom.so /usr/lib/valkey/libvalkey_bloom.so
COPY --from=build /opt/valkey-search/.build-release/libsearch.so /usr/lib/valkey/libsearch.so
COPY --from=build /opt/valkey-ldap/target/release/libvalkey_ldap.so /usr/lib/valkey/libvalkey_ldap.so

# Copy Python entrypoint (Python 3 is already installed in base image)
COPY bundle-docker-entrypoint.py /usr/local/bin/bundle-docker-entrypoint
RUN chmod +x /usr/local/bin/bundle-docker-entrypoint

ENTRYPOINT ["bundle-docker-entrypoint"]

EXPOSE 6379
CMD ["valkey-server"]
