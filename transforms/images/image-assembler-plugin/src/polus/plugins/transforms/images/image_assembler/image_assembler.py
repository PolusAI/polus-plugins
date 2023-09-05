import filepattern as fp
from bfio import BioReader, BioWriter
import numpy as np
from math import ceil
from pathlib import Path
import logging
from time import perf_counter
from typing import Tuple, Optional
import re
from preadator import ProcessManager

# import concurrent.futures
# import multiprocessing
# import os

logging.basicConfig(
    format="%(name)-8s - %(levelname)-8s - %(message)s"
)
logger = logging.getLogger("image-assembler")
logger.setLevel(logging.DEBUG)

# this parameter controls disk writes. Seem to plateau after 8192
# TODO this should be benchmarked of more type of data, maybe made a param?
chunk_size = 1024 * 8
chunk_width, chunk_height = chunk_size, chunk_size

# UNUSED - PREADATOR USES ITS OWN HEURISTICS
# # TODO CHECK those heuristics would require further investigation.
# num_threads = (chunk_size // BioReader._TILE_SIZE) ** 2
# try:
#     num_processes = len(os.sched_getaffinity(0)) * 2
# except Exception:
#     num_processes = multiprocessing.cpu_count() * 2


def generate_output_filenames(
    img_path: Path,
    stitch_path: Path,
    output_path: Path,
    derive_name_from_vector_file: Optional[bool],
) -> None:
    """
    Generate the output filenames that would be created if the assembler was called.
    """
    output_filenames = []
    vector_patterns = collect_stitching_vector_patterns(stitch_path)
    for (vector_file, pattern) in vector_patterns:
        fovs = fp.FilePattern(vector_file, pattern)
        first_image_name = fovs[0][1][0]
        first_image = img_path / first_image_name
        output_image_path = derive_output_image_path(fovs, derive_name_from_vector_file, vector_file, first_image, output_path)
        output_filenames.append(output_image_path)
    return output_filenames


def assemble_images(
    img_path: Path,
    stitch_path: Path,
    output_path: Path,
    derive_name_from_vector_file: Optional[bool],
) -> None:
    """
    Assemble one or several images from a image directory and a directory of stitching vectors.
    """
    vector_patterns = collect_stitching_vector_patterns(stitch_path)
    # max_workers = min(len(vector_patterns), cpu_count())
    # with concurrent.futures.ProcessPoolExecutor( max_workers=1) as executor:
    ProcessManager.init_processes("main", "image-assembler")
    for (vector_file, pattern) in vector_patterns:
        # assemble_image(vector_file, pattern)
        ProcessManager.submit_process(assemble_image, vector_file, pattern, derive_name_from_vector_file, img_path, output_path)
    ProcessManager.join_processes()

def collect_stitching_vector_patterns(stitching_vector_path):
    """Collect all valid stitching vectors in the given directory.
    Returns a tuple containing the vector file and the inferred pattern for it.
    Invalid stitching vectors are ignored.
    """
    # find all files
    if(stitching_vector_path.is_dir()):
        files = [vector for vector in list(stitching_vector_path.iterdir()) if vector.is_file]
    else :
        files = [stitching_vector_path]

    stitching_vector_pattern : Tuple[Path, str] = [] 

    # make sure files are valid stitching vectors
    for v in files:
        try: 
            pattern = fp.infer_pattern(v)
            stitching_vector_pattern.append((v, pattern))
        except RuntimeError as e:
            logger.critical(f"this file cannot be parsed as a stitching vector and will be ignored : {v}")

    return stitching_vector_pattern


# TODO Remove possibility of deriving name from vector file?
# it ties us to a specific naming convention of ".*global-positions-([0-9]+).txt" for the stitching vector
def derive_output_image_path(fovs, derive_name_from_vector_file, vector_file, first_image, output_path):
    """
    Derive the name of the output image according to user specified preferences.
    It can be derived from the inferred pattern or from the pattern of the stiching vector.
    """
    # guess a name for the final assembled image
    output_name = fovs.output_name()

    if derive_name_from_vector_file:
        global_regex = ".*global-positions-([0-9]+).txt"
        match = re.match(global_regex, Path(vector_file).name).groups()[0]
        if(match):
            output_name = "".join([match] + Path(first_image).suffixes)

    output_image_path =  output_path / output_name
    ProcessManager.job_name(output_name)
    return output_image_path
    
