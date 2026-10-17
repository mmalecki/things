# Headless environment for rendering the CadQuery and build123d designs.
#
#   docker build -t things .
#   docker run --rm -v "$PWD:/things" -w /things/cadquery things cq python tape-holder.py
#   docker run --rm -v "$PWD:/things" -w /things/build123d things b123d python picatinny-sling-point.py
FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /usr/local/bin/

# OpenCASCADE and VTK link against X11/OpenGL even when nothing is displayed.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libx11-6 \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# The two projects lock different OCP builds, so each gets its own venv.
COPY cadquery/pyproject.toml cadquery/uv.lock /opt/projects/cadquery/
COPY build123d/pyproject.toml build123d/uv.lock /opt/projects/build123d/
RUN UV_PROJECT_ENVIRONMENT=/opt/venvs/cadquery \
        uv sync --frozen --no-install-project --project /opt/projects/cadquery \
    && UV_PROJECT_ENVIRONMENT=/opt/venvs/build123d \
        uv sync --frozen --no-install-project --project /opt/projects/build123d \
    && uv cache clean

# `cq <cmd>` / `b123d <cmd>` run a command inside the respective venv.
RUN printf '#!/bin/sh\nPATH=/opt/venvs/cadquery/bin:$PATH exec "$@"\n' > /usr/local/bin/cq \
    && printf '#!/bin/sh\nPATH=/opt/venvs/build123d/bin:$PATH exec "$@"\n' > /usr/local/bin/b123d \
    && chmod +x /usr/local/bin/cq /usr/local/bin/b123d

COPY . /things
WORKDIR /things
