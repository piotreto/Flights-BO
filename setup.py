from setuptools import setup, find_packages


setup(
    name='flights',
    packages=find_packages(include=['flights', 'flights.*']),
    version='0.0.1',
    install_requires=[
        'numpy==1.22.3',
        'networkx==2.8.2',
        'tqdm==4.64.0',
        'pandas==1.4.1'
    ]
)
