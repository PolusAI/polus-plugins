"""This file is autogenerated from an ImageJ plugin generation pipeline."""

import logging
import pathlib

import filepattern
import imagej
import scyjava
import tqdm
import typer
from polus.images.transforms.imagej_filter_correlate import POLUS_LOG
from polus.images.transforms.imagej_filter_correlate import filter_correlate

# Initialize the logger
logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger("main")
logger.setLevel(POLUS_LOG)

app = typer.Typer()


def disable_loci_logs() -> None:
    """Bioformats throws a debug message, disable the loci debugger to mute it."""
    debug_tools = scyjava.jimport("loci.common.DebugTools")
    debug_tools.setRootLevel("WARN")


# scyjava to configure the JVM
scyjava.config.add_option("-Xmx6g")
scyjava.when_jvm_starts(disable_loci_logs)


@app.command()
def main(
    inp_dir: pathlib.Path = typer.Option(
        ...,
        "--inpDir",
        help="Collection to be processed by this plugin",
        exists=True,
        file_okay=False,
        readable=True,
        resolve_path=True,
    ),
    pattern: str = typer.Option(
        ".*",
        "--pattern",
        help="Pattern to match the files in the collection",
    ),
    filter_path: pathlib.Path = typer.Option(
        ...,
        "--filterPath",
        help="Filter image",
        exists=True,
        file_okay=True,
        readable=True,
        resolve_path=True,
    ),
    out_dir: pathlib.Path = typer.Option(
        ...,
        "--outDir",
        help="Output collection",
        exists=True,
        file_okay=False,
        writable=True,
        resolve_path=True,
    ),
) -> None:
    """Run the Op."""
    logger.debug("Starting ImageJ...")
    ij = imagej.init(
        "sc.fiji:fiji:2.1.1+net.imagej:imagej-legacy:0.37.4",
        mode="headless",
    )
    logger.debug(f"Loaded ImageJ version: {ij.getVersion()}")

    fp = filepattern.FilePattern(inp_dir, pattern)
    files = []
    for _, fs in fp():
        files.extend(fs)

    for inp_path in tqdm.tqdm(files):
        filter_correlate(inp_path, filter_path, out_dir, ij)


if __name__ == "__main__":
    app()
