from setuptools import setup, find_packages

setup(
    name="n2bl-batch-yt-uploader",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=["pqp"],
    install_requires=[
        "google-api-python-client",
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "tabulate",
        "colorama",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "pqp=pqp:main",   # now you can just run `pqp`
        ],
    },
    python_requires=">=3.8",
)
