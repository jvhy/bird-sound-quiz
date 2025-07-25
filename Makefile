SHELL:=bash

.PHONY: help serve populate_db style types

## 
## This Makefile contains shortcuts for commands that are used often during development.
## 

help:    ##  Show help message
	@sed -ne '/@sed/!s/\#\# //p' $(MAKEFILE_LIST)

serve:    ## Launch quiz app
	uv run manage.py runserver

populate_db:	## Populate database tables
	uv run manage.py populate_species_table
	uv run manage.py populate_region_table
	uv run manage.py populate_observation_table FI
	uv run manage.py populate_recording_table FI

style:    ## Check code style with ruff
	uv run ruff check

types:    ## Check types with mypy
	uv run mypy bird_sound_quiz
