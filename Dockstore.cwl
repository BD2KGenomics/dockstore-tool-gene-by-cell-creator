#!/usr/bin/env cwl-runner

class: CommandLineTool
id: GeneByCellCreator
label: Tool for generating Gene by Cell matrix from output of Toil RNASeq workflow
cwlVersion: v1.0

doc: |
  [![Docker Repository on Quay.io](https://quay.io/repository/briandoconnor/dockstore-tool-md5sum/status "Docker Repository on Quay.io")](https://quay.io/repository/briandoconnor/dockstore-tool-md5sum)
  [![Build Status](https://travis-ci.org/briandoconnor/dockstore-tool-md5sum.svg)](https://travis-ci.org/briandoconnor/dockstore-tool-md5sum)
  A tool for generating Gene by Cell matrix from output of Toil RNASeq workflow.

requirements:
- class: DockerRequirement
  dockerPull: quay.io/ucsc_cgl/dockstore-tool-gene-by-cell-creator:1.0.0
- class: InlineJavascriptRequirement

hints:
- class: ResourceRequirement
  # The command really requires very little resources.
  coresMin: 1
  ramMin: 1024
  outdirMin: 512000

# this should be a directory, but we need to pass this as a parameter to the tool
inputs:
  input_directory:
    type: Directory
    inputBinding:
      position: 1
    doc: The directory which contains (small) sample input

outputs:
  output_file:
    type: File
    format: http://edamontology.org/data_3671
    outputBinding:
      glob: gene_by_cell.tar.gz
    doc: A text file that contains a single line that is the md5sum of the input file.

baseCommand: [/bin/create_gene_by_cell.py]
