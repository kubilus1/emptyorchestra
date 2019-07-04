packages: dist/eo.pex dist/eo.exe

dist/eo.pex: dist
	docker run -w /src --rm -it -v `pwd`:/src ubuntu /bin/bash -c "./setup.sh && pex -f . -v --python=python3 -r all_reqs.txt --build . -o $@ -e emptyorch.eo_web"

dist/eo.exe: dist
	docker run --rm -it -v `pwd`:/src cdrx/pyinstaller-windows:python3 "python setup.py install && pip install cefpython3 && pyinstaller --clean --workpath /tmp *.spec"

dist:
	mkdir $@

clean:
	-rm *.whl
	-rm -rf build
	-rm -rf dist
