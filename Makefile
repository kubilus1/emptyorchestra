packages: dist/emptyorch_amd64_linux dist/eo.exe

nuitka_img:
	docker build -t nuitka -f Dockerfile.nuitka .

pyinst_img:
	docker build -t pyinstaller -f Dockerfile.pyinstall .

enter: pyinst_img
	docker run -w /src --rm -it -v `pwd`:/src pyinstaller /bin/bash

dist/emptyorch_amd64_linux: dist pyinst_img
	docker run -w /src --rm -it -v `pwd`:/src pyinstaller /bin/bash -c "python3 setup.py install && python3 -m pip install -r all_reqs.txt && pyinstaller --clean --workpath /tmp eo_linux.spec"

rust_img:
	docker build -t rust -f Dockerfile.rust .

dist/eo.rust: rust_img
	echo "Build it"
	docker run -w /src --rm -it -v `pwd`:/src /bin/bash -c "pyoxidizer build emptyorchestra"

pex_img:
	docker build -t pex .

dist/eo.pex: dist pex_img
	docker run -w /src --rm -it -v `pwd`:/src pex /bin/bash -c "python3 setup.py install && pex -v --python=python3 --python-shebang='/usr/bin/env python3'  --disable-cache -r all_reqs.txt --build . -o $@ -e emptyorchestra.eo_web"

dist/eo.exe: dist
	docker run --rm -it -v `pwd`:/src cdrx/pyinstaller-windows:python3 "python setup.py install && pip install -r requirements.txt && pyinstaller --clean --workpath /tmp eo_win.spec"
	#docker run --rm -it -v `pwd`:/src cdrx/pyinstaller-windows:python3 "python setup.py install && pip install -r requirements.txt && cp ./hooks/hook-webview.py /wine/drive_c/Python37/Lib/site-packages/PyInstaller/hooks/hook-webview.py && pyinstaller --clean --workpath /tmp eo_win.spec"

dist:
	mkdir $@

clean:
	-rm *.whl
	-rm -rf build
	-rm -rf dist
