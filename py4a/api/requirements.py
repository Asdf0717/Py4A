"""Utilities for handling dependencies across different packages"""

import os
import logging


from typing import List
from wheel_inspect import inspect_wheel


logger = logging.getLogger(__name__)


class Requirements(object):
    def __init__(self, name: str, version: str, wheel_path: str):
        self.name: str = name
        self.version: str = version
        self.wheel_file: str = os.path.basename(wheel_path)
        self._get_dependencies(wheel_path)

    def __str__(self) -> str:
        return f"{self.name} {self.version}:\n" + "\n".join(
            str(req.to_dict()) for req in self.require_deps
        )

    def __repr__(self) -> str:
        return str(self)

    def _get_dependencies(self, wheel_path: str):
        self.require_python: str = ""
        self.require_deps: List[Requirement] = []
        try:
            metadata = inspect_wheel(wheel_path)["dist_info"]["metadata"]
            if "requires_python" in metadata:
                self.require_python = metadata["requires_python"]
            if "requires_dist" in metadata:
                for obj in metadata["requires_dist"]:
                    self.require_deps.append(
                        Requirement(
                            obj["name"],
                            obj["specifier"],
                            obj["marker"],
                            obj["url"],
                            obj["extras"],
                        )
                    )
        except Exception as ex:
            logger.error(f"{self.name}-{self.version} has ill-formed wheel: {ex}")


class Requirement(object):
    def __init__(self, name: str, specifier: str, marker: str, url: str, extras: list):
        self.name: str = name
        self.specifier: str = specifier
        self.marker: str = marker
        self.url: str = url
        self.extras: list = extras

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "specifier": self.specifier,
            "marker": self.marker,
            "url": self.url,
            "extras": self.extras,
        }
