from setuptools import find_packages, setup


requirements = [
    'numpy',
    'python-osc',
    'sounddevice',
]


extras_require = {
    'docs': ['sphinx', 'sphinx_rtd_theme', 'pygments-enaml'],
    'test': ['pytest', 'pytest-benchmark'],
}


setup(
    name='ncrar-audio',
    author='Brad Buran',
    author_email='info@bradburan.com',
    install_requires=requirements,
    extras_require=extras_require,
    packages=find_packages(),
    include_package_data=True,
    description='NCRAR audio tools',
    entry_points={
        'console_scripts': [],
    },
)