def assemble_image(vector_file, pattern, derive_name_from_vector_file, img_path, output_path):
    """Assemble an image from fovs.
    vector_file : path to the stitching vector
    pattern : inferred pattern for this stitching vector
    """
    fovs = fp.FilePattern(vector_file, pattern)

    # let's figure out the size of a partial FOV.
    # Pick the first image in stitching vector.
    # We assume all images have the same size.
    first_image_name = fovs[0][1][0]
    first_image = img_path / first_image_name
    with BioReader(first_image) as br:
        full_image_metadata = br.metadata
        fov_width = br.x
        fov_height = br.y
        # stitching is only performed on the (x,y) plane
        # z_stack images would need to be align beforehand
        # TODO does it makes sense to consider z_stack images?
        # TODO examples?
        assert br.z == 1

    output_image_path = derive_output_image_path(fovs, derive_name_from_vector_file, vector_file, first_image, output_path)

    # compute final full image size (requires a full pass over the partial fovs)
    full_image_width, full_image_height = fov_width, fov_height
    for fov in fovs():
        metadata = fov[0]
        full_image_width = max(full_image_width, metadata['posX'] + fov_width)
        full_image_height = max(full_image_height, metadata['posY'] + fov_height)

    # divide our image into chunks that can be processed separately
    chunk_grid_col = ceil(full_image_width / chunk_width)
    chunk_grid_row = ceil(full_image_height / chunk_height)
    chunks = [[[] for _ in range(chunk_grid_col)] for _ in range(chunk_grid_row)]

    # figure out regions of fovs that needs to be copied into each chunk.
    # This is fast so it can be done beforehand in a single process.
    for fov in fovs():
        # we are parsing a stitching vector, so we are always getting unique records.        
        assert(len(fov[1]) == 1)
        filename = fov[1][0]

        # get global coordinates of fov in the final image
        metadata = fov[0]
        global_fov_start_x = metadata['posX']
        global_fov_start_y = metadata['posY']

        # check which chunks the fov overlaps
        chunk_col_min = global_fov_start_x // chunk_width
        chunk_col_max = (global_fov_start_x + fov_width) // chunk_width
        chunk_row_min = global_fov_start_y // chunk_height
        chunk_row_max = (global_fov_start_y + fov_height)  // chunk_height

        # define regions of fovs to copy to each chunk
        for row in range(chunk_row_min, chunk_row_max + 1):
            for col in range(chunk_col_min, chunk_col_max + 1):
                # global coordinates of the contribution
                global_start_x = max(global_fov_start_x, col * chunk_width)
                global_end_x = min(global_fov_start_x + fov_width, (col + 1) * chunk_width)
                global_start_y = max( global_fov_start_y, row * chunk_height)
                global_end_y = min(global_fov_start_y + fov_height, (row + 1) * chunk_height)

                # coordinates within the fov we will copy from
                fov_start_x = max(global_fov_start_x, col * chunk_width) - global_fov_start_x
                fov_start_y = max(global_fov_start_y, row * chunk_height) - global_fov_start_y

                # coordinates within the chunk we will copy to
                chunk_start_x = global_start_x - col * chunk_width
                chunk_start_y = global_start_y - row * chunk_height

                ## dimensions of the region to be copied
                region_width = global_end_x - global_start_x
                region_height = global_end_y - global_start_y

                region_to_copy = (
                        filename, 
                        (fov_start_x, fov_start_y),
                        (chunk_start_x, chunk_start_y),
                        (region_width, region_height)
                        )
                chunks[row][col].append(region_to_copy)

    # A single copy of of the writer is shared amongst all threads.
    with BioWriter(output_image_path, 
                   metadata=full_image_metadata, 
                   backend="python") as bw:
        bw.x =  full_image_width
        bw.y = full_image_height
        bw._CHUNK_SIZE = chunk_size

        # Copy each fov regions.
        # This requires multiple reads and copies and a final write.
        # This is a slow IObound process so it can benefit from multithreading
        # in order to overlap reads/writes.
        for row in range(chunk_grid_row):
            for col in range(chunk_grid_col):
                ProcessManager.submit_thread(assemble_chunk, row, col, chunks[row][col], bw, img_path)
        ProcessManager.join_threads()

def assemble_chunk(row, col, regions_to_copy, bw, img_path):
    """
    Assemble a chunk of data from all the fovs it overlaps with.
    We pass the BioWriter as an argument to the task because we cannot initialize 
    the process state with preadator.
    """
    # TODO we could allocate a smaller chunk on the edge of the image
    # as this is what BfioWriter expects
    # TODO remove if bfio supertile does this somehow
    chunk = np.zeros((chunk_width, chunk_height), bw.dtype)

    for region_to_copy in regions_to_copy:
        filepath = img_path / region_to_copy[0]
        (fov_start_x, fov_start_y) = region_to_copy[1]
        (chunk_start_x, chunk_start_y) = region_to_copy[2]
        (region_width, region_height) = region_to_copy[3]

        with BioReader(filepath) as br:
            # read data from region of fov
            data = br[fov_start_y: fov_start_y + region_height ,fov_start_x:fov_start_x + region_width]
            #copy data to chunk
            chunk[chunk_start_y:chunk_start_y + region_height, chunk_start_x:chunk_start_x + region_width] = data

    # completed chunk is written to disk
    # we only write what fits in the image since that the behavior bfio expects
    max_y = min((row + 1) * chunk_height, bw.y)
    max_x = min((col + 1) * chunk_width, bw.x)
    bw[row * chunk_height: max_y, col * chunk_width: max_x] = \
        chunk[0: max_y - row * chunk_height, 0: max_x - col * chunk_width]
