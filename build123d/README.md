# build123d designs

Install the environment from this directory:

```sh
uv sync --locked
uv run python molle_backplate.py
```

Fastener dimensions and native hole/nut-pocket primitives come from
[`bd-buildabolt`](https://github.com/mmalecki/bd-buildabolt). For now its source
is Git over SSH, pinned to a commit in `uv.lock`; syncing requires GitHub SSH
access. The CadQuery designs in `../cadquery/` have a separate environment.

## Regression checks

```sh
uv run python -m unittest discover -s tests -v
```

The checks run the migrated designs without connecting to OCP Viewer, write their
normal exports into a temporary directory, and validate the reimported STEP
solids and baseline volumes. They also compare the native fastener primitives
against the previous sketch/extrude geometry. Interactive runs continue to use
`ocp-vscode` as before.

`picatinny-sling-point.py` has a pre-existing failure at its first fillet with
the locked build123d 0.13 / OCP 8 versions. Its full-export test is marked as an
expected failure; a separate check validates the model through the fastener cuts,
before that fillet. The migration does not alter that finishing operation.

The pouch deliberately retains build123d's `CounterSinkHole`: its original
82-degree sink and head clearance cannot be represented by `bd-buildabolt`'s
fixed 90-degree `CounterSinkBoltHole` without changing the design.
