import setuptools

setuptools.setup(
    name="tinyfpgaa",
    version="0.9.0",
    author="William D. Jones",
    author_email="thor0505@comcast.net",
    description="A small example package",
    url="https://github.com/tinyfpga/TinyFPGA-A-Programmer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=["tinyfpgaa"],
    package_dir={"tinyfpgaa": "python"},
    entry_points={
        "console_scripts": ["tinyproga=tinyfpgaa.tinyproga:main"],
    },
    python_requires=">=3.7",
)
