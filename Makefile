packages: dist/emptyorch_amd64_linux dist/eo.exe

pyinst_img:
	docker build -t pyinstaller -f Dockerfile.pyinstall .

dist/emptyorch_amd64_linux: dist pyinst_img
	docker run -w /src --rm -it -v `pwd`:/src pyinstaller /bin/bash -c "python3 setup.py install && ./install.sh && python3 -m pip install -r all_reqs.txt && pyinstaller --clean --workpath /tmp eo_linux.spec"

rust_img:
	docker build -t rust -f Dockerfile.rust .

dist/eo.rust: rust_img
	echo "Build it"
	docker run -w /src --rm -it -v `pwd`:/src /bin/bash -c "pyoxidizer build emptyorchestra"

pex_img:
	docker build -t pex .

dist/eo.pex: dist pex_img
	docker run -w /src --rm -it -v `pwd`:/src pex /bin/bash -c "python3 setup.py install && python3 -m pip wheel -w /tmp/wheels markupsafe pyyaml pycairo pygobject jinja2 && pex -f /tmp/wheels -v --python=python3 --python-shebang='/usr/bin/env python3'  --disable-cache -r all_reqs.txt --build . -o $@ -e emptyorchestra.eo_web"

dist/eo.exe: dist
	docker run --rm -it -v `pwd`:/src cdrx/pyinstaller-windows:python3 "python setup.py install && pip install PyInstaller==3.4 && pip install cefpython3 && pip install -r requirements.txt && pyinstaller --clean --workpath /tmp eo_win.spec"

dist:
	mkdir $@

clean:
	-rm *.whl
	-rm -rf build
	-rm -rf dist
