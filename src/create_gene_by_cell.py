#!/usr/bin/env python
import os
import argparse
import subprocess
import glob
import time

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

    INPUT_FILETYPE = ".tar.gz"

    def __init__(self, input_directory, output_directory, rsem_gene, rsem_iso, kallisto_iso,
                 rsem_gene_outfile, rsem_iso_outfile, kallisto_iso_outfile, tarball_outfile):

        #directories
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.samples_in_directories = True

        # what analysis to run
        self.get_rsem_gene = rsem_gene
        self.get_rsem_iso = rsem_iso
        self.get_kallisto_iso = kallisto_iso
        if not (self.get_rsem_gene or self.get_rsem_iso or self.get_kallisto_iso):
            #none of these were specified -> do all of them
            self.get_rsem_gene = True
            self.get_rsem_iso = True
            self.get_kallisto_iso = True

        # names of output files
        self.rsem_gene_outfile = rsem_gene_outfile
        self.rsem_iso_outfile = rsem_iso_outfile
        self.kallisto_iso_outfile = kallisto_iso_outfile
        self.tarball_outfile = tarball_outfile

        # all gene/isoform identifiers
        self.rsem_gene_ids = set()
        self.rsem_iso_ids = set()
        self.kallisto_iso_ids = set()

        # the actual uuid to count info
        self.rsem_gene_uuid_to_counts = dict()
        self.rsem_iso_uuid_to_counts = dict()
        self.kallisto_iso_uuid_to_counts = dict()


    def main(self):
        #reporting
        start = time.time()

        # extract all data
        uuid_to_file = self.get_uuid_to_file_location()

        # document what will be attempted
        action_string = ""
        if self.get_rsem_gene:
            action_string += "RSEM genes"
        if self.get_rsem_iso:
            if action_string != '': action_string += ", "
            action_string += "RSEM isoforms"
        if self.get_kallisto_iso:
            if action_string != '': action_string += ", "
            action_string += "Kallisto isoforms"
        print "Building Cell x Count matrices for %s" % action_string

        # tracking progress as it's happening
        idx = 0
        total = len(uuid_to_file)
        next_report_idx = int(total / (2**5)) + 1
        counts_start = time.time()

        # get counts for each uuid
        for uuid in uuid_to_file.keys():
            if self.get_rsem_gene:
                self.rsem_gene_uuid_to_counts[uuid] = self.get_rsem_gene_counts(uuid_to_file[uuid])
            if self.get_rsem_iso:
                self.rsem_iso_uuid_to_counts[uuid] = self.get_rsem_isoform_counts(uuid_to_file[uuid])
            if self.get_kallisto_iso:
                self.kallisto_iso_uuid_to_counts[uuid] = self.get_kallisto_isoform_counts(uuid_to_file[uuid])
            #report
            idx += 1
            if idx == next_report_idx:
                print "Handled %d / %d UUIDs in %d seconds" % (idx, total, time.time() - counts_start)
                next_report_idx *= 2

        # write them out
        output_files = list()
        if self.get_rsem_gene:
            rsem_gene_out = os.path.join(self.output_directory, self.rsem_gene_outfile)
            print "Writing RSEM gene file to %s" % rsem_gene_out
            self.write_file_out(self.rsem_gene_uuid_to_counts, self.rsem_gene_ids, rsem_gene_out)
            output_files.append(rsem_gene_out)
        if self.get_rsem_iso:
            rsem_iso_out = os.path.join(self.output_directory, self.rsem_iso_outfile)
            print "Writing RSEM iso file to %s" % rsem_iso_out
            self.write_file_out(self.rsem_iso_uuid_to_counts, self.rsem_iso_ids, rsem_iso_out)
            output_files.append(rsem_iso_out)
        if self.get_kallisto_iso:
            kallisto_iso_out = os.path.join(self.output_directory, self.kallisto_iso_outfile)
            print "Writing Kallisto iso file to %s" % kallisto_iso_out
            self.write_file_out(self.kallisto_iso_uuid_to_counts, self.kallisto_iso_ids, kallisto_iso_out)
            output_files.append(kallisto_iso_out)

        # tar all output
        tarball_out = os.path.join(self.output_directory, self.tarball_outfile)
        compression_args = ['tar', 'cvf', tarball_out]
        compression_args.extend(output_files)
        subprocess.check_call(compression_args)
        print "Output tarball: %s" % tarball_out

        print "Fin (%ds)." % (time.time() - start)




    def get_uuid_to_file_location(self):
        # what we're returning
        uuid_to_file = dict()

        # get filepaths
        if (self.samples_in_directories):
            filepath_stringmatcher = os.path.join(self.input_directory, "*", "*" + GeneByCellCreator.INPUT_FILETYPE)
        else:
            filepath_stringmatcher = os.path.join(self.input_directory, "*" + GeneByCellCreator.INPUT_FILETYPE)
        filepaths = glob.glob(filepath_stringmatcher)
        if len(filepaths) == 0:
            raise Exception ("Found no files matching: %s" % filepath_stringmatcher)

        # tracking progress as it's happening
        idx = 0
        total = len(filepaths)
        next_report_idx = int(total / (2**5)) + 1
        start = time.time()

        with open(os.devnull, 'w') as FNULL:
            for filepath in filepaths:
                #untar
                untar_location = os.path.dirname(filepath)
                subprocess.check_call(['tar', 'xvf', filepath, '-C', untar_location], stdout=FNULL)
                #verify success
                expected_output_dir = filepath.rstrip(GeneByCellCreator.INPUT_FILETYPE)
                if not os.path.isdir(expected_output_dir):
                    (base_path, dir_name) = os.path.split(expected_output_dir)
                    expected_output_dir = os.path.join(base_path, "FAIL."+dir_name)
                    if not os.path.isdir(expected_output_dir):
                        raise Exception("After untarring %s, expected output location was not found: %s" % (filepath, expected_output_dir))
                #get uuid
                uuid = os.path.basename(expected_output_dir)
                if uuid_to_file.has_key(uuid):
                    raise Exception("UUID %s found twice" % uuid)
                #save and continue
                uuid_to_file[uuid] = expected_output_dir
                # report
                idx += 1
                if idx == next_report_idx:
                    print "Untarred %d / %d files in %d seconds" % (idx, total, time.time() - start)
                    next_report_idx *= 2

        print "Untarred %d files" % len(filepaths)
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


