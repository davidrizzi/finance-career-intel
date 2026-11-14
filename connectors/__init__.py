"""Connector registry: source['ats'] -> connector module."""
from connectors import ashby, career_websites, greenhouse, lever, smartrecruiters, successfactors, workday
from connectors.other_ats import DETECT_ONLY, oracle, personio, recruitee, workable

REGISTRY = {m.NAME: m for m in (greenhouse, lever, ashby, smartrecruiters, workday, successfactors,
                                recruitee, personio, workable, oracle, career_websites)}


def get(name: str):
    return REGISTRY.get(name)


def supported() -> list[str]:
    return sorted(REGISTRY)


__all__ = ["REGISTRY", "DETECT_ONLY", "get", "supported"]
