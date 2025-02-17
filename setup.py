from setuptools import setup, find_packages

setup(
    name="enes100",  # Package name
    version="1.0.2", 
    license= 'MIT', 
    description="A MicroPython library for ESP32-based ENES100 communication using WebSockets.",
    author="Keystone Center", 
    author_email = 'enes100@umd.edu',
    url="https://github.com/umdenes100/enes100-micropython",
    packages=['enes100'], 
    classifiers=[
        "Intended Audience :: UMD Students",
        "Programming Language :: MicroPython :: 1.24",
        "Topic :: Communications",
    ],
    keywords="MicroPython ESP32 WebSocket ENES100",
)