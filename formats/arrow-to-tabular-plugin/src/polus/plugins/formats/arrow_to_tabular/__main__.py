"""Arrow to Tabular."""
import json
import logging
import os
import pathlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from typing import Any, Optional

import filepattern as fp
import typer
from tqdm import tqdm

from polus.plugins.formats.arrow_to_tabular.arrow_to_tabular import arrow_to_tabular

# Set number of processors for scalability
max_workers = max(1, cpu_count() // 2)

# Initialize the logger
logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger("polus.plugins.formats.arrow_to_tabular")


def main(
    inp_dir: pathlib.Path = typer.Option(
        ...,
        "--inpDir",
        help="Path to the input data",
    ),
    file_format: str = typer.Option(
        None, "--fileFormat", help="Filepattern of desired tabular output file"
    ),
    out_dir: pathlib.Path = typer.Option(..., "--outDir", help="Output collection"),
    preview: Optional[bool] = typer.Option(
        False,
        "--preview",
        help="Output a JSON preview of outputs produced by this plugin",
    ),
) -> None:
    """Execute Main function."""
    logger.info(f"inpDir = {inp_dir}")
    logger.info(f"outDir = {out_dir}")
    logger.info(f"fileFormat = {file_format}")

    inp_dir = inp_dir.resolve()
    out_dir = out_dir.resolve()

    assert inp_dir.exists(), f"{inp_dir} doesnot exists!! Please check input path again"
    assert (
        out_dir.exists()
    ), f"{out_dir} doesnot exists!! Please check output path again"
    FILE_EXT = os.environ.get("POLUS_TAB_EXT", ".csv")
    FILE_EXT = FILE_EXT if file_format is None else file_format
    assert FILE_EXT in [
        ".csv",
        ".parquet",
    ], f"This tabular file format: {FILE_EXT} is not support supported by this plugin!! Choose either CSV or Parquet FileFormat"

    featherPattern = ".*.arrow"

    fps = fp.FilePattern(inp_dir, featherPattern)

    if preview:
        with open(pathlib.Path(out_dir, "preview.json"), "w") as jfile:
            out_json: dict[str, Any] = {
                "filepattern": featherPattern,
                "outDir": [],
            }
            for file in fps():
                out_name = str(file[1][0].stem) + FILE_EXT
                out_json["outDir"].append(out_name)
            json.dump(out_json, jfile, indent=2)

    with ProcessPoolExecutor(max_workers) as executor:
        processes = []
        for files in fps:
            file = files[1][0]
            processes.append(
                executor.submit(arrow_to_tabular, file, file_format, out_dir)
            )

        for process in tqdm(
            as_completed(processes), desc="Feather --> Tabular", total=len(processes)
        ):
            process.result()

    logger.info("Finished all processes!")


if __name__ == "__main__":
    typer.run(main)
