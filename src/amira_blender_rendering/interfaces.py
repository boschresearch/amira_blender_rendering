#!/usr/bin/env python

"""
This file contains classes and prototypes that are shared with amira_perception.
In particular, it specifies how rendering results should be stored.
"""

from amira_blender_rendering.datastructures import filter_state_keys, DynamicStruct
from amira_blender_rendering.math.geometry import rotation_matrix_to_quaternion

#
#
# NOTE: the functions and classes below were taken from amira_perception. Make
#       sure to keep in sync as long as we don't have a core library that is
#       restricted to such functionality
#
#


class ResultsCollection:
    """Base class to handle detection results and IO of results"""

    def __init__(self):
        """Class constructor"""
        self._list = list()

    def add_result(self, r):
        """add single result"""
        self._list.append(r)

    def add_results(self, res):
        """add results from a list"""
        for r in res:
            self.add_result(r)

    def get_results(self):
        return self._list

    def get_result(self, idx):
        return self._list[idx]

    def __iter__(self):
        for el in self._list:
            yield el

    def __len__(self):
        return len(self._list)

    def state_dict(self, retain_keys: list = None):
        """Make results serializable (for writing out). Filter result keys if desired.

        Opt Args:
            retain_keys([]): list of keys to retain when converting to state_dict
        """
        if retain_keys is None:
            retain_keys = []
        return [r.state_dict(retain_keys) for r in self]

    @staticmethod
    def create_annotations(fname: str, results, retain_keys: list = None, **kwargs):
        """Convert result into annotation as a list of dicts to be dumped

        Args:
            fname(.png): name of image where object are detected
            results: DetectionResult object
            retain_keys([]): list of keys to filer results

        Returns:
            annotations([dict]): list of dictionaries with annotated info
                for each detected object in the same frame
        """
        if retain_keys is None:
            retain_keys = []
        annotations = []
        for r in results:
            data = r.state_dict(retain_keys)
            # add file_name to identify corresponding frame
            data['file_name'] = fname

            if "mask_name" in kwargs:
                data["mask_name"] = kwargs["mask_name"]

            # convert numpy array to list, that it can be dumped as json
            for k, v in data.items():
                if isinstance(v, np.ndarray):
                    data[k] = v.tolist()

            annotations.append(data)
        return annotations

    @staticmethod
    def dump_to_json(fpath: str, fname: str, data):
        """Dump data to json

        Args:
            fpath: filepath (already expanded)
            fname: filename (.json)
            data: json serializable object
        """
        with open(expandpath(os.path.join(fpath, fname)), 'w') as f:
            json.dump(data, f)

    @staticmethod
    def load_from_json(fpath: str, fname: str):
        """Load data from fpath/fname

        Args:
            fpath: path to directory
            fname: filename (.json)

        Returns:
            json data converted dict
        """
        with open(expandpath(os.path.join(fpath, fname)), 'r') as f:
            data = json.load(f)
        return data

    @staticmethod
    def build_directory_info(base_path: str):
        """Build a dynamic struct with the directory configuration of a Results folder for RetinaNet.

        The base_path should be expanded and not contain global variables or
        other system dependent abbreviations.

        Args:
            base_path (str): path to the root directory of the dataset
        """
        # expand once again just to be sure
        base_path = expandpath(base_path)

        # initialize
        dir_info = DynamicStruct()
        dir_info.annotations = DynamicStruct()

        # setup all path related information
        dir_info.base_path = base_path
        dir_info.annotations.base_path = os.path.join(dir_info.base_path, 'Annotations')
        dir_info.annotations.detections = os.path.join(dir_info.annotations.base_path, 'Detections')
        dir_info.annotations.groundtruths = os.path.join(dir_info.annotations.base_path, 'Groundtruths')
        dir_info.images = os.path.join(dir_info.base_path, 'Images')

        return dir_info

    @staticmethod
    def create_directory_structure(dir_info: DynamicStruct):
        """Build information struct about the directory structure

        Paths contained in dir_info are expected to be already expanded. That is,
        it should not contain global variables or other system dependent
        abbreviations.

        Args:
            dir_info (DynamicStruct): directory information for the dataset. See
                `build_directory_info` for more information.
        Returns:
            bool: whether the directory structure already existed to be able to check for previous results
        """
        existing_results = True
        if os.path.exists(dir_info.base_path):
            if not os.path.isdir(dir_info.base_path):
                raise RuntimeError("Output path '{}' exists but is not a directory".format(dir_info.base_path))

        for dir in [dir_info.annotations.detections, dir_info.annotations.groundtruths, dir_info.images]:
            if not os.path.exists(dir):
                os.makedirs(dir)
                existing_results = False
        return existing_results

    def draw_bbox(self, image):
        """
        If result in self._list is BBoxDetection, draw correspoding box to given image
        """
        _red = (255, 0, 0)
        _green = (0, 255, 0)
        _yellow = (255, 255, 0)
        for r in self.get_results():
            if isinstance(r, BBoxDetectionResult):
                image = draw_bbox(
                    image,
                    r.score,
                    r.class_name,
                    r.bbox,
                    textcolor=_yellow if r.type == 'detection' else _red,
                    boxcolor=_green if r.type == 'detection' else _red)
        return image

    def draw_pose(self, image):
        """
        If result in self._list is PoseDetection, draw corresponding pose to given image
        """
        raise NotImplementedError



