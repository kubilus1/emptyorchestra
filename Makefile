VER?=0.0.0

packages: tux_pkg win_pkg

nuitka_img:
	docker build -t nuitka -f Dockerfile.nuitka .

pyinst_img:
	docker build -t pyinstaller -f Dockerfile.pyinstall .

enter: pyinst_img
	docker run -w /src --rm -it -v `pwd`:/src pyinstaller /bin/bash

dist/emptyorch_amd64_linux: dist pyinst_img
	docker run -w /src --rm -it -v `pwd`:/src pyinstaller /bin/bash -c "python3 -m pip install -U pip && python3 setup.py install && python3 -m pip install -r all_reqs.txt && pyinstaller --clean --workpath /tmp eo_linux_min.spec"

dist/emptyorch_min_amd64_linux: dist pyinst_img
	docker run -w /src --rm -it -v `pwd`:/src pyinstaller /bin/bash -c "python3 -m pip install -U pip && python3 setup.py install && python3 -m pip install -r min_reqs.txt && pyinstaller --clean --workpath /tmp eo_linux_min.spec"

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


electronbuild:
	docker build -t electronbuild -f ./electron_build/Dockerfile .

electronbuild_win:
	docker build -t electronbuild_win -f ./electron_build/Dockerfile.win .

win_pkg: clean dist/eo.exe electronbuild_win
	docker run --rm -it -w /src -v `pwd`:/src electronbuild_win /bin/bash -c "cd electron_build && npm install && electron-builder -w -c.extraMetadata.version=$(VER)"

tux_pkg: clean dist/emptyorch_min_amd64_linux electronbuild
	docker run --rm -it -w /src -v `pwd`:/src electronbuild /bin/bash -c "cd electron_build && npm install && electron-builder -l -c.extraMetadata.version=$(VER)"

dev_run:
	cd electron_build && DEVMODE=1 npm start

dist:
	mkdir $@

dist_pkg:
	python3 setup.py sdist bdist_wheel

release:
	twine upload dist/*
	
clean:
	-rm *.whl
	-rm -rf build
	-rm -rf dist
