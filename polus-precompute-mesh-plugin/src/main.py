import logging, argparse, time, multiprocessing, subprocess
from pathlib import Path
import os
import numpy as np


# Initialize the logger    
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')
logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

def main():
    # Setup the Argument parsing
    logger.info("Parsing arguments...")
    parser = argparse.ArgumentParser(prog='main', description='Generate a precomputed slice for Polus Volume Viewer.')

    parser.add_argument('--inpDir', dest='input_dir', type=str,
                        help='Path to folder with CZI files', required=True)
    parser.add_argument('--outDir', dest='output_dir', type=str,
                        help='The output directory for ome.tif files', required=True)

    # Parse the arguments
    args = parser.parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir

    logger.info('Input Directory = {}'.format(input_dir))
    logger.info('Output Directory = {}'.format(output_dir))
    

    # Get list of images that we are going to through
    logger.info('Getting the images...')
    images = [os.path.basename(i) for i in os.listdir(input_dir) if str(i).endswith(".ome.tif")]
    images.sort()

    # Set up lists for tracking processes
    processes = []
    process_timer = []
    pnum = 0
    
    # Build one pyramid for each image in the input directory
    # Each stack is built within its own process, with a maximum number of processes
    # equal to number of cpus - 1.
    stack_count = 1
    im_count = 1
    for image in images:
        output_image = os.path.join(output_dir, image)
        if not os.path.exists(output_image):
            os.makedirs(output_image, exist_ok=True)
        if len(processes) >= multiprocessing.cpu_count()-1 and len(processes)>0:
            free_process = -1
            while free_process<0:
                for process in range(len(processes)):
                    if processes[process].poll() is not None:
                        free_process = process
                        break
                time.sleep(3)
                
            pnum += 1
            logger.info("Finished Z stack process {} of {} in {}s!".format(pnum,len(images),time.time() - process_timer[free_process]))
            del processes[free_process]
            del process_timer[free_process]
        try:
            
            processes.append(subprocess.Popen("python3 generate_mesh.py --inpDir '{}' --outDir '{}'".format(input_dir,
                                                                                                            output_image),
                                                                                                            shell=True))
        except:
            raise Exception("Previous process in build-pyramid.py input is wrong")
            exit()
        im_count += 1
        process_timer.append(time.time())
        stack_count = stack_count + 1
    
    # Wait for all processes to finish
    while len(processes)>1:
        free_process = -1
        while free_process<0:
            for process in range(len(processes)):
                if processes[process].poll() is not None:
                    free_process = process
                    break
            time.sleep(3)
        pnum += 1
        logger.info("Finished stack process {} of {} in {}s!".format(pnum,len(images),time.time() - process_timer[free_process]))
        del processes[free_process]
        del process_timer[free_process]

    processes[0].wait()
    
    logger.info("Finished all processes!")

if __name__ == "__main__":
    main()
