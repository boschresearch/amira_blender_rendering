#!/usr/bin/env python

# Copyright (c) 2016 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

