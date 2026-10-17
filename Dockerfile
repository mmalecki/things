# Headless environment for rendering the CadQuery and build123d designs.
#
#   docker build -t things .
#   docker run --rm -v "$PWD:/things" -w /things/cadquery things cq python tape-holder.py
#   docker run --rm -v "$PWD:/things" -w /things/build123d things b123d python picatinny-sling-point.py
FROM python:3.13-slim-bookworm

RUN apt update -y && apt upgrade -y
RUN apt install -y --no-install-recommends \
    ca-certificates git curl wget unzip zip xz-utils \
    ripgrep fd-find jq less file tree procps shellcheck \
    build-essential python3 python3-pip python3-venv \
    openssh-client netcat-openbsd gnupg uidmap slirp4netns iproute2 \
    dbus-bin libnotify-bin libsecret-tools \
    libgl1 libx11-6 \
    && ln -s /usr/bin/fdfind /usr/local/bin/fd

ARG UV_VERSION=latest
RUN if [ "$UV_VERSION" = latest ]; then uv_path=uv; else uv_path="uv/$UV_VERSION"; fi \
 && curl -fsSL "https://astral.sh/$uv_path/install.sh" \
  | env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh

RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
RUN apt-get install -y nodejs
RUN rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

ARG WORK_UID=1000
RUN groupadd work
RUN useradd --uid "$WORK_UID" -m work -g work

USER work:work
RUN npm config set prefix "$HOME/.npm"
RUN npm install -g @anthropic-ai/claude-code @opencode/cli @openai/codex
RUN npm install -g --ignore-scripts @earendil-works/pi-coding-agent
ENV PATH="/home/work/.npm/bin:$PATH"
ENTRYPOINT ["bash"]
