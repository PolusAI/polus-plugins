"""Ome Converter."""
import json
import logging
import os
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from typing import Any, Optional

import filepattern as fp
import typer
from tqdm import tqdm

from polus.plugins.formats.ome_converter.image_converter import image_converter

# Initialize the logger
logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger("polus.plugins.formats.ome_converter")


def main(
    inp_dir: pathlib.Path = typer.Option(
        ...,
        "--inpDir",
        help="Input generic data collection to be processed by this plugin",
    ),
    pattern: str = typer.Option(
        None, "--filePattern", help="A filepattern defining the images to be converted"
    ),
    file_extension: Optional[str] = typer.Option(
        None, "--fileExtension", help="Type of data conversion"
    ),
    out_dir: pathlib.Path = typer.Option(..., "--outDir", help="Output collection"),
    preview: Optional[bool] = typer.Option(
        False, "--preview", help="Output a JSON preview of files"
    ),
) -> None:
    """Convert bioformat supported image datatypes conversion to ome.tif or ome.zarr file format."""
    logger.info(f"inpDir = {inp_dir}")
    logger.info(f"outDir = {out_dir}")
    logger.info(f"filePattern = {pattern}")
    logger.info(f"fileExtension = {file_extension}")

    inp_dir = inp_dir.resolve()
    out_dir = out_dir.resolve()

    assert inp_dir.exists(), f"{inp_dir} doesnot exists!! Please check input path again"
    assert (
        out_dir.exists()
    ), f"{out_dir} doesnot exists!! Please check output path again"

    FILE_EXT = os.environ.get("POLUS_IMG_EXT", ".ome.tif")

    FILE_EXT = FILE_EXT if file_extension is None else file_extension

    numworkers = max(cpu_count(), 2)
    if pattern is None:
        pattern = ".*"

    fps = fp.FilePattern(inp_dir, pattern)

    numworkers = max(cpu_count(), 2)
    if preview:
        with open(pathlib.Path(out_dir, "preview.json"), "w") as jfile:
            out_json: dict[str, Any] = {
                "filepattern": pattern,
                "outDir": [],
            }
            for file in fps():
                out_name = str(file[1][0].name.split(".")[0]) + FILE_EXT
                out_json["outDir"].append(out_name)
            json.dump(out_json, jfile, indent=2)

    with ThreadPoolExecutor(max_workers=numworkers) as executor:
        threads = []
        for files in fps():
            threads.append(
                executor.submit(
                    image_converter, pathlib.Path(files[1][0]), FILE_EXT, out_dir
                )
            )
        for f in tqdm(
            as_completed(threads),
            desc=f"converting images to {FILE_EXT}",
            total=len(threads),
        ):
            f.result()


if __name__ == "__main__":
    typer.run(main)
