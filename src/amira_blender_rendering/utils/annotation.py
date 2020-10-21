#!/usr/bin/env python

# Copyright (c) 2020 - for information on the respective copyright owner
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


class ObjectBookkeeper(object):
    """Tracks object classes (str), and instance count"""
    def __init__(self):
        self._book = dict()

    def add(self, object_class):
        if object_class in self._book:
            self._book[object_class]["instances"] += 1
        else:
            self._book[object_class] = dict(id=len(self._book), instances=1)

    def __getitem__(self, object_class):
        if object_class in self._book:
            return self._book[object_class]
        else:
            return dict(id=None, instances=None)

    def __str__(self):
        return self._book.__str__()

    def __len__(self):
        return len(self._book)
