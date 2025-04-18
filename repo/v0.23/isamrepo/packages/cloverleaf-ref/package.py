# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

from spack.package import *


class CloverleafRef(MakefilePackage):
    """Proxy Application. CloverLeaf_ref is a miniapp that solves the
    compressible Euler equations on a Cartesian grid,
    using an explicit, second-order accurate method.
    """

    homepage = "https://github.com/UK-MAC/CloverLeaf_ref"
    url = "https://github.com/UK-MAC/CloverLeaf_ref/archive/refs/tags/v1.3.tar.gz"
    git = "https://github.com/green-br/CloverLeaf_ref.git"

    maintainers("amd-toolchain-support")

    version("master", branch="spack")

    depends_on("c", type="build")  # generated
    depends_on("fortran", type="build")  # generated

    variant(
        "ieee", default=False, description="Build with IEEE754 compliant floating point operations"
    )
    variant("debug", default=False, description="Build with DEBUG flags")

    depends_on("mpi")

    parallel = False

    # Cloverleaf_ref Makefile contains some but not all required options for each compiler.
    # This package.py inserts what is needed for Intel, AOCC, and LLVM compilers.
    @property
    def build_targets(self):
        targets = ["--directory=./"]

        targets.append("MPI_COMPILER={0}".format(self.spec["mpi"].mpifc))
        targets.append("C_MPI_COMPILER={0}".format(self.spec["mpi"].mpicc))

        if self.spec.satisfies("+debug"):
            targets.append("DEBUG=1")
        if self.spec.satisfies("+ieee"):
            targets.append("IEEE=1")

        # Work around for bug in Makefiles for versions 1.3 and 1.1 (mis-defined as -openmp)
        if self.spec.satisfies("%intel"):
            targets.append("COMPILER=INTEL")
            targets.append("OMP_INTEL=-qopenmp")

        # Work around for missing AOCC compilers option in Makefiles for versions 1.3 and 1.1
        elif self.spec.satisfies("%aocc"):
            targets.append("COMPILER=AOCC")
            targets.append("OMP_AOCC=-fopenmp")

            if self.spec.satisfies("+ieee"):
                targets.append("I3E_AOCC=-ffp-model=precise")
                if self.spec.satisfies("%aocc@:4.0.0"):
                    targets.append("I3E_AOCC+=-Kieee")

            # logic for Debug build: no optimizatrion and debug symbols
            if self.spec.satisfies("+debug"):
                targets.append("FLAGS_AOCC=-O0 -g -Wall -Wextra -fsanitize=address")
                targets.append("CFLAGS_AOCC=-O0 -g -Wall -Wextra -fsanitize=address")
            else:
                targets.append("CFLAGS_AOCC=-O3 -fnt-store=aggressive")
                targets.append("FLAGS_AOCC=-O3 -fnt-store=aggressive")

        # Work around for missing CLANG entries in Makefiles for master branch (commit:0fdb917),
        # and for versions 1.3 and 1.1
        elif self.spec.satisfies("%clang"):
            targets.append("COMPILER=CLANG")
            targets.append("OMP_CLANG=-fopenmp")

            if self.spec.satisfies("+ieee"):
                targets.append("I3E_CLANG=-ffp-model=precise")

            # logic for Debug build: no optimizatrion and debug symbols
            if self.spec.satisfies("+debug"):
                targets.append("FLAGS_CLANG=-O0 -g")
                targets.append("CFLAGS_CLANG=-O0 -g")
            else:
                targets.append("FLAGS_CLANG=-O3")
                targets.append("CFLAGS_CLANG=-O3")

        elif self.spec.satisfies("%gcc"):
            targets.append("COMPILER=GNU")

        elif self.spec.satisfies("%cce"):
            if self.spec.satisfies("+ieee"):
                targets.append("I3E_CRAY=")

            targets.append("COMPILER=CRAY")
            targets.append("OMP_CRAY=-fopenmp")
            # logic for Debug build: no optimizatrion and debug symbols
            if self.spec.satisfies("+debug"):
                targets.append("FLAGS_CRAY=-O0 -g")
                targets.append("CFLAGS_CRAY=-O0 -g")
            else:
                targets.append("FLAGS_CRAY=-O3")
                targets.append("CFLAGS_CRAY=-O3")
       
        elif self.spec.satisfies("%nvhpc"):
            if self.spec.satisfies("+ieee"):
                targets.append("I3E_NVHPC=-Kieee")

            targets.append("COMPILER=NVHPC")
            targets.append("OMP_NVHPC=-mp")
            # logic for Debug build: no optimizatrion and debug symbols
            if self.spec.satisfies("+debug"):
                targets.append("FLAGS_NVHPC=-O0 -g")
                targets.append("CFLAGS_NVHPC=-O0 -g")
            else:
                targets.append("FLAGS_NVHPC=-O3")
                targets.append("CFLAGS_NVHPC=-O3")
        
        elif self.spec.satisfies("%arm"):
            if self.spec.satisfies("+ieee"):
                targets.append("I3E_ARM=")

            targets.append("COMPILER=ARM")
            targets.append("OMP_ARM=-fopenmp")
            # logic for Debug build: no optimizatrion and debug symbols
            if self.spec.satisfies("+debug"):
                targets.append("FLAGS_ARM=-O0 -g")
                targets.append("CFLAGS_ARM=-O0 -g")
            else:
                targets.append("FLAGS_ARM=-O3")
                targets.append("CFLAGS_ARM=-O3")


        elif self.spec.satisfies("%xl"):
            targets.append("COMPILER=XLF")

        return targets

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        mkdirp(prefix.doc.tests)

        install("./clover_leaf", prefix.bin)
        install("./clover.in", prefix.bin)
        install("./*.in", prefix.doc.tests)
        if os.path.exists("InputDecks"):
            install_tree("InputDecks", prefix.doc.tests)
