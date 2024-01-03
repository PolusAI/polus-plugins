"""Image dimension stacking package."""
import json
import logging
import warnings
from os import environ
from pathlib import Path
from typing import Any

import filepattern as fp
import polus.plugins.formats.image_dimension_stacking.dimension_stacking as st
import typer

warnings.filterwarnings("ignore")

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
POLUS_LOG = getattr(logging, environ.get("POLUS_LOG", "INFO"))
logger = logging.getLogger("polus.plugins.formats.image_dimension_stacking")
logger.setLevel(POLUS_LOG)
logging.getLogger("bfio").setLevel(POLUS_LOG)


app = typer.Typer(help="Stack multi dimensional image into single image.")


def generate_preview(out_dir: Path, file_pattern: str) -> None:
    """Generate preview of the plugin outputs."""
    with Path.open(Path(out_dir, "preview.json"), "w") as jfile:
        out_json: dict[str, Any] = {
            "filepattern": file_pattern,
            "outDir": [],
        }

        fps = fp.FilePattern(out_dir, file_pattern)
        out_name = fps.output_name()
        out_json["outDir"].append(out_name)
        json.dump(out_json, jfile, indent=2)


@app.command()
def main(
    inp_dir: Path = typer.Option(
        ...,
        "--inpDir",
        "-i",
        help="Path to input directory containing binary images.",
    ),
    file_pattern: str = typer.Option(
        ".*",
        "--filePattern",
        "-f",
        help="Filename pattern used to separate data.",
    ),
    group_by: str = typer.Option(
        ...,
        "--groupBy",
        "-g",
        help="Desired polygon type.",
    ),
    out_dir: Path = typer.Option(
        ...,
        "--outDir",
        "-o",
        help="Output collection.",
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        "-p",
        help="Generate preview of expected outputs.",
    ),
) -> None:
    """Image dimension stacking plugin."""
    logger.info(f"--inpDir: {inp_dir}")
    logger.info(f"--filePattern: {file_pattern}")
    logger.info(f"--groupBy: {group_by}")
    logger.info(f"--outDir: {out_dir}")

    if not inp_dir.exists():
        msg = "inpDir does not exist"
        raise ValueError(msg, inp_dir)

    if not out_dir.exists():
        msg = "outDir does not exist"
        raise ValueError(msg, out_dir)

    if group_by not in ["c", "t", "z"]:
        msg = "Dimensions are not properly defined, Select c, t or z"
        raise ValueError(msg)

    if len(group_by) != 1:
        msg = f"{group_by} Only one variable is selected for dimension stacking"
        raise ValueError(msg)

    if preview:
        generate_preview(out_dir=out_dir, file_pattern=file_pattern)

    st.dimension_stacking(
        inp_dir=inp_dir,
        file_pattern=file_pattern,
        group_by=group_by,
        out_dir=out_dir,
    )


if __name__ == "__main__":
    app()
