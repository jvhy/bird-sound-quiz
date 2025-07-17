SHELL:=bash

.PHONY: help serve style types

## 
## This Makefile contains shortcuts for commands that are used often during development.
## 

help:    ##  Show help message
	@sed -ne '/@sed/!s/\#\# //p' $(MAKEFILE_LIST)


serve:    ## Launch quiz app
	uv run bird_sound_quiz/manage.py runserver

style:    ## Check code style with ruff
	uv run ruff check

types:    ## Check types with mypy
	uv run mypy bird_sound_quiz
