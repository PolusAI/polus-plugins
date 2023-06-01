"""Rolling Ball package entrypoint."""

import json
import logging
import typing
from multiprocessing import cpu_count
from os import environ
from pathlib import Path

import typer
from bfio.bfio import BioReader, BioWriter

from .rolling_ball import rolling_ball

print("DEBUGGING")

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
POLUS_LOG = getattr(logging, environ.get("POLUS_LOG", "INFO"))
logger = logging.getLogger("polus.plugins.transforms.images.rolling_ball")
logger.setLevel(POLUS_LOG)
logging.getLogger("bfio").setLevel(POLUS_LOG)

POLUS_IMG_EXT = environ.get("POLUS_IMG_EXT", ".ome.tif")

app = typer.Typer(help="Rolling Ball plugin")


@app.command()
def main(
    input_dir: Path = typer.Option(
        ...,
        "--inputDir",
        "-i",
        help="Input image collection to be processed by this plugin.",
    ),
    ball_radius: int = typer.Option(
        25,
        "--ballRadius",
        "-r",
        help="Radius of the ball used to perform background subtraction.",
    ),
    light_background: bool = typer.Option(
        False,
        "--lightBackground",
        "-l",
        help="Whether the image has a light or dark background.",
    ),
    output_dir: Path = typer.Option(
        ..., "--outputDir", "-o", help="Output collection."
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        "-p",
        help="Output a JSON preview of files generated by this tool.",
    ),
):
    """A WIPP plugin to perform background subtraction using the rolling-ball algorithm.

    Args:
    input_dir: path to directory containing the input images.
    ball_radius: radius of ball to use for the rolling-ball algorithm.
    light_background: whether the image has a light or dark background.
    output_dir: path to directory where to store the output images.
    preview: set to true to generate a preview of this outputs.
    """
    logger.info("Parsing arguments...")

    logger.info(f"inputDir = {input_dir}")

    logger.info(f"ballRadius = {ball_radius}")

    logger.info(f"lightBackground = {light_background}")

    logger.info(f"outputDir = {output_dir}")

    logger.info(f"preview = {preview}")

    if not input_dir.exists():
        raise ValueError("inputDir does not exist", input_dir)

    if not output_dir.exists():
        raise ValueError("outputDir does not exist", output_dir)

    if preview:
        generatePreview(input_dir, output_dir)
        return

    for in_path in input_dir.iterdir():
        if in_path.is_dir():
            logger.warning(f"{in_path} is a directory and will be ignored.")
            continue

        out_path = output_dir / in_path.name

        # Load the input image
        with BioReader(in_path) as reader:
            logger.info(f"Working on {in_path.name} with shape {reader.shape}")

            # Initialize the output image
            with BioWriter(
                out_path, metadata=reader.metadata, max_workers=cpu_count()
            ) as writer:
                rolling_ball(
                    reader=reader,
                    writer=writer,
                    ball_radius=ball_radius,
                    light_background=light_background,
                )


def generatePreview(input_dir: Path, output_dir: Path):
    preview: typing.Dict[str, typing.Union[typing.List, str]] = {
        "outputDir": [],
    }

    for in_path in input_dir.iterdir():
        if in_path.is_dir():
            logger.warning(f"{in_path} is a directory and will be ignored.")
            continue

        preview["outputDir"].append(in_path.name)

    with open(output_dir / "preview.json", "w") as fw:
        json.dump(preview, fw, indent=2)


if __name__ == "__main__":
    app()
