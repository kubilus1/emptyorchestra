from distutils.core import setup

setup(
name='emptyorchestra',
version='0.0.2',
author='Matt Kubilus',
packages=['emptyorchestra'],
package_dir = {'emptyorchestra':''},
package_data = {'emptyorchestra':['*.xrc']},
scripts=['emptyorch'],
)

