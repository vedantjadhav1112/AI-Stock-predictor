# ============================================================
# src/__init__.py
# ============================================================
# This file makes the 'src' directory a Python PACKAGE.
#
# What is a Python package?
# -------------------------
# When Python sees a folder with __init__.py inside it,
# it treats that folder as a "package" — a bundle of modules
# you can import from.
#
# Without this file:
#   from src.data_fetcher import get_stock_data  ← ERROR ❌
#
# With this file:
#   from src.data_fetcher import get_stock_data  ← Works ✅
#
# This file can be empty! Its mere existence is what matters.
# We'll add convenience imports here as we build more modules.
# ============================================================
