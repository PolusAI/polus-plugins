"""Provides the apply_flatfield module."""

import concurrent.futures
import logging
import operator
import pathlib
import sys
import typing

import bfio
import numpy
import tqdm
from filepattern import FilePattern

from . import utils

logger = logging.getLogger(__name__)
logger.setLevel(utils.POLUS_LOG)


def apply(  # noqa: PLR0913
    img_dir: pathlib.Path,
    img_pattern: str,
    ff_dir: pathlib.Path,
    ff_pattern: str,
    df_pattern: typing.Optional[str],
    out_dir: pathlib.Path,
) -> None:
    """Run batch-wise flatfield correction on the image collection."""
    img_fp = FilePattern(str(img_dir), img_pattern)
    img_variables = img_fp.get_variables()

    ff_fp = FilePattern(str(ff_dir), ff_pattern)
    ff_variables = ff_fp.get_variables()

    # check that ff_variables are a subset of img_variables
    if set(ff_variables) - set(img_variables):
        msg = (
            f"Flatfield variables are not a subset of image variables: "
            f"{ff_variables} - {img_variables}"
        )
        raise ValueError(msg)

    if (df_pattern is None) or (not df_pattern):
        df_fp = None
    else:
        df_fp = FilePattern(str(ff_dir), df_pattern)
        df_variables = df_fp.get_variables()
        if set(df_variables) != set(ff_variables):
            msg = (
                f"Flatfield and darkfield variables do not match: "
                f"{ff_variables} != {df_variables}"
            )
            raise ValueError(msg)

    for group, files in img_fp(group_by=ff_variables):
        img_paths = [p for _, [p] in files]
        variables = dict(group)

        ff_path: pathlib.Path = ff_fp.get_matching(**variables)[0][1][0]

        df_path = None if df_fp is None else df_fp.get_matching(**variables)[0][1][0]

        _unshade_images(img_paths, out_dir, ff_path, df_path)


def _unshade_images(
    img_paths: list[pathlib.Path],
    out_dir: pathlib.Path,
    ff_path: pathlib.Path,
    df_path: typing.Optional[pathlib.Path],
) -> None:
    """Remove the given flatfield components from all images and save outputs.

    Args:
        img_paths: list of paths to images to be processed
        out_dir: directory to save the corrected images
        ff_path: path to the flatfield image
        df_path: path to the darkfield image
    """
    with bfio.BioReader(ff_path, max_workers=2) as bf:
        ff_image = bf[:, :, :, 0, 0].squeeze()

    if df_path is not None:
        with bfio.BioReader(df_path, max_workers=2) as df:
            df_image = df[:, :, :, 0, 0].squeeze()
    else:
        df_image = None

    batch_indices = list(range(0, len(img_paths), 16))
    if batch_indices[-1] != len(img_paths):
        batch_indices.append(len(img_paths))

    for i_start, i_end in tqdm.tqdm(
        zip(batch_indices[:-1], batch_indices[1:]),
        total=len(batch_indices) - 1,
    ):
        _unshade_batch(
            img_paths[i_start:i_end],
            out_dir,
            ff_image,
            df_image,
        )


def _unshade_batch(
    batch_paths: list[pathlib.Path],
    out_dir: pathlib.Path,
    ff_image: numpy.ndarray,
    df_image: typing.Optional[numpy.ndarray] = None,
) -> None:
    """Apply flatfield correction to a batch of images.

    Args:
        batch_paths: list of paths to images to be processed
        out_dir: directory to save the corrected images
        ff_image: component to be used for flatfield correction
        df_image: component to be used for flatfield correction
    """
    # Load images
    images = []
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=utils.MAX_WORKERS,
    ) as load_executor:
        load_futures = []
        for i, inp_path in enumerate(batch_paths):
            load_futures.append(load_executor.submit(utils.load_img, inp_path, i))

        for lf in tqdm.tqdm(
            concurrent.futures.as_completed(load_futures),
            total=len(load_futures),
            desc="Loading batch",
        ):
            images.append(lf.result())

    images = [img for _, img in sorted(images, key=operator.itemgetter(0))]
    img_stack = numpy.stack(images, axis=0)

    # Apply flatfield correction
    if df_image is not None:
        img_stack -= df_image

    img_stack /= ff_image

    # Save outputs
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=utils.MAX_WORKERS,
    ) as save_executor:
        save_futures = []
        for inp_path, img in zip(batch_paths, img_stack):
            save_futures.append(
                save_executor.submit(utils.save_img, inp_path, img, out_dir),
            )

        for sf in tqdm.tqdm(
            concurrent.futures.as_completed(save_futures),
            total=len(save_futures),
            desc="Saving batch",
        ):
            sf.result()
