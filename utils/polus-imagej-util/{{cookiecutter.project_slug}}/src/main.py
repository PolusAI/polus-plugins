'''
This file is autogenerated from an ImageJ plugin generation pipeline.
'''

from bfio.bfio import BioReader, BioWriter
import argparse
import logging
import os
import numpy as np
from pathlib import Path
import ij_converter
import jpype, imagej, scyjava
import typing

# Initialize the logger
# logging.basicConfig(format='%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s',
#                     datefmt='%d-%b-%y %H:%M:%S')

# Import environment variables
POLUS_LOG = getattr(logging,os.environ.get('POLUS_LOG','INFO'))
POLUS_EXT = os.environ.get('POLUS_EXT','.ome.tif')

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

def main({#- Required inputs -#}
         {% for inp,val in cookiecutter._inputs.items() -%}
         {%     if val.required -%}
         {%         if val.type=="boolean" -%}
         _{{ inp }}: bool,
         {%         elif val.type=="collection" -%}
         _{{ inp }}: Path,
         {%         else -%}
         _{{ inp }}: str,
         {%         endif -%}
         {%     endif -%}
         {% endfor -%}
         {#- Required Outputs (all outputs are required, and should be a Path) -#}
         {% for inp,val in cookiecutter._outputs.items() -%}
         _{{ inp }}: Path,
         {% endfor -%}
         {#- Optional inputs -#}
         {% for inp,val in cookiecutter._inputs.items() -%}
         {%     if not val.required -%}
         {%         if val.type=="boolean" -%}
         _{{ inp }}: typing.Optional[bool] = None,
         {%         elif val.type=="collection" -%}
         _{{ inp }}: typing.Options[Path] = None,
         {%         else -%}
         _{{ inp }}: typing.Optional[str] = None,
         {%         endif -%}
         {%     endif -%}
         {% endfor -%}) -> None:
             
    """ Initialize ImageJ """ 
    # Bioformats throws a debug message, disable the loci debugger to mute it
    def disable_loci_logs():
        DebugTools = scyjava.jimport("loci.common.DebugTools")
        DebugTools.setRootLevel("WARN")
    scyjava.when_jvm_starts(disable_loci_logs)
    
    # This is the version of ImageJ pre-downloaded into the docker container
    logger.info('Starting ImageJ...')
    ij = imagej.init("sc.fiji:fiji:2.1.1+net.imagej:imagej-legacy:0.37.4",
                     headless=True)
    #ij_converter.ij = ij
    logger.info('Loaded ImageJ version: {}'.format(ij.getVersion()))
    
    """ Validate and organize the inputs """
    args = []
    argument_types = []
    arg_len = 0

    {% for inp,val in cookiecutter._inputs.items() %}
    # Validate {{ inp }}{% if inp != "opName" %}
    {{ inp }}_types = { {% for i,v in val.call_types.items() %}
        "{{ i }}": "{{ v }}",{% endfor %}
    }
    
    # Check that all inputs are specified 
    if _{{ inp }} is None and _opName in list({{ inp }}_types.keys()):
        raise ValueError('{} must be defined to run {}.'.format('{{ inp }}',_opName))
    {%- if val.type == "collection"%}
    elif _{{ inp }} != None:
        {{ inp }}_type = {{ inp }}_types[_opName]
    
        # switch to images folder if present
        if _{{ inp }}.joinpath('images').is_dir():
            _{{ inp }} = _{{ inp }}.joinpath('images').absolute()

        args.append([f for f in _{{ inp }}.iterdir() if f.is_file()])
        arg_len = len(args[-1])
    else:
        argument_types.append(None)
        args.append([None])
    {%- else %}
    else:
        {{ inp }} = None
    {%- endif %}
    {% else %}
    {{ inp }}_values = [{% for v in val.options %}
        "{{v}}",{% endfor %}
    ]
    assert _{{ inp }} in {{ inp }}_values, '{{ inp }} must be one of {}'.format({{ inp }}_values)
    {% endif %}{%- endfor %}
    for i in range(len(args)):
        if len(args[i]) == 1:
            args[i] = args[i] * arg_len
            
    """ Set up the output """
    {%- for out,val in cookiecutter._outputs.items() %}
    {{ out }}_types = { {% for i,v in val.call_types.items() %}
        "{{ i }}": "{{ v }}",{% endfor %}
    }
    {%- endfor %}

    """ Run the plugin """
    try:
        for ind, (
            {%- for inp,val in cookiecutter._inputs.items() -%}
            {%- if val.type=='collection' %}{{ inp }}_path,{% endif -%}
            {%- endfor %}) in enumerate(zip(*args)):
            
            {%- for inp,val in cookiecutter._inputs.items() if val.type=='collection' %}
            {%- if val.type=='collection' %}
            if {{ inp }}_path != None:

                # Load the first plane of image in {{ inp }} collection
                logger.info('Processing image: {}'.format({{ inp }}_path))
                {{ inp }}_br = BioReader({{ inp }}_path)
                
                # Convert to appropriate numpy array
                {{ inp }} = ij_converter.to_java(ij, np.squeeze({{ inp }}_br[:,:,0:1,0,0]),{{ inp }}_type)
                {%- if loop.first %}
                metadata = {{ inp }}_br.metadata
                fname = {{ inp }}_path.name
                dtype = ij.py.dtype({{ inp }})
            {%- endif %}
            {%- endif %}{% endfor %}

            {%- for inp,val in cookiecutter._inputs.items() if val.type!='collection' and inp!='opName' %}
            if _{{ inp }} is not None:
                {{ inp }} = ij_converter.to_java(ij, _{{ inp }},{{ inp }}_types[_opName],dtype)
            {% endfor %}
            logger.info('Running op...')
            {% for i,v in cookiecutter.plugin_namespace.items() %}
            {%- if loop.first %}if{% else %}elif{% endif %} _opName == "{{ i }}":
                {{ v }}
            {% endfor %}
            logger.info('Completed op!')
            
            {%- for inp,val in cookiecutter._inputs.items() %}
            {%- if val.type=='collection' %}
            if {{ inp }}_path != None:
                {{ inp }}_br.close()
            {%- endif %}{% endfor %}
            
            {% for out,val in cookiecutter._outputs.items() -%}

            # Saving output file to {{ out }}
            logger.info('Saving...')
            {{ out }}_array = ij_converter.from_java(ij, {{ out }},{{ out }}_types[_opName])
            bw = BioWriter(_{{ out }}.joinpath(fname),metadata=metadata)
            bw.Z = 1
            bw.dtype = {{ out }}_array.dtype
            bw[:] = {{ out }}_array.astype(bw.dtype)
            bw.close()
            {%- endfor %}
            
    except:
        logger.error('There was an error, shutting down jvm before raising...')
        raise
            
    finally:
        # Exit the program
        logger.info('Shutting down jvm...')
        del ij
        jpype.shutdownJVM()
        logger.info('Complete!')

if __name__=="__main__":

    ''' Setup Command Line Arguments '''
    logger.info("Parsing arguments...")
    parser = argparse.ArgumentParser(prog='main', description='{{ cookiecutter.project_short_description }}')
    
    # Add command-line argument for each of the input arguments
    {% for inp,val in cookiecutter._inputs.items() -%}
    parser.add_argument('--{{ inp }}', dest='{{ inp }}', type=str,
                        help='{{ val.description }}', required={{ val.required }})
    {% endfor %}
    # Add command-line argument for each of the output arguments
    {%- for out,val in cookiecutter._outputs.items() %}
    parser.add_argument('--{{ out }}', dest='{{ out }}', type=str,
                        help='{{ val.description }}', required=True)
    {% endfor %}
    """ Parse the arguments """
    args = parser.parse_args()
    
    # Input Args
    {%- for inp,val in cookiecutter._inputs.items() %}
    {% if val.type=="boolean" -%}
    _{{ inp }} = args.{{ inp }} == 'true'
    {% elif val.type=="collection" -%}
    _{{ inp }} = Path(args.{{ inp }})
    {% else -%}
    _{{ inp }} = args.{{ inp }}
    {% endif -%}
    logger.info('{{ inp }} = {}'.format(_{{ inp }}))
    {% endfor %}
    # Output Args
    {%- for out,val in cookiecutter._outputs.items() %}
    _{{ out }} = Path(args.{{ out }})
    logger.info('{{ out }} = {}'.format(_{{ out }}))
    {%- endfor %}
    
    main(
    {%- filter indent(5) %}
    {%- for inp,val in cookiecutter._inputs.items() -%}
    _{{ inp }}=_{{ inp }},
    {% endfor -%}
    {%- for inp,val in cookiecutter._outputs.items() -%}
    _{{ inp }}=_{{ inp }}{% if not loop.last %},{% endif %}{% endfor %}{% endfilter -%}
    )