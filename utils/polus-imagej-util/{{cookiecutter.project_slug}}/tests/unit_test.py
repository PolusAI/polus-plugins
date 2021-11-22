import argparse
import logging
import unittest
import os
import shutil
import sys
import traceback
import numpy as np
from pathlib import Path
from bfio.bfio import BioWriter

"""
This file is autogenerated from an ImageJ plugin generation pipeline. 
It is not intended to be run directly. Run imagej-testing/shell_test.py to begin testing.
"""

# Get plugin directory
plugin_dir = Path(__file__).parents[1]
sys.path.append(str(plugin_dir))

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> origin/imagej-util-clean
# Get src directory
src_path = plugin_dir.joinpath('src')
sys.path.append(str(src_path))

<<<<<<< HEAD
=======
>>>>>>> 32c0d333bfa71d6311e616bb15d50a6e35b64c8c
=======
>>>>>>> origin/imagej-util-clean
from src.main import main


class UnitTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        # Set up logger for unit tests
        cls.logger = logging.getLogger(__name__)
        cls.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s:%(message)s')
        file_handler = logging.FileHandler('imagej-testing/unit-test.log')
        file_handler.setFormatter(formatter)
        cls.logger.addHandler(file_handler)
        
        # Set up new log for summary of passed and failed tests
        cls.summary = logging.getLogger('summary')
        cls.summary.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s:%(message)s')
        file_handler = logging.FileHandler('imagej-testing/test-summary.log')
        file_handler.setFormatter(formatter)
        cls.summary.addHandler(file_handler)
    
    def generate_data(self, input, wipp_type, imagej_type):
            
        numpy_types = {
            'double'     : np.float64,
            'float'      : np.float32,
            'long'       : np.int64, # np.int64 not supported by bfio
            'int'        : np.int32,
            'short'      : np.int16,
            'char'       : np.ubyte, # np.ubyte not supported by bfio
            'byte'       : np.int8,
            'boolean'    : np.bool_ # np.bool_ not supported by bfio
        }
        
        if wipp_type == None:
            return None
        
        # Determine if the input data type is a collection
        elif wipp_type == 'collection':
            
            if imagej_type == None:
                dtype = np.double
            
            elif imagej_type in numpy_types.keys():
                dtype = numpy_types[imagej_type]
        
            else:
                dtype = np.double
            
            # Create input and output path objects for the randomly generated image file
            input_path = Path(__file__).parent.joinpath('{}/random.ome.tif'.format(input))
            #self.outputPath = Path(__file__).parent.joinpath('output/random.ome.tif')
            
            # Check if "input" is a sub-directory of "tests"
            if input_path.parent.exists():
            
                # Remove the "input" sub-directory
                shutil.rmtree(input_path.parent)
                
            # Create input and output sub-directories in tests
            os.mkdir(input_path.parent)
            
            """Using auto generated images"""
            
            # Create a random image to be used for plugin testing
            infile = None
            outfile = None
            image_size = 2048
            image_shape = (image_size, image_size)
            random_image = np.random.randint(
                low = 0,
                high = 255,
                size = image_shape,
                dtype = np.uint16
            )

            array = dtype(random_image)
            
            # Create a BioWriter object to write the ramdomly generated image file to tests/input dir
            with BioWriter(input_path) as writer:
                writer.X = image_shape[0]
                writer.Y = image_shape[1]
                writer.dtype = array.dtype
                writer[:] = array[:]
                # Not neccessary: writer.close()
            
            
            """Using sample images"""
            # # TODO: use Imagej sample data for unit testing
            # # Get input source directory
            # test_path = Path(__file__)
            # input_path = test_path.with_name('input')

            # # Create input directory in plugin test directory path
            # input_path = Path(__file__).with_name(input)
            
            # # Check if the input path already exists as a a sub-directory of "tests"
            # if input_path.exists():
            
            #     # Remove the "input" sub-directory
            #     shutil.rmtree(input_path)
            
            # # Copy sample images to input folder
            # shutil.copytree(sample_dir, input_path)
            
            
            return input_path.parent
        
        elif wipp_type == 'array':
            # arr = np.random.rand(2048,2048)
            arr = '1,2'
            return arr
        
        elif wipp_type == 'number':
            number = np.random.randint(5)
            return number
        
        else:
            self.logger.info(
                'FAILURE: The data type, {}, of input, {}, is currently not supported\n'.format(wipp_type, input)
                )
            raise TypeError('The input data type is not currently supported')
    
    def output_handler(self, output, dtype):
        if dtype == 'collection':
            
            # Create output path object for the plugin output
            output_path = Path(__file__).with_name(output)
            
            # Check if output is a sub-directory of "tests" directory
            if output_path.exists():
            
                # Delete the "output" sub-directory
                shutil.rmtree(output_path)
                
            # Create output as sub-directory of tests
            os.mkdir(output_path)
            
            return output_path
            
    
    def test_plugin(self):
        
        projectName = '{{ cookiecutter.project_name }}'
        self.logger.info('Testing the op: {} with overloading option: {}'.format(projectName, op))
        
        method_call_types = {}
        
        supported_data_types = [
            'double',
            'float',
            'long',
            'int',
            'short',
            'char',
            'byte',
            'boolean',
        ]
        
        # Get WIPP and ImageJ data types
        {% for inp,val in cookiecutter._inputs.items() -%}
        {% if inp == 'opName' -%}
        _{{ inp }} = op
        {% else -%}
        _{{ inp }}_wipp_types = {{ val.wipp_type }}
        _{{ inp }}_imagej_types =  {{ val.call_types }}
        if _{{ inp }}_wipp_types.get(op, None) != 'collection':
            method_call_types.update({method:dtype for method,dtype in _{{ inp }}_imagej_types.items() \
                if dtype in supported_data_types})
        {% endif -%}
        {% endfor -%}
        
        # Generate data for the inputs
        {% for inp,val in cookiecutter._inputs.items() -%}
        {% if inp != 'opName' -%}
        _{{ inp }} = self.generate_data(
            '{{ inp }}',
            _{{ inp }}_wipp_types.get(op, None), 
            method_call_types.get(op, None)
            )
        {% endif -%}
        {% endfor -%}
        
        # Handle the op output
        {% for out,val in cookiecutter._outputs.items() -%}
        _{{ out }} = self.output_handler('{{ out }}', '{{ val.type }}')
        {% endfor -%}
        
        
        try:
        # Call the op
            main(
            {%- filter indent(5) %}
            {%- for inp,val in cookiecutter._inputs.items() -%}
            _{{ inp }}=_{{ inp }},
            {% endfor -%}
            {%- for out,val in cookiecutter._outputs.items() -%}
            _{{ out }}=_{{ out }}{% if not loop.last %},{% endif %}{% endfor %}{% endfilter -%}
            )
            self.logger.info('SUCCESS: op: {} with option {} was successful\n'.format(projectName, op))
            self.summary.info('1')
        except Exception:
            self.logger.info(
                'FAILURE: op: {} with option {} was NOT successful'.format(projectName, op)+'\n'+str(sys.exc_info())
                )
            self.logger.info(traceback.format_exc()+'\n')
            self.summary.info('0')
            
if __name__ == '__main__':
    
    # Instantiate a parser for command line arguments
    parser = argparse.ArgumentParser(prog='unit_test', description='Test imagej plugin')
    
    # Add command-line argument for each of the input arguments
    parser.add_argument('--opName', dest='opName', type=str,
                        help='Operation to test', required=True)
    

    """ Parse the arguments """
    args = parser.parse_args()
    
    # Input Args
    op = args.opName
    
    del sys.argv[1:]
    unittest.main()