#!/usr/bin/python

import csv
import json

with open('HCA_tar_gz_download_manifest.tsv','rb') as tsvin, open('new.csv', 'wb') as csvout:
    tsvin = csv.reader(tsvin, delimiter='\t')
    csvout = csv.writer(csvout)


    input_array = []

    first_line = True
    for row in tsvin:
        if first_line:
            first_line = False
            continue

        file_name = row[16]
        file_uuid = row[17]
        bundle_uuid = row[18]

        input_key_value = {}
        input_key_value["class"] = "File"
        input_key_value["path"] = "redwood://walt-hca.ucsc-cgl.org/" + bundle_uuid + "/" + file_uuid + "/" + file_name
 
        input_array.append(input_key_value)

    input_dict = {}
    input_dict["my_test"] = input_array
    input_dict["input_directory"] = "/datastore"
    input_dict["rsem_gene"] = 'true'
    input_dict["rsem_isoform"] = 'true'
    input_dict["kallisto_isoform"] = 'true'
   
    output_dict = {}
    output_dict["class"] = "File"
    output_dict["path"] = "/tmp/gene_by_cell.tar.gz"

    input_dict["output_file"] = output_dict


    print json.dumps(input_dict, indent=4, sort_keys=True) 
