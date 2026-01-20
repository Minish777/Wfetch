from setuptools import setup

setup(
    name="wfetch",
    version="3.5.0",
    author="Minish777",
    description="Minimal system fetch tool with working config",
    py_modules=['wfetch'],
    install_requires=[
        'psutil>=5.9.0',
    ],
    entry_points={
        'console_scripts': [
            'wfetch = wfetch:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)