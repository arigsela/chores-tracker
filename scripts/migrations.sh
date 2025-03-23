#!/bin/bash
set -e

# Generate a new migration
cd backend && alembic revision --autogenerate -m "$1"