"""Vercel serverless entry point."""
import sys
import os

# Add the parent directory to path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run import app

# Vercel needs the app object exposed as 'app'
