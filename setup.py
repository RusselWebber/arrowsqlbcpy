#!/usr/bin/env python
# Heavily based on the pythonnet project's setup.py that does the same for dotnet builds

import distutils
import sys
import platform
from distutils.command.build import build as _build
from setuptools.command.develop import develop as _develop
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
from setuptools import Distribution
from setuptools import setup, Command

import os

# Disable SourceLink during the build until it can read repo-format v1, #1613
os.environ["EnableSourceControlManagerQueries"] = "false"


class DotnetLib:
    def __init__(self, name, path, **kwargs):
        self.name = name
        self.path = path
        self.args = kwargs


class publish_dotnet(Command):
    """Publish command for dotnet-cli based builds"""

    description = "Build DLLs with dotnet-cli"
    user_options = [
        ("dotnet-config=", None, "dotnet publish configuration"),
        ("runtime=", None, "dotnet runtime"),
        (
            "inplace",
            "i",
            "ignore build-lib and put compiled extensions into the source "
            + "directory alongside your pure Python modules",
        ),
    ]

    def initialize_options(self):
        self.dotnet_config = None
        self.build_lib = None
        self.runtime = None
        self.inplace = False

    def finalize_options(self):
        if self.dotnet_config is None:
            self.dotnet_config = "release"
        if self.runtime is None:
            self.runtime = runtime()

        build = self.distribution.get_command_obj("build")
        build.ensure_finalized()
        if self.inplace:
            self.build_lib = "./src"
        else:
            self.build_lib = build.build_lib

    def run(self):
        dotnet_modules = self.distribution.dotnet_libs

        for lib in dotnet_modules:
            output = os.path.join(
                os.path.abspath(self.build_lib), lib.args.pop("output")
            )
            rename = lib.args.pop("rename", {})
            lib.args.pop("runtime")

            opts = sum(
                [
                    ["--" + name.replace("_", "-"), value]
                    for name, value in lib.args.items()
                ],
                [],
            )

            opts.extend(["--configuration", self.dotnet_config])
            opts.extend(["--output", output])
            opts.extend(["-r", self.runtime])
            opts.extend(["--sc", ""])

            self.announce("Running dotnet publish...", level=distutils.log.INFO)
            self.spawn(["dotnet", "publish", lib.path] + opts)

            for k, v in rename.items():
                source = os.path.join(output, k)
                dest = os.path.join(output, v)

                if os.path.isfile(source):
                    try:
                        os.remove(dest)
                    except OSError:
                        pass

                    self.move_file(src=source, dst=dest, level=distutils.log.INFO)
                else:
                    self.warn(
                        "Can't find file to rename: {}, current dir: {}".format(
                            source, os.getcwd()
                        )
                    )


# Add publish_dotnet to the build tasks:
class build(_build):
    sub_commands = _build.sub_commands + [("publish_dotnet", None)]

class develop(_develop):
    def install_for_development(self):
        # Build extensions in-place
        self.reinitialize_command("publish_dotnet", inplace=1)
        self.run_command("publish_dotnet")

        return super().install_for_development()


class bdist_wheel(_bdist_wheel):
    def finalize_options(self):
        # Monkey patch bdist_wheel to think the package is not pure as we
        # include DLLs
        super().finalize_options()
        self.root_is_pure = False


# Monkey-patch Distribution s.t. it supports the dotnet_libs attribute
Distribution.dotnet_libs = None

cmdclass = {
    "build": build,
    "publish_dotnet": publish_dotnet,
    "develop": develop,
    "bdist_wheel": bdist_wheel,
}

# Determine host architecture and thus .Net runtime to target
def runtime():
    is_win = platform.system() == "Windows"
    is_mac = platform.system() == "Darwin"
    if is_win:
        return "win-x64"
    elif is_mac:
        return "osx-x64"
    else:
        return "linux-x64"


dotnet_libs = [
    DotnetLib(
        "arrowsqlbcpy",
        "src/lib/ArrowSqlBulkCopyNet.csproj",
        output="arrowsqlbcpy/lib",
        runtime=runtime(),
    )
]

setup(
    cmdclass=cmdclass,
    dotnet_libs=dotnet_libs,
)