class PoseRenderResult:

    def __init__(self, model_name, model_id, object_name, object_id,
                 rgb_const, rgb_random, depth, mask,
                 T_int, T_ext, rotation, translation,
                 corners2d, corners3d, aabb, oobb,
                 dense_features=None,
                 mask_name=''):
        """Initialize struct to store the result of rendering synthetic data

        Args:
            model_name(str): name of rendered model (type of object)
            model_id(int): id for model name (if any). To distinguish among different models
            object_name(str): object specific name (instance name)
            object_id(int): object specific id (if any). To distinguish among different instances
            rgb_const: image with constant light position across generated samples
            rgb_random: image with a random light position
            depth: depth image
            mask: stencil that masks the object
            T_int: intrinsic camera transformation matrix
            T_ext: homogeneous transformation matrix
            rotation(np.array(3,3) or np.array(4): rotation embedded as 3x3 rotation matrix or (4,) quaternion (WXYZ).
                Internally, we store rotation as quaternion only.
            translation(np.array(3,)): translation vector
            corners2d: 2D bbox in image space (image space aligned, not object-oriented!.) (top-left, bottom-right)
            corners2d: object-oriented bbox projected to image space (first element is the centroid)
            aabb: axis aligned bounding box around object (this is in model-coordinates before model-world transform)
            oobb: object-oriented bounding box in 3D world coordinates (this is after view-rotation)
            *dense_features: optional dense feature representation of the surface
            *mask_name(str): optional mask name to indetify correct mask in multi object scenarios. Default: ''
        """
        self.model_name = model_name
        self.model_id = model_id
        self.object_name = object_name
        self.object_id = object_id
        self.rgb_const = rgb_const
        self.rgb_random = rgb_random
        self.depth = depth
        self.mask = mask
        self.dense_features = dense_features
        self.T_int = T_int
        self.T_ext = T_ext
        # internally convert matrix to quanternion WXYZ
        if rotation is None:
            q = None
        else:
            if rotation.shape == (3, 3):
                q = rotation_matrix_to_quaternion(rotation)
            else:
                q = rotation.flatten()
                if q.shape != (4,):
                    q = None
                    raise ValueError('Rotation must be either a (3,3) matrix or a (4,) quaternion (WXYZ)')
        self.q = q
        self.t = translation
        self.corners2d = corners2d
        self.corners3d = corners3d
        self.oobb = oobb
        self.aabb = aabb
        self.mask_name = mask_name

    def state_dict(self, retain_keys: list = None):
        data = {
            "model_name": self.model_name,
            "model_id": self.model_id,
            "object_name": self.object_name,
            "object_id": self.object_id,
            "mask_name": self.mask_name,
            "pose": {
                "q": self.q.tolist(),
                "t": self.t.tolist(),
            },
            "bbox": {
                "corners2d": self.corners2d.tolist(),
                "corners3d": self.corners3d.tolist(),
                "aabb": self.aabb.tolist(),
                "oobb": self.oobb.tolist(),
            }
        }
        return filter_state_keys(data, retain_keys)

