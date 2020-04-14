#!/usr/bin/env python

import numpy as np

def boundingbox_from_mask(mask):
    """Compute the 2D bounding box from an object stencil mask.

    Args:
        mask: MxN mask with 0 everywhere except the object of interest.
    """
    assert len(mask.shape) == 2

    # flatten to two dimensions and extract first and last non-zero entry
    xs = np.sum(mask, axis=0)
    ys = np.sum(mask, axis=1)
    xs = np.nonzero(xs)
    ys = np.nonzero(ys)
    x = (np.min(xs), np.max(xs))
    y = (np.min(ys), np.max(ys))

    return np.array([[x[0], y[0]],
                     [x[1], y[1]]])

