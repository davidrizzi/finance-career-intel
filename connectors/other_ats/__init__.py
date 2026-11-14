"""Connectors for further applicant-tracking systems.

Working connectors: recruitee, personio, workable, oracle (Oracle Recruiting Cloud).
Detected-only (no public feed that can be read without breaking their terms or
a login wall): taleo, icims, avature, tal.net, umantis, refline and others.
Those are recorded in the source registry as 'unsupported' with a link for
manual checking; they are never reported as 'no vacancies'.
"""
from . import oracle, personio, recruitee, workable  # noqa: F401

DETECT_ONLY = {"taleo", "icims", "avature", "talnet", "umantis", "refline", "bamboohr", "jobvite",
               "teamtailor", "prospective", "softgarden", "dvinci", "cornerstone", "phenom", "eightfold"}
