PY ?= python3

.PHONY: resume full tailor test sample setup
setup:            ## install the three runtime deps + pytest
	$(PY) -m pip install -r requirements.txt

resume:           ## build out/resume.pdf and run every check (fails loudly)
	$(PY) -m resume build

full:             ## full 18-bullet set -> out/full/
	$(PY) -m resume build --config config/full.yaml --out out/full

tailor:           ## make tailor JD=path/to/job.txt
	$(PY) -m resume build --jd $(JD)

test:
	$(PY) -m pytest -q tests

sample:           ## shareable copy without data/private.yaml, committed under examples/
	$(PY) -m resume build --no-private --out out/sample
	cp out/sample/resume-public.pdf examples/resume.pdf
	cp out/sample/resume-public.txt examples/resume-ats-text.txt
	cp out/sample/missing-info.md examples/missing-info.md
