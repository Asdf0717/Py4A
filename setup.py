from setuptools import setup, find_packages

requirements = [line.strip('\n') for line in open('./requirements.txt')]

setup(
    name='py4a',
    version='1.0',
    description='Extract breaking changes of Python packages',
    long_description=open('README.md').read(),
    long_description_content_type='txt/markdown',
    packages=find_packages(),
    zip_safe=False,
    install_requires=requirements,
    include_package_data=True
)