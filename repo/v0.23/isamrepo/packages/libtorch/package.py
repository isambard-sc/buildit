# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
import os

from spack.package import *


class Libtorch(CMakePackage):
    """
    The core of pytorch does not depend on Python. A CMake-based
    build system compiles the C++ source code into a shared object, 
    libtorch.so.
    """

    homepage = "https://pytorch.org"
    git = "https://github.com/pytorch/pytorch"

    license("BSD-3-Clause")

    version("1.13.1", tag="v1.13.1",
            commit="49444c3e546bf240bed24a101e747422d1f8a0ee",
            submodules=True)

    variant("build_type", default="Release",
            description="CMake build type",
            values=("Debug", "Release"))

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    
    depends_on("python@:3.11")
    depends_on("py-pyyaml")
    depends_on("py-typing-extensions")
    depends_on("py-setuptools")
    
    patch(
        "https://github.com/facebookincubator/gloo/commit/4a5e339b764261d20fc409071dc7a8b8989aa195.patch?full_index=1",
        sha256="dc8b3a9bea4693f32d6850ea2ce6ce75e1778538bfba464b50efca92bac425e3",
        working_dir="third_party/gloo",
    )

    def cmake_args(self):
        args = [
            self.define("BUILD_SHARED_LIBS", "ON"),
            self.define("PYTHON_EXECUTABLE", which("python3")),
        ]

        return args

