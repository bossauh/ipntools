from distutils.core import setup
setup(
    name="ipntools",
    packages=["ipntools"],
    version="0.3",
    license="MIT",
    description="Library that handles ip address and other networking stuff. (Really basic)",
    author="Philippe Mathew",
    author_email="philmattdev@gmail.com",
    url="https://github.com/bossauh/ipntools",
    download_url="https://github.com/bossauh/ipntools/archive/refs/tags/v_03.tar.gz",
    keywords=["helper"],
    install_requires=[
        "mcstatus",
        "fluxhelper",
        "aiohttp",
        "fake_useragent",
        "beautifulsoup4"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ]
)
