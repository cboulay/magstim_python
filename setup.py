from distutils.core import setup
dependencies = {
        'pyserial': '>=2.5'
}
setup(name='MagstimInterface',
      version='1.0',
      packages = ['MagstimInterface'],
      requires = [('%s (%s)' % (p,v)).replace(' ()','') for p,v in dependencies.items()],  # available in distutils from Python 2.5 onwards
      install_requires = ['%s%s' % (p,v) for p,v in dependencies.items()],
)