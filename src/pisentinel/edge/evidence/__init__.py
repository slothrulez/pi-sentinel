"""Tamper-evident evidence chain: canonical serialization, hashing, writer and verifier.

``canonical``, ``chain`` and ``verify`` depend only on the Python standard library so the
verifier can be run independently of the writer on an analysis machine.
"""