def parse_arguments():

    parser = argparse.ArgumentParser("Creates Gene/Isoform by Cell matrix from output of Toil RNASeq workflow")

    # locations
    parser.add_argument('--output_dir', '-o', action='store', dest='output_directory', default=".",
                        help="Location for output")
    parser.add_argument('--input_dir', '-i', action='store', dest='input_directory', default=".",
                        help="Location where input files are stored")

    # what files to generate
    parser.add_argument('--rsem_gene', '-g', action='store_true', dest='rsem_gene', default=False,
                        help="output RSEM gene counts")
    parser.add_argument('--rsem_isoform', '-s', action='store_true', dest='rsem_iso', default=False,
                        help="output RSEM isoform counts")
    parser.add_argument('--kallisto_isoform', '-k', action='store_true', dest='kallisto_iso', default=False,
                        help="output Kallisto isoform counts")

    # file names
    parser.add_argument('--rsem_gene_filename', action='store', dest='rsem_gene_outfile', default="rsem_cell_by_gene.tsv",
                        help="Name of RSEM gene outputfile")
    parser.add_argument('--rsem_isoform_filename', action='store', dest='rsem_iso_outfile', default="rsem_cell_by_isoform.tsv",
                        help="Name of RSEM isoform outputfile")
    parser.add_argument('--kallisto_isoform_filename', action='store', dest='kallisto_iso_outfile', default="kallisto_cell_by_isoform.tsv",
                        help="Name of Kallisto isoform outputfile")
    parser.add_argument('--tarball_filename', action='store', dest='tarball_filename', default="gene_by_cell.tar.gz",
                        help="Name of output tarball")

    return parser.parse_args()






if __name__ == "__main__":
    args = parse_arguments()
    GeneByCellCreator(input_directory=args.input_directory, output_directory=args.output_directory,
                      rsem_gene=args.rsem_gene, rsem_iso=args.rsem_iso, kallisto_iso=args.kallisto_iso,
                      rsem_gene_outfile=args.rsem_gene_outfile, rsem_iso_outfile=args.rsem_iso_outfile,
                      kallisto_iso_outfile=args.kallisto_iso_outfile, tarball_outfile=args.tarball_filename).main()
