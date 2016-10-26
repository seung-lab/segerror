#!/usr/bin/env python
__doc__ = '''
Error Curve Between Segmentations (pyws vs label)

 This module computes the error metrics of error.py between
a watershed h5 file (as generated by spipe) and a comparison set of labels.
It derives the thresholded version of the dendrogram over a specified range,
and then finds the error for each thresholded segmentation.

Saves the curve of errors to disk under an HDF5 file specifying each score
'''


import argparse, timeit
import numpy as np
import io_utils, utils, data_prep


def main( ws_filename, label_filename, output_filename,

          thr_low, thr_high, thr_inc,

          calc_rfs=True, calc_re=True,
          calc_vifs=True, calc_vi=True,

          rel2d=False,
          foreground_restriction=False,
          split0=True ):


    print("Reading data...")
    ws_seg, dend_pairs, dend_values = io_utils.import_ws_file( ws_filename )
    label_seg = io_utils.import_file( label_filename )
    assert ws_seg.shape == label_seg.shape


    thresholds = np.arange(thr_low, thr_high, thr_inc)

    prep = utils.parse_fns( utils.prep_fns,
                            [rel2d, foreground_restriction] )
    ws_seg, label_seg = utils.run_preprocessing( ws_seg, label_seg, prep )


    om = utils.calc_overlap_matrix( ws_seg, label_seg, split0 )


    metrics = utils.parse_fns( utils.metric_fns,
                               [calc_rfs,calc_re,
                                calc_vifs,calc_vi] )

    results = init_results( metrics, len(thresholds) )
    #descending threshold to allow incremental merging
    for i in range(thresholds.size-1,-1,-1):
        t = thresholds[i]
        print("Threshold: {}".format(t))

        start = timeit.default_timer()
        om.merge_to_thr(dend_pairs, dend_values, t)
        end = timeit.default_timer()
        print("Mapping completed in {} seconds".format(end-start))

        for (name, fn) in metrics:
            (f,m,s) = fn(om, name)
            results["{}/Full".format(name)][i] = f
            results["{}/Merge".format(name)][i] = m
            results["{}/Split".format(name)][i] = s

    if len(results) > 0:
        results["Thresholds"] = thresholds
        io_utils.write_h5_map_file( results, output_filename )


def init_results( metrics, num_thresholds ):
    results = {}
    for (name, fn) in metrics:
        results["{}/Full".format(name)] = np.zeros((num_thresholds,))
        results["{}/Merge".format(name)] = np.zeros((num_thresholds,))
        results["{}/Split".format(name)] = np.zeros((num_thresholds,))

    return results


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
    	description=__doc__,
    	formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('ws_filename',
    	help="Filename of the watershed output")
    parser.add_argument('label_filename',
    	help='Filename of the labels for comparison- "ground truth" if available')
    parser.add_argument('output_filename',
        help='HDF5 filename for output curves')
    parser.add_argument('thr_low',nargs='?',
        type=float, default=0.0,
        help='Threshold lower-bound')
    parser.add_argument('thr_high',nargs='?',
        type=float, default=1.0,
        help='Threshold upper_bound')
    parser.add_argument('thr_inc',nargs='?',
        type=float, default=0.05,
        help='Threshold increment')

    #NOTE: "No" args store whether or not to calc the metric
    # the 'no' part of the flag is for command-line semantics
    parser.add_argument('-no_rfs','-no_rand_f_score',
    	default=False, action='store_true')
    parser.add_argument('-no_re','-no_rand_error',
    	default=False, action='store_true')
    parser.add_argument('-no_vifs','-no_variation_f_score',
    	default=False, action='store_true')
    parser.add_argument('-no_vi','-no_variation_information',
    	default=False, action='store_true')

    parser.add_argument('-rel2d','-2d_relabeling',
    	default=False, action="store_true")
    parser.add_argument('-no_fr','-no_foreground_restriction',
    	default=False, action='store_true')
    parser.add_argument('-no_split0','-dont_split_0_segment',
    	default=False, action='store_true')

    args = parser.parse_args()

    rfs     = not args.no_rfs
    re      = not args.no_re
    vi      = not args.no_vi
    vifs    = not args.no_vifs
    rel2d   =     args.rel2d
    fr      = not args.no_fr
    split0  = not args.no_split0

    main(args.ws_filename, args.label_filename,
         args.output_filename,

         args.thr_low, args.thr_high, args.thr_inc,

         rfs,re,vifs,vi,

         rel2d,fr, split0)
