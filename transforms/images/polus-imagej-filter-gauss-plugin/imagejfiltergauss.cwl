class: CommandLineTool
cwlVersion: v1.2
inputs:
  inpDir:
    inputBinding:
      prefix: --inpDir
    type: Directory
  opName:
    inputBinding:
      prefix: --opName
    type: string
  outDir:
    inputBinding:
      prefix: --outDir
    type: Directory
  sigma:
    inputBinding:
      prefix: --sigma
    type: double?
  sigmas:
    inputBinding:
      prefix: --sigmas
    type: string?
outputs:
  outDir:
    outputBinding:
      glob: $(inputs.outDir.basename)
    type: Directory
requirements:
  DockerRequirement:
    dockerPull: polusai/imagej-filter-gauss-plugin:0.3.2
  InitialWorkDirRequirement:
    listing:
    - entry: $(inputs.outDir)
      writable: true
  InlineJavascriptRequirement: {}
