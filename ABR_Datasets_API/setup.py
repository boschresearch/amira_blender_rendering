import setuptools


def requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()


def readme():
    with open('README.md') as f:
        return f.read()


setuptools.setup(
    name='abr_dataset_tools',
    packages=['abr_dataset_tools'],
    package_dir={'abr_dataset_tools': 'abr_dataset_tools'},
    version='1.0',
    description='API to handle datasets genereted with AMIRA Blender Rendering',
    long_description=readme(),
    author='AMIRA',
    python_requires='>=3.7.*, <4',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: End Users',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=requirements(),
)
