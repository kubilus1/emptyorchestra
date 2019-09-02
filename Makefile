packages: dist/eo.pex dist/eo.exe

pex_img:
	docker build -t pex .

dist/eo.pex: dist pex_img
	docker run -w /src --rm -it -v `pwd`:/src pex /bin/bash -c "pex -f . -v --python-shebang='/usr/bin/env python3' -r all_reqs.txt --build . -o $@ -e emptyorchestra.eo_web"

dist/eo.exe: dist
	docker run --rm -it -v `pwd`:/src cdrx/pyinstaller-windows:python3 "python setup.py install && pip install cefpython3 && pyinstaller --clean --workpath /tmp *.spec"

dist:
	mkdir $@

clean:
	-rm *.whl
	-rm -rf build
	-rm -rf dist
