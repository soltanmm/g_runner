import os
import os.path
import setuptools
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Doc(setuptools.Command):
  description = 'Generate documentation via sphinx apidoc'
  user_options = []

  def initialize_options(self):
    pass

  def finalize_options(self):
    pass

  def run(self):
    import sphinx
    import sphinx.apidoc
    metadata = self.distribution.metadata
    src_dir = os.path.join(
        os.getcwd(),
        (self.distribution.package_dir if self.distribution.package_dir else
         {'': ''})[''])
    sys.path.append(src_dir)
    sphinx.apidoc.main([
        '', '--force', '--full', '-H', metadata.name, '-A', metadata.author,
        '-V', metadata.version, '-R', metadata.version, '--private',
        '-o', os.path.join('doc', 'src'), src_dir])
    conf_filepath = os.path.join('doc', 'src', 'conf.py')
    with open(conf_filepath, 'a') as conf_file:
      conf_file.write(
"""
extensions.append('sphinx.ext.napoleon')
napoleon_google_docstring = True
napoleon_numpy_docstring = True

html_theme = 'sphinx_rtd_theme'
""")
    sphinx.main(['', os.path.join('doc', 'src'), os.path.join('doc', 'build')])


setuptools.setup(
    name='g_runner',
    description='',
    author='',
    author_email='',
    packages=setuptools.find_packages('src'),
    package_dir={'':'src'},
    setup_requires=['nose>=1.0', 'coverage>=4.0a0', 'sphinx>=1.3'],
    test_suite='nose.collector',
    cmdclass = {
        'doc': Doc
    }
)
