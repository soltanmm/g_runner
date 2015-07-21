import os
import os.path
import setuptools

os.chdir(os.path.dirname(os.path.abspath(__file__)))

setuptools.setup(
    name='g_runner',
    description='',
    author='',
    author_email='',
    packages=setuptools.find_packages('src'),
    package_dir={'':'src'},
    setup_requires=['nose>=1.0', 'coverage>=4.0a0'],
    test_suite='nose.collector'
)
