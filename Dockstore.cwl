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
  dockerPull: quay.io/ucsc_cgl/dockstore-tool-gene-by-cell-creator:latest
- class: InlineJavascriptRequirement

hints:
- class: ResourceRequirement
  coresMin: 1
  ramMin: 1024
  outdirMin: 512000

inputs:
  input_directory:
    type: string
    inputBinding:
      position: 1
      prefix: --input_dir
    doc: The directory path which contains input tar.gz files, recursively searched

  rsem_gene:
    type: boolean
    inputBinding:
      position: 2
      prefix: --rsem_gene

  rsem_isoform:
    type: boolean
    inputBinding:
      position: 3
      prefix: --rsem_isoform

  kallisto_isoform:
    type: boolean
    inputBinding:
      position: 4
      prefix: --kallisto_isoform

outputs:
  output_file:
    type: File
    format: http://edamontology.org/data_3615
    outputBinding:
      glob: gene_by_cell.tar.gz
    doc: A text tsv file that contains the cell by gene matrices.

baseCommand: ["/bin/create_gene_by_cell.py"]
