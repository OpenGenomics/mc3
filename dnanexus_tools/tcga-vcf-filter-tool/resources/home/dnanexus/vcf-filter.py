#!/usr/bin/env python

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", action="store_true", default=False)
    parser.add_argument('input_vcf')
    parser.add_argument('filter_file')
    parser.add_argument('output_vcf')    
    args = parser.parse_args()

    allowed_seq = {}

    with open(args.filter_file) as handle:
        for line in handle:
            for elem in line.rstrip().split(","):
                allowed_seq[elem] = True

    with open(args.input_vcf) as ihandle:
        with open(args.output_vcf, "w") as ohandle:
            for line in ihandle:
                write = False
                if line.startswith("#"):
                    write = True
                else:
                    tmp = line.split("\t")
                    if tmp[0] in allowed_seq:
                        write = True
                    if args.filter:
                        if tmp[6] != 'PASS':
                            write = False
                    
                if write:
                    ohandle.write(line)
