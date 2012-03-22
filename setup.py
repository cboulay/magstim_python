from distutils.core import setup
dependencies = {
        'pyserial': '>=2.5'
}
setup(name='Magstim',
      version='1.0',
      packages = ['Magstim'],
      requires = [('%s (%s)' % (p,v)).replace(' ()','') for p,v in dependencies.items()],  # available in distutils from Python 2.5 onwards
      install_requires = ['%s%s' % (p,v) for p,v in dependencies.items()],
)