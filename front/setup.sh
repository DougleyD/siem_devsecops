#!/bin/bash
export FLASK_APP=run.py
export FLASK_DEBUG=1
flask db init
flask db migrate -m "Migration Model to Data Base"
flask db upgrade