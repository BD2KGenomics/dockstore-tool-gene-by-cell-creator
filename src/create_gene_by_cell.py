#!/usr/bin/env python
import os
import sys
import subprocess
import glob

class GeneByCellCreator:
    RSEM_GENE_LOC       = "RSEM/rsem_genes.results"
    RSEM_GENE_KEY       = "gene_id"
    RSEM_GENE_COUNT_KEY = "expected_count"

    RSEM_ISO_LOC        = "RSEM/rsem_isoforms.results"
    RSEM_ISO_KEY        = "transcript_id"
    RSEM_ISO_COUNT_KEY  = "expected_count"

    KALLISTO_ISO_LOC    = "Kallisto/abundance.tsv"
    KALLISTO_ISO_KEY    = "target_id"
    KALLISTO_ISO_COUNT_KEY = "est_counts"

    def __init__(self, input_directory =".", input_filetype =".tar.gz", output_directory=".",
                 rsem_gene = True, rsem_iso = True, kallisto_iso = True,
                 rsem_gene_outfile = "rsem_cell_by_gene.tsv", rsem_iso_outfile = "rsem_cell_by_isoform.tsv",
                 kallisto_iso_outfile = "kallisto_cell_by_isoform.tsv"):

        #directories
        self.input_directory = input_directory
        self.input_filetype = input_filetype if input_filetype.startswith(".") else ("." + input_filetype)
        self.output_directory = output_directory

        # what analysis to run
        self.get_rsem_gene = rsem_gene
        self.get_rsem_iso = rsem_iso
        self.get_kallisto_iso = kallisto_iso

        # names of output files
        self.rsem_gene_outfile = rsem_gene_outfile
        self.rsem_iso_outfile = rsem_iso_outfile
        self.kallisto_iso_outfile = kallisto_iso_outfile

        # all gene/isoform identifiers
        self.rsem_gene_ids = set()
        self.rsem_iso_ids = set()
        self.kallisto_iso_ids = set()

        # the actual uuid to count info
        self.rsem_gene_uuid_to_counts = dict()
        self.rsem_iso_uuid_to_counts = dict()
        self.kallisto_iso_uuid_to_counts = dict()


    def main(self):

        # sanity checks
        if not (self.get_rsem_gene or self.get_rsem_iso or self.get_kallisto_iso):
            raise Exception("Configured to collect no counts!")

        # extract all data
        uuid_to_file = self.get_uuid_to_file_location()
        # get counts for each uuid
        for uuid in uuid_to_file.keys():
            if self.get_rsem_gene:
                self.rsem_gene_uuid_to_counts[uuid] = self.get_rsem_gene_counts(uuid_to_file[uuid])
            if self.get_rsem_iso:
                self.rsem_iso_uuid_to_counts[uuid] = self.get_rsem_isoform_counts(uuid_to_file[uuid])
            if self.get_kallisto_iso:
                self.kallisto_iso_uuid_to_counts[uuid] = self.get_kallisto_isoform_counts(uuid_to_file[uuid])

        # write them out
        if self.get_rsem_gene:
            self.write_file_out(self.rsem_gene_uuid_to_counts, self.rsem_gene_ids,
                                os.path.join(self.output_directory, self.rsem_gene_outfile))
        if self.get_rsem_iso:
            self.write_file_out(self.rsem_iso_uuid_to_counts, self.rsem_iso_ids,
                                os.path.join(self.output_directory, self.rsem_iso_outfile))
        if self.get_kallisto_iso:
            self.write_file_out(self.kallisto_iso_uuid_to_counts, self.kallisto_iso_ids,
                                os.path.join(self.output_directory, self.kallisto_iso_outfile))




    def get_uuid_to_file_location(self):
        # what we're returning
        uuid_to_file = dict()

        # get filepaths
        filepath_stringmatcher = os.path.join(self.input_directory, "*" + self.input_filetype)
        filepaths = glob.glob(filepath_stringmatcher)
        if len(filepaths) == 0:
            raise Exception ("Found no files matching: %s" % filepath_stringmatcher)

        for filepath in filepaths:
            #untar
            subprocess.check_call(['tar', 'xvf', filepath], cwd=self.input_directory)
            #verify success
            expected_output_dir = filepath.rstrip(self.input_filetype)
            if not os.path.isdir(expected_output_dir):
                raise Exception("After untarring %s, expected output location was not found: %s" % (filepath, expected_output_dir))
            #get uuid
            uuid = os.path.basename(expected_output_dir)
            if uuid_to_file.has_key(uuid):
                raise Exception("UUID %s found twice" % uuid)
            #save and continue
            uuid_to_file[uuid] = expected_output_dir

        return uuid_to_file


    def get_rsem_gene_counts(self, filepath):
        # our return value
        gene_counts = dict()

        # file mgmnt
        rsem_gene_file = os.path.join(filepath, GeneByCellCreator.RSEM_GENE_LOC)
        if not os.path.isfile(rsem_gene_file):
            raise Exception("RSEM Gene file not found: %s" % rsem_gene_file)

        # read it in
        gene_idx = None
        count_idx = None
        with open(rsem_gene_file, 'r') as f:
            for line in f:
                parts = line.split("\t")
                # get indices
                if gene_idx is None:
                    for i in range(0, len(parts)):
                        if parts[i] == GeneByCellCreator.RSEM_GENE_KEY: gene_idx = i
                        if parts[i] == GeneByCellCreator.RSEM_GENE_COUNT_KEY: count_idx = i
                    if gene_idx is None or count_idx is None:
                        raise Exception("Didn't find expected columns '%s', '%s' in %s" %
                                        (GeneByCellCreator.RSEM_GENE_KEY, GeneByCellCreator.RSEM_GENE_COUNT_KEY,
                                         rsem_gene_file))
                    continue

                # get values
                gene = parts[gene_idx]
                count = parts[count_idx]
                self.rsem_gene_ids.add(gene)
                if count != 0:
                    gene_counts[gene] = count

        # return our counts
        return gene_counts

    def get_rsem_isoform_counts(self, filepath):
        # our return value
        isoform_counts = dict()

        # file mgmnt
        rsem_isoform_file = os.path.join(filepath, GeneByCellCreator.RSEM_ISO_LOC)
        if not os.path.isfile(rsem_isoform_file):
            raise Exception("RSEM Isoform file not found: %s" % rsem_isoform_file)

        # read it in
        isoform_idx = None
        count_idx = None
        with open(rsem_isoform_file, 'r') as f:
            for line in f:
                parts = line.split("\t")
                # get indices
                if isoform_idx is None:
                    for i in range(0, len(parts)):
                        if parts[i] == GeneByCellCreator.RSEM_ISO_KEY: isoform_idx = i
                        if parts[i] == GeneByCellCreator.RSEM_ISO_COUNT_KEY: count_idx = i
                    if isoform_idx is None or count_idx is None:
                        raise Exception("Didn't find expected columns '%s', '%s' in %s" %
                                        (GeneByCellCreator.RSEM_ISO_KEY, GeneByCellCreator.RSEM_ISO_COUNT_KEY,
                                         rsem_isoform_file))
                    continue

                # get values
                isoform = parts[isoform_idx]
                count = parts[count_idx]
                self.rsem_iso_ids.add(isoform)
                if count != 0:
                    isoform_counts[isoform] = count

        # return our counts
        return isoform_counts



    def get_kallisto_isoform_counts(self, filepath):
        # our return value
        isoform_counts = dict()

        # file mgmnt
        kallisto_isoform_file = os.path.join(filepath, GeneByCellCreator.KALLISTO_ISO_LOC)
        if not os.path.isfile(kallisto_isoform_file):
            raise Exception("Kallisto Isoform file not found: %s" % kallisto_isoform_file)

        # read it in
        isoform_idx = None
        count_idx = None
        with open(kallisto_isoform_file, 'r') as f:
            for line in f:
                parts = line.split("\t")
                # get indices
                if isoform_idx is None:
                    for i in range(0, len(parts)):
                        if parts[i] == GeneByCellCreator.KALLISTO_ISO_KEY: isoform_idx = i
                        if parts[i] == GeneByCellCreator.KALLISTO_ISO_COUNT_KEY: count_idx = i
                    if isoform_idx is None or count_idx is None:
                        raise Exception("Didn't find expected columns '%s', '%s' in %s" %
                                        (GeneByCellCreator.KALLISTO_ISO_KEY, GeneByCellCreator.KALLISTO_ISO_COUNT_KEY,
                                         kallisto_isoform_file))
                    continue

                # get values
                isoform = parts[isoform_idx]
                count = parts[count_idx]
                self.kallisto_iso_ids.add(isoform)
                if count != 0:
                    isoform_counts[isoform] = count

        # return our counts
        return isoform_counts

    def write_file_out(self, uuid_to_counts, count_identifiers, output_file_name):
        # sorting identifiers
        uuids = list(uuid_to_counts.keys())
        count_identifiers = list(count_identifiers)
        uuids.sort()
        count_identifiers.sort()

        with open(output_file_name, 'w') as f:
            # header
            f.write("sample")
            for ident in count_identifiers:
                f.write("\t%s" % ident)
            f.write("\n")

            # samples
            for uuid in uuids:
                counts = uuid_to_counts[uuid]
                f.write(uuid)
                for ident in count_identifiers:
                    val = 0.0
                    if counts.has_key(ident):
                        val = counts[ident]
                    f.write("\t%s" % val)
                f.write("\n")







if __name__ == "__main__":
    GeneByCellCreator().main()