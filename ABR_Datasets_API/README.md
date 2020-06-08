AMIRA Blender Rendering (ABR)
============================

ABR is a rendering tool to create large scale photorealistic phisics-based images.
For an in-depth description refer to the corresponding README and the software documentations


ABR Datasets API
==================

A lean python package to handle datasets generated using ABR.

The principal functionalities provided are:
- data loading
- data visualization

The following public API is currently implemented:
- get_sample:  retrive dataset sample from index
- get_samples: retrive dataset samples from list of indexes
- get_images:  retrive rgb, depth and mask from sample at given index
- get_rgb:     retrive rgb image from sample at given index
- get_depth:   retrive depth info from sample at given index
- get_mask:    retrive composite seg. mask from sample at given index
- plot_images: plot rgb, depth and mask from sample at given index
- plot_rgb:    plot rgb image from sample at given index
- plot_depth:  plot depth from sample at given index
- plot_mask:   plot composite seg. mask from sample at given index
- print_info:  print dataset info (folder and sample structure)